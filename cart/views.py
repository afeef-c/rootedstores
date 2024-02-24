from django.utils import timezone

from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import AddressBook
from .models import Cart,CartItem
from store.models import Product, Variation
from django.http import HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from orders.forms import CouponForm
from orders.models import Coupon, Order, OrderProduct
from django.urls import reverse

# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    
    return cart


def add_cart(request, product_id):
    current_user = request.user
    product = Product.objects.get(id=product_id)
    #if the user is authenticated
    if current_user.is_authenticated:
        product_variation = []
        if request.method == "POST":
            for item in request.POST:
                key=item
                value = request.POST[key]
                try:
                    variation = Variation.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    product_variation.append(variation)
                    
                except:
                    pass
                

        is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user).exists()

        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list = []
            id  = []
            for item in cart_item:
                existing_variations = item.variations.all()
                ex_var_list.append(list(existing_variations))
                id.append(item.id)

            if product_variation in ex_var_list:
                #increase the cart item quantity
                index = ex_var_list.index(product_variation)
                item_id = id[index]
                item = CartItem.objects.get(product=product, id = item_id)
                if product.stock > 0:
                    item.quantity += 1 
                    item.save()
                    product.stock -= 1
                    product.save() 
                    
                else:
                    messages.error(request, 'quantity limit exceeded!!, please try afeter some times')    
                    return redirect('cart')
            else:
                #create new item
                if product.stock > 0:
                    item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                    if len(product_variation)>0:
                        item.variations.clear()
                        item.variations.add(*product_variation)
                        #cart_item.quantity += 1
                    product.stock -= 1
                    product.save()
                    item.save()
                    

        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity = 1,
                user = current_user
            )
            if len(product_variation)>0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
            product.stock -= 1
            product.save()
                
        #return HttpResponse(cart_item.quantity)
        return redirect('cart')
    
    # if user not authenticated
    else:
        messages.error(request,'For using cart functionalites pleas login/register ')
        return redirect('login')

@login_required(login_url='login')
def remove_cart(request, product_id, cart_item_id):
    
    product = get_object_or_404(Product, id= product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id = _cart_id(request))    
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            product.stock += 1
            cart_item.save()
            product.save()
        else:
            cart_item.delete()
            product.stock += 1
            product.save()
    except:
        pass
    return redirect('cart')

@login_required(login_url='login')
def remove_cart_item(request,product_id, cart_item_id):
    
    product = get_object_or_404(Product, id= product_id)
    
    if request.user.is_authenticated:
        cart_item = CartItem.objects.get(product=product, user=request.user, id = cart_item_id)
        quantity = cart_item.quantity
    else:
        cart = Cart.objects.get(cart_id = _cart_id(request))
        cart_item = CartItem.objects.get(product=product, cart=cart, id = cart_item_id)
        quantity = cart_item.quantity
    cart_item.delete()
    product.stock += quantity
    product.save()
    return redirect('cart')


def cart(request, total=0, quantity=0, cart_item=None,panding_total=0):
    grand_total = 0
    tax = 0
    variations = {}
    shipping_fee = 0
    if cart_item is None:
        cart_items = []
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        
        for cart_item in cart_items:
            item_variations = Variation.objects.filter(product=cart_item.product)
            variations[cart_item.id] = item_variations  # Store variations for each cart item
            cart_item.item_total = cart_item.quantity * cart_item.product.get_offer_price()
            quantity += cart_item.quantity
            total += cart_item.item_total
    
        if 'coupon' in request.session:
            coupon = request.session['coupon']
            discount_amount = coupon['discount_amount']
        else:
            discount_amount=0
            coupon = None

        
        if total>=1000:
            shipping_fee = 0
        else:
            shipping_fee = 100
        tax = (2 * total) / 100
        grand_total = total + tax +shipping_fee - discount_amount



        orders_exist = Order.objects.filter(user=request.user, status='Pending').exists()
        if orders_exist:
            order = Order.objects.get(user=request.user, status='Pending')
            payment_method = order.payment.payment_method

            order_products = OrderProduct.objects.filter(order=order, ordered=False)
            for pending_item in order_products:
                pending_item.item_total = (float(pending_item.product_price) * pending_item.quantity)
                panding_total += pending_item.item_total
                quantity += pending_item.quantity

        else:
            order=None
            payment_method=None
    except ObjectDoesNotExist:
        cart_items =[]

    

    context = {
        'total': total,
        'quantity': quantity,
        'shipping_fee':shipping_fee,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'tax': tax,
        'couponform':CouponForm(),
        'discount_amount':discount_amount,
        'coupon':coupon,
        'orders_exist': orders_exist,
        'order':order,
        #'order_products':order_products,
        'panding_total':panding_total,
        'payment_method':payment_method 
    }   
    return render(request, 'cart/cart.html', context)


@login_required(login_url='login')
def placeorder(request,total=0, quantity=0, cart_item=None):
    grand_total = 0
    tax = 0
    variations = {}
    if cart_item is None:
        cart_items = []
        
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            if cart_items.count() <= 0:
                messages.error(request,'Your cart is empty pleas add some products')
                return redirect('store')
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for cart_item in cart_items:
            item_variations = Variation.objects.filter(product=cart_item.product)
            variations[cart_item.id] = item_variations  # Store variations for each cart item

            cart_item.item_total = cart_item.quantity * cart_item.product.get_offer_price()
            quantity += cart_item.quantity
            total += cart_item.item_total
        
        if 'coupon' in request.session:
            coupon = request.session['coupon']
            discount_amount = coupon['discount_amount']
        else:
            discount_amount=0

        
        if total<1000:
            shipping_fee = 100
        else:
            shipping_fee = 0

        tax = (2 * total) / 100
        grand_total = total + tax +shipping_fee-discount_amount

    except ObjectDoesNotExist:
        cart_items =[]
    
    address = AddressBook.objects.filter(user_id=request.user.id)

    context = {
        'total': total,
        'quantity': quantity,
        'shipping_fee':shipping_fee,
        'cart_items': cart_items,
        'grand_total': grand_total,
        'tax': tax,
        'address':address,
        'discount_amount':discount_amount
    }

    return render(request, 'orders/placeorder.html', context)


def add_coupon(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                coupon = Coupon.objects.get(code=code, is_active=True, valid_until__gte=timezone.now(), valid_from__lte = timezone.now() )
                # Apply discount to cart total
                request.session['coupon'] = {
                    'code': coupon.code,
                    'discount_amount': float(coupon.discount_amount)
                }
                if 'coupon' in request.session:
                    coupon_id = request.session['coupon']
                    coupon = Coupon.objects.get(pk=coupon_id)
                    coupon_discount = coupon.discount


                context = {
                    'coupon_discount':coupon_discount
                }
                messages.success(request, 'Coupon applied successfully!')
                url = reverse('cart') + f'?coupon_discount={context["coupon_discount"]}'
                return redirect(url)
                
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid or expired coupon code")
    return redirect('cart')


