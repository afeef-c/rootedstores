import datetime
import random
from django.shortcuts import redirect, render
from django.urls import reverse
from rooted import settings

from store.models import Product, Variation

from .models import Order, OrderProduct, Payment
from .forms import OrderForm
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from cart.models import CartItem
from django.core.mail import send_mail

# Create your views here.

def payments(request):
    order = Order.objects.get(user=request.user, is_ordered=False, order_number = request.session['order_number'])
    order_number = order.order_number
    payment_method=request.session['payment_method']

    if payment_method == 'cash':
        paymentid = request.user.first_name + str(random.randint(111111,999999))
        while Payment.objects.filter(payment_id=paymentid) is None:
            paymentid = request.user + str(random.randint(111111,999999))
        
        payment = Payment(
            user = request.user,
            payment_id = paymentid,
            payment_method = "Cash on delivery",
            amount_paid = order.order_total,
            status = 'processing',
            
        )
        payment.save()

        order.payment = payment
        order.is_ordered = True
        order.save()

        if request.method == "POST":

            #move cart items to order product table , 
            cart_items = CartItem.objects.filter(user=request.user)

            for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = order.id
                orderproduct.payment = payment
                orderproduct.user_id = request.user.id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.product.price
                orderproduct.ordered = True
                orderproduct.save()
            
                cart_item = CartItem.objects.get(id=item.id)
                product_variations = cart_item.variations.all()
                orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                orderproduct.variations.set(product_variations)
                orderproduct.save()

                #reduce product quantiry from product table
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()
            
            # clear cart and send mail to customer 
            CartItem.objects.filter(user=request.user).delete()

            #conformation mail to user
            send_mail("Order Confirmation:", f"Thank you for your order, Order confirmed with ORDER NO : {order.order_number}", settings.EMAIL_HOST_USER, [request.user.email], fail_silently=False)
            data = {
                'order_number': order.order_number,
                'transID':payment.payment_id
                }
            url = reverse('order_complete') + f'?order_number={data["order_number"]}&payment_id={data["transID"]}'
            return redirect(url)
            
        return render(request,'orders/order_complete.html')
        



@login_required
def place_order(request,total=0,quantity=0):

    current_user = request.user
    print(current_user)
    cart_items = CartItem.objects.filter(user=current_user) 
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    
    grand_total = 0
    tax = 0
    shipping_fee = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2*total)/100

    if total<1000:
        shipping_fee = 100
    else:
        shipping_fee = 0

    grand_total = total + tax +shipping_fee
         
    if request.method == "POST":
        form = OrderForm(request.POST)
        save_address = request.POST.get('save_address')
        #if save_address:
        #    address = Addre
        accept_terms = request.POST.get('accept_terms')
        if form.is_valid():
            #store all order info in side order table
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.email = form.cleaned_data['email']
            data.phone = form.cleaned_data['phone']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.pin_code = form.cleaned_data['pin_code']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.shipping_fee = shipping_fee
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            # it will create a data.id
            # generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr,mt,dt)
            current_date  = d.strftime("%Y%m%d") 
            
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.status = 'Confirmed'
            data.save()

            payment_method = request.POST.get('payment-method')  # Selected payment method
            request.session['payment_method'] = payment_method
            request.session['order_number'] = order_number

            
            
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                
                'order': order,
                'cart_item':cart_item,
                'total':total,
                'tax':tax,
                'shipping_fee':shipping_fee,
                'grand_total':grand_total,
                'payment_method':payment_method
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')


    return HttpResponse("An error occurred.")  # Default return statement

    

def order_complete(request):
        order_number = request.GET.get('order_number')
        transID  = request.GET.get('payment_id')
        
                
        try:
            order = Order.objects.get(order_number=order_number, is_ordered=True)
            order_products = OrderProduct.objects.filter(order_id=order.id)
            order.status = 'Confirmed'
            subtotal = 0
            shipping_fee = 100
            tax=0
            payment = Payment.objects.get(payment_id = transID)
            for item in order_products:
                item.total = item.quantity * item.product.price
                subtotal += item.total

            if subtotal>=1000:
                shipping_fee = 0
            else:
                shipping_fee = 100
            tax = (2 * subtotal) / 100
            grand_total = subtotal + tax +shipping_fee

            context = {
                'order':order,
                'payment':payment,
                'order_number':order.order_number,
                'payment_id': payment.payment_id,
                'order_products':order_products, 
                'subtotal':subtotal,
                'grand_total':grand_total,
                'tax':tax,
                'shipping_fee':shipping_fee

            }
            return render(request,'orders/order_complete.html',context)
        except (Payment.DoesNotExist,Order.DoesNotExist):
            return redirect('home')

    