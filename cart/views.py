from django.shortcuts import get_object_or_404, redirect, render
from .models import Cart,CartItem
from store.models import Product, Variation
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    product_variation = []
    if request.method == "POST":
        for item in request.POST:
            key=item
            value = request.POST[key]
            try:
                variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variation.append(variation)
                print(variation)
            except:
                pass
        
    
    try:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += 1
        cart_item.save()
    
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart
        )
        cart_item.save()
    #return HttpResponse(cart_item.quantity)
    return redirect('cart')

def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id = _cart_id(request))
    product = get_object_or_404(Product, id= product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

def remove_cart_item(request,product_id):
    cart = Cart.objects.get(cart_id = _cart_id(request))
    product = get_object_or_404(Product, id= product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()

    return redirect('cart')


def cart(request, total=0, quantity=0, cart_item=None):
    grand_total = 0
    tax = 0
    if cart_item is None:
        cart_items = []
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        for cart_item in cart_items:
            quantity += cart_item.quantity
            total += (cart_item.product.price * cart_item.quantity)

        tax = (2 * total) / 100
        grand_total = total + tax
    except ObjectDoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'tax': tax,
    }   
    return render(request, 'store/cart.html', context)


#add to cart using ajaxx
def add_to_cart(request):
    cart_p = {}
    cart_p[str(request.GET['id'])]={
        'title':request.GET['title'],
        'image':request.GET['image'],
        'qty':request.GET['qty'],
        'price':request.GET['price'],
    }
    if 'cartdata' in request.session:
        if str(request.GET['id']) in request.session['cartdata']:
            cart_data = request.session['cartdata']
            cart_data[str(request.GET['id'])]['qty'] = int(cart_p[str(request.GET['id'])]['qty'])
            cart_data.update(cart_p)
            request.session['cartdata'] = cart_data
        else:
            cart_data = request.session['cartdata']
            cart_data.update(cart_p)
            request.session['cartdata'] = cart_data
    else:
        request.session['cartdata'] = cart_p
            
    return JsonResponse({'data':request.session['cartdata'],'totalitems':len(request.session['cartdata'])})

def session_cart(request):

    return render(request,'store/cart.html', {'cart_data':request.session['cartdata'],'totalitems':len(request.session['cartdata'])})

