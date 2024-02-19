import datetime
import json
import os
import random
from django.shortcuts import redirect, render
from django.urls import reverse
from accounts.models import AddressBook
from rooted import settings
from django.contrib import messages

from store.models import Product, Variation

from .models import Order, OrderProduct, Payment
from .forms import OrderForm
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.contrib.auth.decorators import login_required

from cart.models import CartItem
from django.core.mail import send_mail


from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from paypal.standard.forms import PayPalPaymentsForm

from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import razorpay

#from weasyprint import HTML
import pdfkit


# Create your views here.

client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))



from django.core.exceptions import ObjectDoesNotExist

@login_required
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    shipping_fee = 0
    for cart_item in cart_items:
        total += (float(cart_item.product.get_offer_price()) * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100

    if total < 1000:
        shipping_fee = 100
    else:
        shipping_fee = 0

    grand_total = total + tax + shipping_fee

    if request.method == "POST":
        selected_address = request.POST.get('address_method')
        accept_terms = request.POST.get('accept_terms')
        form = OrderForm(request.POST)
        data = {}
        if selected_address == 'new_address':
            if form.is_valid():
                data['user_id'] = current_user.id  # Use user's ID instead of 'id'
                data['first_name'] = form.cleaned_data['first_name']
                data['last_name'] = form.cleaned_data['last_name']
                data['email'] = form.cleaned_data['email']
                data['phone'] = form.cleaned_data['phone']
                data['address_line_1'] = form.cleaned_data['address_line_1']
                data['address_line_2'] = form.cleaned_data['address_line_2']
                data['pin_code'] = form.cleaned_data['pin_code']
                data['country'] = form.cleaned_data['country']
                data['state'] = form.cleaned_data['state']
                data['city'] = form.cleaned_data['city']
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
            
            data['user_id'] = current_user.id  # Use user's ID instead of 'id'
            data['first_name'] = address.first_name
            data['last_name'] = address.last_name
            data['email'] = address.email
            data['phone'] = address.phone
            data['address_line_1'] = address.address_line_1
            data['address_line_2'] = address.address_line_2
            data['pin_code'] = address.pin_code
            data['country'] = address.country
            data['state'] = address.state
            data['city'] = address.city

        if selected_address != 'new_address':
            data['order_note'] = request.POST.get('order_note')

        data['order_total'] = grand_total
        data['tax'] = tax
        data['shipping_fee'] = shipping_fee
        data['ip'] = request.META.get('REMOTE_ADDR')

        # Generate order number
        yr = int(datetime.date.today().strftime('%Y'))
        dt = int(datetime.date.today().strftime('%d'))
        mt = int(datetime.date.today().strftime('%m'))
        d = datetime.date(yr, mt, dt)
        current_date = d.strftime("%Y%m%d")
        order_number = current_date + str(current_user.id)  # Use user's ID as part of the order number
        data['order_number'] = order_number
        data['status'] = 'Processing'

        request.session['order_data'] = data

        payment_method = request.POST.get('payment-method')
        request.session['payment_method'] = payment_method
        request.session['amount'] = grand_total
        request.session['order_number'] = order_number

        context = {
            'data':data,
            'cart_item': cart_item,
            'total': total,
            'tax': tax,
            'shipping_fee': shipping_fee,
            'grand_total': grand_total,
            'payment_method': payment_method,
        }

        return render(request, 'orders/payments.html', context)

@csrf_exempt
def payments(request):
    try:
        order = Order(**request.session.get('order_data'))
        amount = request.session.get('amount') 
        
        payment_method = request.session.get('payment_method')

        if request.method == "POST":

            if payment_method == 'cash':
                # Generate a unique payment ID for cash payment
                payment_id = order.user.first_name + str(random.randint(111111, 999999))
                while Payment.objects.filter(payment_id=payment_id).exists():
                    payment_id = order.user.first_name + str(random.randint(111111, 999999))
                
                payment = Payment.objects.create(
                    user=order.user,
                    payment_method="Cash on delivery",
                    payment_id=payment_id,
                    amount_paid=amount,
                    status='PENDING'
                )
            #else:
            #    # For other payment methods like RazorPay
            #    payment_id = request.session.get('payment_id')
            #    payment = Payment.objects.create(
            #        user=order.user,
            #        payment_method="RazorPay",
            #        payment_id=payment_id,
            #        amount_paid=amount,
            #        status='processing'
            #    )

            order.payment = payment
            order.status = 'Confirmed'
            order.is_ordered = True
            order.save()

            # Move cart items to order product table
            cart_items = CartItem.objects.filter(user=order.user)
            for item in cart_items:
                order_product = OrderProduct.objects.create(
                    order=order,
                    user=order.user,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product_price=item.product.get_offer_price(),
                    ordered=True
                )
                order_product.variations.set(item.variations.all())


            # Clear cart
            cart_items.delete()

            # Send confirmation email to customer
            send_mail("Order Confirmation:", f"Thank you for your order, Order confirmed with ORDER NO : {order.order_number}", settings.EMAIL_HOST_USER, [order.user.email], fail_silently=False)

            # Redirect to order completion page
            data = {'order_number': order.order_number, 'transID': payment.payment_id}
            url = reverse('order_complete') + f'?order_number={data["order_number"]}&payment_id={data["transID"]}'
            return redirect(url)
        else:
            # If the request method is not POST, delete the order
            order.delete()

    except Order.DoesNotExist:
        # Handle the case where the order does not exist
        return redirect('some_error_url')  # Redirect to an error page or handle it accordingly    


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
    
    order = Order(**request.session.get('order_data'))
    CartItem.objects.filter(user=request.user)
    

    if request.method == "POST":
        name = order.full_name
        amount = int(order.order_total)
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        
        rozer_order_id = initiate_payment(amount)
        rozer_id = order.order_number
        
        context = {
            'rozer_order_id': rozer_order_id,
            'amount': amount,
            'name':name,
            'razorpay_key':settings.RAZOR_KEY_ID,
            'order':order,
            'cart':CartItem
        }
        
    return render(request, "orders/payment.html", context)


@csrf_exempt
def callback(request):
    
    def verify_signature(response_data):
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        return client.utility.verify_payment_signature(response_data)

    if "razorpay_signature" in request.POST:  # If the request contains a Razorpay signature
    
        payment_id = request.POST.get("razorpay_payment_id", "")
        provider_order_id = request.POST.get("razorpay_order_id", "")
        signature_id = request.POST.get("razorpay_signature", "")
        order_number = request.POST.get("order_number")
        
        # Assuming order_data is stored in session
        order_data = request.session.get('order_data')
        order = Order(**order_data)
        if verify_signature(request.POST):  # If the signature is valid

            
            request.session['order_number'] = order.order_number
            payment = Payment.objects.create(
                        user=order.user,
                        payment_method="RazorPay",
                        payment_id=payment_id,
                        amount_paid=order.order_total,
                        status='SUCCESS'
                    )
            order.status = 'Confirmed'
            order.is_ordered = True
            order.order_number = provider_order_id
            order.payment = payment
            order.save()
            cart_items = CartItem.objects.filter(user=order.user)
        
            for item in cart_items:
                order_product = OrderProduct.objects.create(
                    order=order,
                    user=order.user,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product_price=item.product.get_offer_price(),
                    ordered=True
                )
                order_product.variations.set(item.variations.all())

                # Clear cart
            cart_items.delete()

            # Send confirmation email to customer
            send_mail("Order Confirmation:", f"Thank you for your order, Order confirmed with ORDER NO : {order.order_number}", settings.EMAIL_HOST_USER, [order.user.email], fail_silently=False)

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
        print(order_number)
    
        order = Order.objects.get(user=request.user, order_number=order_number, is_ordered=True)
    else:
        order = Order.objects.get(user=user, order_number=order_number, is_ordered=True)
    order_products = OrderProduct.objects.filter(order_id=order.id)
    order_products = OrderProduct.objects.filter(order=order)  # Assuming 'order' is the Order instance you want to fetch products for
    order.status = 'Completed'
    subtotal = 0
    shipping_fee = 100
    tax=0
    payment = Payment.objects.get(payment_id = transID)
    for item in order_products:
        item.total = item.quantity * item.product_price
        subtotal += item.total

    if subtotal>=1000:
        shipping_fee = 0
    else:
        shipping_fee = 100
    tax = (2 * subtotal) / 100
    grand_total = round(subtotal + tax +shipping_fee, 2)




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

    html_content = render_to_string('orders/order_complete.html',context)

    # Create an EmailMultiAlternatives object
    email = EmailMultiAlternatives(
        subject="Order Confirmation",
        body=strip_tags(html_content),  # Use plain text version of HTML content as the email body
        from_email=settings.EMAIL_HOST_USER,
        to=[request.user.email],
    )

    # Attach the HTML content as an alternative
    email.attach_alternative(html_content, "text/html")

    # Send the email
    email.send(fail_silently=False)
    return render(request,'orders/order_complete.html',context)



def payment_cancel(request):

    return render(request,'orders/payment_cancel.html')



def download_invoice(request):
    # Retrieve parameters from request.GET
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')
    order_products = request.GET.get('order_products')
    subtotal = request.GET.get('subtotal')
    grand_total = request.GET.get('grand_total')
    tax = request.GET.get('tax')
    shipping_fee = request.GET.get('shipping_fee')

    # Render HTML template with context data
    context = {
        'order_number': order_number,
        'payment_id': payment_id,
        'order_products': order_products,
        'subtotal': subtotal,
        'grand_total': grand_total,
        'tax': tax,
        'shipping_fee': shipping_fee
        # Add other context data as needed
    }
    html_content = render_to_string('invoice_template.html', context)

    # Generate PDF from HTML content using pdfkit
    pdf_file_path = f'invoice_{order_number}.pdf'
    pdfkit.from_string(html_content, pdf_file_path)

    # Read the generated PDF file
    with open(pdf_file_path, 'rb') as f:
        pdf_file = f.read()

    # Create a response with the PDF file as a file attachment
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{pdf_file_path}"'

    # Delete the temporary PDF file
    os.remove(pdf_file_path)

    return response
