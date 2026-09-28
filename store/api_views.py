import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .utils import get_user_cart


def serialize_product(p):
    return {
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'category': {
            'id': p.category.id,
            'name': p.category.name,
            'slug': p.category.slug,
        },
        'description': p.description,
        'price': float(p.price),
        'discount_price': float(p.discount_price) if p.discount_price else None,
        'effective_price': float(p.effective_price),
        'stock': p.stock,
        'is_in_stock': p.is_in_stock,
        'is_featured': p.is_featured,
        'image_url': p.display_image,
        'created_at': p.created_at.isoformat(),
    }


def serialize_order(order):
    return {
        'order_number': order.order_number,
        'customer_username': order.user.username,
        'full_name': order.full_name,
        'email': order.email,
        'phone': order.phone,
        'address': {
            'street': order.address,
            'city': order.city,
            'state': order.state,
            'postal_code': order.postal_code,
        },
        'payment_method': order.payment_method,
        'payment_status': order.payment_status,
        'subtotal': float(order.subtotal),
        'shipping_cost': float(order.shipping_cost),
        'total_amount': float(order.total_amount),
        'status': order.status,
        'status_step': order.status_step,
        'tracking_number': order.tracking_number,
        'admin_notes': order.admin_notes,
        'created_at': order.created_at.isoformat(),
        'items': [
            {
                'product_id': item.product.id if item.product else None,
                'product_name': item.product_name,
                'price': float(item.product_price),
                'quantity': item.quantity,
                'total_price': float(item.total_price),
            } for item in order.items.all()
        ]
    }


# -------------------------------------------------------------
# Products API
# -------------------------------------------------------------

@require_http_methods(["GET"])
def api_products_list(request):
    """
    GET /api/products/
    Query parameters:
    - category: slug of category
    - search: search keyword
    - featured: 'true' or 'false'
    """
    products = Product.objects.filter(is_active=True).select_related('category')
    
    cat_slug = request.GET.get('category')
    if cat_slug:
        products = products.filter(category__slug=cat_slug)
        
    search = request.GET.get('search')
    if search:
        products = products.filter(name__icontains=search)
        
    featured = request.GET.get('featured')
    if featured == 'true':
        products = products.filter(is_featured=True)

    data = [serialize_product(p) for p in products]
    return JsonResponse({'count': len(data), 'products': data}, status=200)


@require_http_methods(["GET"])
def api_product_detail(request, product_id):
    """
    GET /api/products/<product_id>/
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    return JsonResponse({'product': serialize_product(product)}, status=200)


# -------------------------------------------------------------
# Cart API
# -------------------------------------------------------------

@require_http_methods(["GET"])
def api_cart_detail(request):
    """
    GET /api/cart/
    Returns current cart items and totals.
    """
    cart = get_user_cart(request)
    items = []
    for item in cart.items.select_related('product').all():
        items.append({
            'item_id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'product_image': item.product.display_image,
            'price': float(item.product.effective_price),
            'quantity': item.quantity,
            'subtotal': float(item.subtotal),
            'available_stock': item.product.stock,
        })

    subtotal = float(cart.total_price)
    shipping = 0.00 if subtotal >= 100 or subtotal == 0 else 10.00
    total = subtotal + shipping

    return JsonResponse({
        'cart_id': cart.id,
        'total_items': cart.total_items,
        'subtotal': subtotal,
        'shipping_cost': shipping,
        'total_amount': total,
        'items': items,
    }, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def api_cart_add(request):
    """
    POST /api/cart/add/
    Body JSON: {"product_id": 1, "quantity": 1}
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    product_id = data.get('product_id')
    quantity = int(data.get('quantity', 1))

    if not product_id:
        return JsonResponse({'error': 'product_id is required'}, status=400)

    product = get_object_or_404(Product, id=product_id, is_active=True)
    if product.stock <= 0:
        return JsonResponse({'error': 'Product is out of stock'}, status=400)

    cart = get_user_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        if item.quantity + quantity > product.stock:
            return JsonResponse({'error': f'Stock limit reached ({product.stock} available)'}, status=400)
        item.quantity += quantity
        item.save()
    else:
        item.quantity = min(quantity, product.stock)
        item.save()

    return JsonResponse({
        'success': True,
        'message': f"Added '{product.name}' to cart",
        'cart_total_items': cart.total_items,
        'cart_total_price': float(cart.total_price),
    }, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def api_cart_update(request):
    """
    POST /api/cart/update/
    Body JSON: {"item_id": 1, "quantity": 3}
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    item_id = data.get('item_id')
    quantity = int(data.get('quantity', 1))

    cart = get_user_cart(request)
    item = get_object_or_404(CartItem, id=item_id, cart=cart)

    if quantity <= 0:
        item.delete()
        msg = "Item removed"
    elif quantity > item.product.stock:
        return JsonResponse({'error': f"Only {item.product.stock} in stock"}, status=400)
    else:
        item.quantity = quantity
        item.save()
        msg = "Quantity updated"

    return JsonResponse({
        'success': True,
        'message': msg,
        'cart_total_items': cart.total_items,
        'cart_total_price': float(cart.total_price),
    }, status=200)


# -------------------------------------------------------------
# Orders API
# -------------------------------------------------------------

@require_http_methods(["GET"])
def api_orders_list(request):
    """
    GET /api/orders/
    Returns orders for authenticated user, or all orders if staff.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.user.is_staff:
        orders = Order.objects.all().order_by('-created_at')
    else:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')

    data = [serialize_order(o) for o in orders]
    return JsonResponse({'count': len(data), 'orders': data}, status=200)


@require_http_methods(["GET"])
def api_order_detail(request, order_number):
    """
    GET /api/orders/<order_number>/
    Order tracking & status info.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)

    if request.user.is_staff:
        order = get_object_or_404(Order, order_number=order_number)
    else:
        order = get_object_or_404(Order, order_number=order_number, user=request.user)

    return JsonResponse({'order': serialize_order(order)}, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def api_order_update_status(request, order_number):
    """
    POST /api/orders/<order_number>/status/
    Admin endpoint to update order tracking status.
    Body JSON: {"status": "Shipped", "tracking_number": "TRK-12345", "admin_notes": "Shipped via FedEx"}
    """
    if not request.user.is_authenticated or not request.user.is_staff:
        return JsonResponse({'error': 'Administrator permissions required'}, status=403)

    order = get_object_or_404(Order, order_number=order_number)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    new_status = data.get('status')
    if new_status:
        valid_statuses = [c[0] for c in Order.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({'error': f'Invalid status. Allowed: {valid_statuses}'}, status=400)
        order.status = new_status

    if 'tracking_number' in data:
        order.tracking_number = data.get('tracking_number')

    if 'payment_status' in data:
        order.payment_status = data.get('payment_status')

    if 'admin_notes' in data:
        order.admin_notes = data.get('admin_notes')

    order.save()

    return JsonResponse({
        'success': True,
        'message': f"Order #{order.order_number} status updated to {order.status}",
        'order': serialize_order(order)
    }, status=200)
