from cart.models import Cart, CartItem
from cart.views import _cart_id
from orders.models import Order, OrderProduct
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
    pending_total = 0
    order_products = None

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            orders = Order.objects.filter(user=request.user, status='Pending')
            if orders.exists():
                order = orders.latest('created_at')  # Get the latest pending order
                order_products = OrderProduct.objects.filter(order=order, ordered=False)
                for pending_item in order_products:
                    pending_item.item_total = (float(pending_item.product_price) * pending_item.quantity)
                    pending_total += pending_item.item_total
                    quantity += pending_item.quantity
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for item in cart_items:
            item_variations = Variation.objects.filter(product=item.product)
            # variations[item.id] = item_variations  # Store variations for each cart item
            item.item_total = item.quantity * item.product.get_offer_price()
            quantity += item.quantity
            total += item.item_total

        tax = (2 * total) / 100
        grand_total = total + tax
        
        context = {
            'total': total,
            'quantity': quantity,
            'variations': variations,
            'cart_items': cart_items,
            'grand_total': grand_total,
            'tax': tax,
            'order_products': order_products,
            'orders_exist': order_products is not None,  # Update orders_exist based on order_products
        }

    except Cart.DoesNotExist:
        cart_items = []
        context = {'cart_items': cart_items}

    return context



