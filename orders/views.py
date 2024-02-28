import datetime
from decimal import Decimal
import json
import os
import random
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from accounts.models import Account, AddressBook, Transaction, Wallet
from rooted import settings
from django.contrib import messages

from store.models import Product, Variation

from .models import Coupon, Order, OrderProduct, Payment
from .forms import OrderForm
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.contrib.auth.decorators import login_required

from cart.models import CartItem
from django.core.mail import send_mail


from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import razorpay

from django.core.serializers import serialize

#from weasyprint import HTML
import pdfkit
import xlwt




# Create your views here.


client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))



from django.core.exceptions import ObjectDoesNotExist

@login_required
def place_order(request, total=0, quantity=0):
    
    current_user = Account.objects.get(id=request.user.id)
    
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    
    if 'coupon' in request.session:
        coupon = request.session['coupon']
        discount_amount = coupon['discount_amount']
        coupon_code = coupon['code']
        coupon_instance = Coupon.objects.get(code=coupon_code)
    else:
        discount_amount=0
        coupon=None
        coupon_code=None


    grand_total = 0
    tax = 0
    shipping_fee = 0
    est_total = 0
    for cart_item in cart_items:
        total += (float(cart_item.product.get_offer_price()) * cart_item.quantity)
        est_total = (float(cart_item.product.price) * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100

    if total < 1000:
        shipping_fee = 100
    else:
        shipping_fee = 0
    
        
    grand_total = round(total + tax + shipping_fee-discount_amount, 2)
    
    if request.method == "POST":
        
        selected_address = request.POST.get('address_method')
        accept_terms = request.POST.get('accept_terms')
        form = OrderForm(request.POST)
        
        if selected_address == 'new_address':
            if form.is_valid():
                order = Order.objects.create(
                    user=current_user,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data['phone'],
                    address_line_1=form.cleaned_data['address_line_1'],
                    address_line_2=form.cleaned_data['address_line_2'],
                    pin_code=form.cleaned_data['pin_code'],
                    country=form.cleaned_data['country'],
                    state=form.cleaned_data['state'],
                    city=form.cleaned_data['city'],
                    order_note= form.cleaned_data['order_note'],
                    order_total = grand_total,
                    tax = tax,
                    shipping_fee = shipping_fee,
                    ip = request.META.get('REMOTE_ADDR'),
                )
                if request.POST.get('save_address') == 'on':
                    address = AddressBook()
                    address.user = current_user
                    address.first_name = form.cleaned_data['first_name']
                    address.last_name = form.cleaned_data['last_name']
                    address.email = form.cleaned_data['email']
                    address.phone = form.cleaned_data['phone']
                    address.address_line_1 = form.cleaned_data['address_line_1']
                    address.address_line_2 = form.cleaned_data['address_line_2']
                    address.pin_code = form.cleaned_data['pin_code']
                    address.country = form.cleaned_data['country']
                    address.state = form.cleaned_data['state']
                    address.city = form.cleaned_data['city']
                    address.save()
        else:
            try:
                address = AddressBook.objects.get(id=selected_address)
            except AddressBook.DoesNotExist:
                return redirect('some_error_url')
            
            order = Order.objects.create(
                    user=current_user ,
                    first_name=address.first_name,
                    last_name=address.last_name,
                    email=address.email,
                    phone=address.phone,
                    address_line_1=address.address_line_1,
                    address_line_2=address.address_line_2,
                    pin_code=address.pin_code,
                    country=address.country,
                    state=address.state,
                    city=address.city,
                    order_total = grand_total,
                    tax = tax,
                    shipping_fee = shipping_fee,
                    ip = request.META.get('REMOTE_ADDR'),
                )
        
        
        order_number  = order.user.last_name[:3] + str(random.randint(11111, 99999))+order.user.first_name[:2]
        
        while Order.objects.filter(order_number=order_number).exists():
            order_number = order.user.last_name[:3] + str(random.randint(11111, 99999))+order.user.first_name[:2]

        order.order_number = order_number
        order.status = 'Pending'
        
        if 'coupon' in request.session:
            order.coupon = coupon_instance
        else:
            order.coupon = None
        order.save()
        
        if 'coupon' in request.session:
            del request.session['coupon']


        

        request.session['order_id'] = order.id

            

        order_id = request.session.get('order_id')
        order = Order.objects.get(pk=order_id)
        if selected_address != 'new_address':
            order.order_note = request.POST.get('order_note','')


        
        payment_method = request.POST.get('payment-method')
        payment = Payment.objects.create(
            user=order.user,
            payment_method = payment_method,
            payment_id=order.order_number,
            amount_paid=order.order_total,
            status='PENDING'
        )
        order.payment= payment
        order.save()
        cart_items = CartItem.objects.filter(user=order.user)
        for item in cart_items:
            order_product = OrderProduct.objects.create(
                order=order,
                user=order.user,
                product_id=item.product_id,
                quantity=item.quantity,
                product_price=item.product.get_offer_price(),
                ordered=False
            )
            order_product.variations.set(item.variations.all())
            item.delete()

        order_products = OrderProduct.objects.filter(order=order, ordered=False)
        for item in order_products:
            item.item_total = (float(item.product_price) * item.quantity)
            quantity += item.quantity

        
        context = {
            'order_products':order_products,
            'total': total,
            'tax': tax,
            'shipping_fee': shipping_fee,
            'grand_total': grand_total,
            'discount_amount':discount_amount,
            'payment_method':payment_method,
            'order':order,
            'payment': payment
            
        }

        return render(request, 'orders/payments.html', context)
                    
    else:
        try:
            address = AddressBook.objects.get(id=selected_address)
        except AddressBook.DoesNotExist:
            return redirect('place_order')

        
        

@csrf_exempt
def payments(request):
    
    order_id= request.session.get('order_id')
    order = Order.objects.get(pk=order_id)
    payment = order.payment
    print(order_id, order,payment)
    if request.method == "POST":
        
        payment_id = order.user.first_name + str(random.randint(111111, 999999))
        while Payment.objects.filter(payment_id=payment_id).exists():
            payment_id = order.user.first_name + str(random.randint(111111, 999999))
        
        if payment.payment_method == 'cash':
        # Generate a unique payment ID for cash payment
        
        
            payment.payment_id = payment_id
            payment.status = 'COD'
            payment.payment_method = 'Cash on delivery'
            order.status = 'Confirmed'
            order.is_ordered = True
            order.save()
            payment.save()
            
        else:
            messages.error(request, "Choose a valid payment method!!")
            return redirect('place_order')



        # Fetch all OrderProduct instances for the given order where ordered is False
        order_products = OrderProduct.objects.filter(order=order, ordered=False)

        # Iterate over each OrderProduct instance and set ordered to True
        for order_product in order_products:
            order_product.ordered = True
            order_product.save()
        

        request.session.pop('coupon', None)    

        # Send confirmation email to customer
        send_mail("Order Confirmation:", f"Thank you for your order, Order confirmed with ORDER NO : {order.order_number}", settings.EMAIL_HOST_USER, [order.email], fail_silently=False)

        # Redirect to order completion page
        data = {'order_number': order.order_number, 'transID': payment.payment_id}
        print(data)
        url = reverse('order_complete') + f'?order_number={data["order_number"]}&payment_id={data["transID"]}'
        return redirect(url)
    else:
        # If the request method is not POST, delete the order
        order.delete()


@csrf_exempt
def wallet_payments(request):
    
    order_id= request.session.get('order_id')
    order = Order.objects.get(pk=order_id)
    payment = order.payment
    
    if request.method == "POST":
        
        payment_id = order.user.first_name + str(random.randint(111111, 999999))
        while Payment.objects.filter(payment_id=payment_id).exists():
            payment_id = order.user.first_name + str(random.randint(111111, 999999))

        if payment.payment_method == 'wallet':
            wallet = Wallet.objects.get(user=request.user)

            payment.payment_id = payment_id
            payment.status = 'SUCCESS',
            payment.payment_method = 'Wallet'
            order.status = 'Confirmed'
            order.is_ordered = True
            order.save()
            payment.save()
            # Update wallet balance by adding the refunded amount
            wallet.balance -= Decimal(order.order_total)
            wallet.save()

            # Create a transaction record for the refund
            transaction = Transaction.objects.create(
                wallet=wallet,
                amount=order.order_total,
                type='debit'  
            )
        else:
            messages.error(request, "Choose a valid payment method!!")
            return redirect('place_order')
        # Fetch all OrderProduct instances for the given order where ordered is False
        order_products = OrderProduct.objects.filter(order=order, ordered=False)

        # Iterate over each OrderProduct instance and set ordered to True
        for order_product in order_products:
            order_product.ordered = True
            order_product.save()
        

        request.session.pop('coupon', None)    

        # Send confirmation email to customer
        send_mail("Order Confirmation:", f"Thank you for your order, Order confirmed with ORDER NO : {order.order_number}", settings.EMAIL_HOST_USER, [order.email], fail_silently=False)

        # Redirect to order completion page
        data = {'order_number': order.order_number, 'transID': payment.payment_id}
        print(data)
        url = reverse('order_complete') + f'?order_number={data["order_number"]}&payment_id={data["transID"]}'
        return redirect(url)
    else:
        # If the request method is not POST, delete the order
        order.delete()




def initiate_payment(amount, currency='INR'):
   data = {
       'amount': amount * 100,  # Razorpay expects amount in paise (e.g., 100 INR = 10000 paise)
       'currency': currency,
       'payment_capture': '1'  # Auto capture the payment after successful authorization
   }
   response = client.order.create(data=data)
   return response['id']

@login_required
def rozer_payments(request):

    order_id= request.session.get('order_id')
    order = Order.objects.get(pk=order_id)
    payment = order.payment

    if request.method == "POST":

        name = order.full_name
        amount = round(order.order_total,2)
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        
        rozer_order_id = initiate_payment(amount)
        rozer_id = order.order_number
        

        context = {
            'rozer_order_id': rozer_order_id,
            'amount': amount,
            'name':name,
            'razorpay_key':settings.RAZOR_KEY_ID,
            'order':order,
        }
        
    return render(request, "orders/payment.html", context)


@csrf_exempt
def callback(request):

    order_id= request.session.get('order_id')
    order = Order.objects.get(pk=order_id)
    payment = order.payment

    def verify_signature(response_data):
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        return client.utility.verify_payment_signature(response_data)

    if "razorpay_signature" in request.POST:  # If the request contains a Razorpay signature
    
        payment_id = request.POST.get("razorpay_payment_id", "")
        provider_order_id = request.POST.get("razorpay_order_id", "")
        signature_id = request.POST.get("razorpay_signature", "")
        order_number = request.POST.get("order_number")
        
        
        
        if verify_signature(request.POST):  # If the signature is valid

            payment.status = 'SUCCESS'
            payment.payment_id = payment_id
            payment.payment_method = "RazorPay"
            request.session['order_number'] = order.order_number
            order.status = 'Confirmed'
            order.is_ordered = True
            order.order_number = provider_order_id
            order.save()
            payment.save()
            

            # Fetch all OrderProduct instances for the given order where ordered is False
            order_products = OrderProduct.objects.filter(order=order, ordered=False)

            # Iterate over each OrderProduct instance and set ordered to True
            for order_product in order_products:
                order_product.ordered = True
                order_product.save()
        
            request.session.pop('coupon', None)

            send_mail("Order Confirmation:", f"Thank you for your order, Order confirmed with ORDER NO : {order.order_number}", settings.EMAIL_HOST_USER, [order.email], fail_silently=False)

            # Redirect to order completion page
            data = {'order_number': order.order_number, 'transID': payment.payment_id, 'user':order.user}
            url = reverse('order_complete') + f'?order_number={data["order_number"]}&payment_id={data["transID"]}&user={data["user"]}'
            return redirect(url)

            
        else:
            return render(request, "orders/payment_failure.html", context={"status": order.status})
    else:
        return HttpResponseBadRequest("Invalid request")    #else:



def order_complete(request,):
    
    order_number = request.GET.get('order_number')
    transID  = request.GET.get('payment_id')
    user = request.GET.get('user')
            
    if request.user:

        order = Order.objects.get(user=request.user, order_number=order_number, is_ordered=True)
    else:
        order = Order.objects.get(user=user, order_number=order_number, is_ordered=True)

    order_products = OrderProduct.objects.filter(order_id=order.id)
    #order_products = OrderProduct.objects.filter(order=order)  # Assuming 'order' is the Order instance you want to fetch products for
    order.status = 'Completed'
    subtotal = 0
    shipping_fee = 100
    tax=0
    payment = Payment.objects.get(payment_id = transID)
    for item in order_products:
        item.total = item.quantity * item.product_price
        subtotal += item.total
    
    if order.coupon is not None:
        discount_amount = float(order.coupon.discount_amount)
    else:
        discount_amount=0


    if subtotal>=1000:
        shipping_fee = 0
    else:
        shipping_fee = 100
    tax = (2 * subtotal) / 100

    grand_total=round(subtotal + tax + shipping_fee - discount_amount, 2)
    

    context = {
        'order':order,
        'payment':payment,
        'order_number':order.order_number,
        'payment_id': payment.payment_id,
        'order_products':order_products, 
        'subtotal':subtotal,
        'grand_total':grand_total,
        'tax':tax,
        'shipping_fee':shipping_fee,
        'discount_amount':discount_amount
    }

    html_content = render_to_string('orders/invoice_template.html',context)

    # Create an EmailMultiAlternatives object
    email = EmailMultiAlternatives(
        subject="Order Confirmation",
        body=strip_tags(html_content),  # Use plain text version of HTML content as the email body
        from_email=settings.EMAIL_HOST_USER,
        to=[order.email],
    )

    # Attach the HTML content as an alternative
    email.attach_alternative(html_content, "text/html")

    # Send the email
    email.send(fail_silently=False)
    return render(request,'orders/order_complete.html',context)



def payment_cancel(request):

    return render(request,'orders/payment_cancel.html')

