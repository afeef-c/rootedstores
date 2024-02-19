from cart.models import Cart, CartItem
from cart.views import _cart_id
from store.models import Variation
from django.core.exceptions import ObjectDoesNotExist


def counter(request):
    cart_count=0
    if 'admin' in request.path:
        return{}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
            #for cart_item in cart_items:
            #    cart_count += cart_item.quantity
            cart_count = cart_items.count()
        except Cart.DoesNotExist:
            cart_count = 0

    return dict(cart_count=cart_count)

def cart(request):
    total = 0
    quantity = 0
    grand_total = 0
    tax = 0
    variations = {}

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for item in cart_items:
            item_variations = Variation.objects.filter(product=item.product)
            variations[item.id] = item_variations  # Store variations for each cart item

            item.item_total = item.quantity * item.product.get_offer_price()
            quantity += item.quantity
            total += item.item_total

        tax = (2 * total) / 100
        grand_total = total + tax
    except Cart.DoesNotExist:
        cart_items = []

    context = {
        'total': total,
        'quantity': quantity,
        'variations': variations,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'tax': tax,
    }

    return context