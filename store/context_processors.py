from .models import Category, Cart


def cart_and_categories(request):
    categories = Category.objects.all()
    cart_total_items = 0

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        if session_key:
            cart = Cart.objects.filter(session_key=session_key).first()
        else:
            cart = None

    if cart:
        cart_total_items = cart.total_items

    return {
        'nav_categories': categories,
        'cart_count': cart_total_items,
    }
