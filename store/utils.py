from .models import Cart, CartItem


def get_user_cart(request):
    """
    Retrieves or creates the Cart instance for current user or guest session.
    If a guest logs in, session cart items can be merged into user cart.
    """
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Check if there is an anonymous session cart to merge
        session_key = request.session.session_key
        if session_key:
            session_cart = Cart.objects.filter(session_key=session_key).first()
            if session_cart and session_cart != cart:
                for item in session_cart.items.all():
                    existing_item = cart.items.filter(product=item.product).first()
                    if existing_item:
                        existing_item.quantity += item.quantity
                        existing_item.save()
                    else:
                        item.cart = cart
                        item.save()
                session_cart.delete()
        return cart
    else:
        if not request.session.session_key:
            request.session.create()
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
        return cart
