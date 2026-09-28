from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .forms import RegisterForm, CheckoutForm, ProductForm, CategoryForm, OrderStatusForm
from .utils import get_user_cart


# -------------------------------------------------------------
# Storefront & Catalog Views
# -------------------------------------------------------------

def home(request):
    """Product catalog with search, category filtering, and sorting."""
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    sort_by = request.GET.get('sort', '').strip()

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )

    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    else:
        # Default featured first, then newest
        products = products.order_by('-is_featured', '-created_at')

    featured_products = Product.objects.filter(is_active=True, is_featured=True)[:4]

    context = {
        'products': products,
        'categories': categories,
        'active_category': active_category,
        'query': query,
        'sort_by': sort_by,
        'featured_products': featured_products,
        'total_count': products.count(),
    }
    return render(request, 'store/home.html', context)


def product_detail(request, slug):
    """Detailed view for a single product."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'store/product_detail.html', context)


# -------------------------------------------------------------
# Cart Views
# -------------------------------------------------------------

def cart_view(request):
    """View shopping cart contents, calculations, and checkout CTA."""
    cart = get_user_cart(request)
    items = cart.items.select_related('product').all()
    subtotal = cart.total_price
    shipping_cost = Decimal('0.00') if subtotal >= 100 or subtotal == 0 else Decimal('10.00')
    total = subtotal + shipping_cost

    context = {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
        'free_shipping_threshold': Decimal('100.00'),
    }
    return render(request, 'store/cart.html', context)


def add_to_cart(request, product_id):
    """Add product to cart or increment quantity."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if product.stock <= 0:
        messages.error(request, f"Sorry, '{product.name}' is currently out of stock.")
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    cart = get_user_cart(request)
    quantity = int(request.POST.get('quantity', 1))

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        if cart_item.quantity + quantity > product.stock:
            messages.warning(request, f"Cannot add more than {product.stock} units available in stock.")
            return redirect(request.META.get('HTTP_REFERER', 'cart'))
        cart_item.quantity += quantity
        cart_item.save()
        messages.success(request, f"Updated quantity for '{product.name}'.")
    else:
        cart_item.quantity = min(quantity, product.stock)
        cart_item.save()
        messages.success(request, f"Added '{product.name}' to your cart!")

    # If it was an AJAX/Fetch request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Added '{product.name}' to your cart!",
            'cart_count': cart.total_items,
        })

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'cart'
    return redirect(next_url)


def update_cart_item(request, item_id):
    """Update item quantity in cart."""
    cart = get_user_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    action = request.POST.get('action')

    if action == 'increment':
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, "Item quantity increased.")
        else:
            messages.warning(request, "Maximum available stock reached.")
    elif action == 'decrement':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, "Item quantity decreased.")
        else:
            cart_item.delete()
            messages.info(request, "Item removed from cart.")

    return redirect('cart')


def remove_cart_item(request, item_id):
    """Remove item completely from cart."""
    cart = get_user_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    name = cart_item.product.name
    cart_item.delete()
    messages.info(request, f"'{name}' removed from your cart.")
    return redirect('cart')


# -------------------------------------------------------------
# Checkout & Order Tracking
# -------------------------------------------------------------

@login_required(login_url='login')
def checkout(request):
    """Checkout page to place order."""
    cart = get_user_cart(request)
    items = cart.items.select_related('product').all()

    if not items:
        messages.warning(request, "Your cart is empty. Please add items to checkout.")
        return redirect('home')

    # Stock validation check
    for item in items:
        if item.quantity > item.product.stock:
            messages.error(request, f"'{item.product.name}' only has {item.product.stock} items left in stock.")
            return redirect('cart')

    subtotal = cart.total_price
    shipping_cost = Decimal('0.00') if subtotal >= 100 else Decimal('10.00')
    total = subtotal + shipping_cost

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.subtotal = subtotal
            order.shipping_cost = shipping_cost
            order.total_amount = total
            
            # If payment is card or upi, simulate instant completion; if cod, mark pending
            if order.payment_method in ['card', 'upi']:
                order.payment_status = 'Completed'
            else:
                order.payment_status = 'Pending'

            order.save()

            # Create OrderItems and decrease stock
            for item in items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_price=item.product.effective_price,
                    quantity=item.quantity,
                    total_price=item.subtotal,
                )
                item.product.stock -= item.quantity
                item.product.save()

            # Clear cart
            cart.items.all().delete()

            messages.success(request, f"Order #{order.order_number} placed successfully!")
            return redirect('order_success', order_number=order.order_number)
    else:
        # Prepopulate with user details if available
        initial_data = {
            'full_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'email': request.user.email,
        }
        form = CheckoutForm(initial=initial_data)

    context = {
        'form': form,
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
    }
    return render(request, 'store/checkout.html', context)


@login_required(login_url='login')
def order_success(request, order_number):
    """Order confirmation view."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})


@login_required(login_url='login')
def order_history(request):
    """View customer past order history."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})


@login_required(login_url='login')
def order_tracking(request, order_number):
    """Track single order with visual progress steps."""
    if request.user.is_staff:
        order = get_object_or_404(Order, order_number=order_number)
    else:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'store/order_tracking.html', {'order': order})


# -------------------------------------------------------------
# User Authentication Views
# -------------------------------------------------------------

def user_register(request):
    """Register new customer account."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'store/register.html', {'form': form})


def user_login(request):
    """Login existing user or admin."""
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                # Merge session cart into user cart
                get_user_cart(request)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                if user.is_staff:
                    return redirect('admin_dashboard')
                return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'store/login.html', {'form': form})


def user_logout(request):
    """Logout current user."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')


@login_required(login_url='login')
def user_profile(request):
    """User profile overview with recent orders."""
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(request, 'store/profile.html', {
        'recent_orders': recent_orders,
        'user': request.user,
    })


# -------------------------------------------------------------
# Custom Admin Management Portal (Role-based: Staff/Admin only)
# -------------------------------------------------------------

def staff_required(view_func):
    return user_passes_test(lambda u: u.is_active and u.is_staff, login_url='login')(view_func)


@staff_required
def admin_dashboard(request):
    """Admin executive dashboard with key business metrics and quick actions."""
    total_sales = Order.objects.exclude(status='Cancelled').aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='Pending').count()
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=5).count()

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]
    latest_products = Product.objects.select_related('category').order_by('-created_at')[:6]

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
        'latest_products': latest_products,
    }
    return render(request, 'store/admin/dashboard.html', context)


@staff_required
def admin_product_list(request):
    """Admin view for product inventory management."""
    products = Product.objects.select_related('category').order_by('-created_at')
    return render(request, 'store/admin/product_list.html', {'products': products})


@staff_required
def admin_product_add(request):
    """Admin create new product."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product '{product.name}' created successfully!")
            return redirect('admin_product_list')
    else:
        form = ProductForm()
    return render(request, 'store/admin/product_form.html', {'form': form, 'title': 'Add New Product'})


@staff_required
def admin_product_edit(request, product_id):
    """Admin edit existing product."""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Product '{product.name}' updated successfully!")
            return redirect('admin_product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/admin/product_form.html', {'form': form, 'title': f'Edit {product.name}', 'product': product})


@staff_required
def admin_product_delete(request, product_id):
    """Admin delete product."""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' was deleted.")
        return redirect('admin_product_list')
    return render(request, 'store/admin/confirm_delete.html', {'object': product, 'type': 'Product'})


@staff_required
def admin_order_list(request):
    """Admin view for managing and filtering customer orders."""
    status_filter = request.GET.get('status')
    orders = Order.objects.select_related('user').order_by('-created_at')
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'store/admin/order_list.html', {
        'orders': orders,
        'current_filter': status_filter,
    })


@staff_required
def admin_order_detail(request, order_number):
    """Admin order detail view with status updater."""
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order #{order.order_number} status updated to '{order.status}'.")
            return redirect('admin_order_detail', order_number=order.order_number)
    else:
        form = OrderStatusForm(instance=order)

    return render(request, 'store/admin/order_detail.html', {'order': order, 'form': form})


@staff_required
def admin_category_list(request):
    """Admin view for category management."""
    categories = Category.objects.annotate(product_count=Count('products')).all()
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"Category '{category.name}' created!")
            return redirect('admin_category_list')
    else:
        form = CategoryForm()

    return render(request, 'store/admin/category_list.html', {'categories': categories, 'form': form})
