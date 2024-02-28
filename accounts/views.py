from decimal import Decimal
from django.http import HttpResponse
from django.utils import timezone
import random
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from cart.models import Cart, CartItem
from cart.views import _cart_id
from orders.models import Order, OrderProduct, Payment
from store.models import Product

from .forms import *
from .models import Account, AddressBook, Transaction, Wallet, WishList,WishlistItem
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required

from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth import get_user_model
from .forms import RegistrationForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import update_session_auth_hash
import requests
from io import BytesIO
from django.template.loader import get_template
import xhtml2pdf.pisa as pisa
from django.template.loader import render_to_string
from django.conf import settings
import xlwt
from bs4 import BeautifulSoup



User = get_user_model()  # Use the get_user_model() function to get the User model



def account(request):
    return render(request, 'accounts/account.html')
    
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Generate OTP
            otp = random.randint(100000, 999999)

            # Store OTP in session
            request.session['otp'] = otp
            request.session['otp_timestamp'] = str(timezone.now())

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            # Hash the password
            hashed_password = make_password(password)

            # Save user without password
            user = User.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                password='',  # Password will be set separately

            )

            # Set hashed password
            user.password = hashed_password
            user.save()

            # Send OTP via email
            send_mail("User Date: ", f"Verify your mail by OTP: {otp}", settings.EMAIL_HOST_USER, [email], fail_silently=False)

            # Set a cookie to allow OTP entry for a limited time
            
            red=redirect(f'/accounts/otp/{user.uid}/')
            red.set_cookie("can_otp_enter",True,max_age=600)
            messages.success(request, 'You are successfully registered with us please verify OTP ')
            return red
            

    else:
        form = RegistrationForm()

    return render(request, 'accounts/account.html', {'form': form})


def login(request):
    
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = auth.authenticate(email=email, password=password)
            
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id = _cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    
                    # getting product var by cartid
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    #get the cart items from the user to access its prod-var
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id  = []
                    for item in cart_item:
                        existing_variations = item.variations.all()
                        ex_var_list.append(list(existing_variations))
                        id.append(item.id)

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user=user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
                    
            except:
                pass
            auth.login(request, user)
            messages.success(request, 'You are logged in')
            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                #print('query : ', query) :query :  next=/cart/checkout/
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    next_page = params['next']
                    return redirect(next_page)
                
            except:
                return redirect('home')

        else:
            messages.error(request, 'Invalid login credentials!!')
            return redirect('login')
            
    return render(request, 'accounts/account.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request,'You are logged out ')
    return redirect('login')


def otp_verify(request, uid):
    if request.method == "POST":
        try:
            profile = Account.objects.get(uid=uid)

            # Check if the 'can_otp_enter' cookie is set
            if request.COOKIES.get('can_otp_enter') is not None:
                stored_otp = request.session['otp']
                
                entered_otp = request.POST.get('otp')

                if int(stored_otp) == int(entered_otp):
                    profile.is_active = True
                    profile.save()
                    messages.success(request, 'Congratulations! Your account is activated.')

                    # Redirect to the login page after successful activation
                    red=redirect("login")
                    red.set_cookie('verified', True)
                    return red

                messages.error(request, 'Wrong OTP. Try again')

            return redirect(request.path)  # Redirect to the same page on OTP failure

        except MultipleObjectsReturned:
            # Handle the case where more than one object is returned
            messages.error(request, 'Error: Multiple accounts found for the given UID.')
            return redirect('register')  # Redirect to an error page or handle it appropriately

    return render(request, "accounts/otp.html", {'id': uid})

# =========================================================Starts dashboard =======================================

@login_required(login_url='login')
def dashboard(request):
    user = request.user
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id)
    orders_count = orders.count()
    
    if orders_count == 0:
        orders = None

    if UserProfile.objects.filter(user=request.user).exists():
        address = AddressBook.objects.filter(user_id=request.user.id)
        userprofile = get_object_or_404(UserProfile, user=request.user)
        
        try:
            wallet = Wallet.objects.get(user=request.user)
            transaction = Transaction.objects.filter(wallet=wallet)
            
            
        except Wallet.DoesNotExist:
            wallet = None
            transaction = None
            wallet_message = "Wallet not yet activated"

        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)
        
        context={
            'orders_count': orders_count,
            'orders': orders,
            'user_form': user_form,
            'profile_form': profile_form,
            'userprofile': userprofile,
            'address': address,
            'wallet':wallet,
            'wallet_message': wallet_message if wallet is None else None,
            'transaction':transaction
        }
        return render(request, 'accounts/dashboard.html', context)
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user)
        context={
            'user': user,
            'user_form': user_form,
            'profile_form': profile_form,
            'orders':orders,
            'orders_count':orders_count,
        }
        return render(request, 'accounts/dashboard.html', context)

# =========================================================End dashboard =======================================


def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            
            otp = random.randint(100000, 999999)

            # Consider using a safer method to store OTP, like Django's cache framework

            # Store OTP in session (consider safer alternatives)
            request.session['otp_fp'] = otp
            request.session['otp_timestamp'] = str(timezone.now())

            # Send OTP via email
            try:
                send_mail("User Date: ", f"Verify your mail by OTP: {otp}", settings.EMAIL_HOST_USER, [email], fail_silently=False)
            except Exception as e:
                messages.error(request, "Failed to send email. Please try again later.")
                return redirect('forgotPassword')
            
            # Set a cookie for OTP entry
            red = redirect(f'/accounts/otp_fp/{user.uid}/')
            red.set_cookie("can_otp_enter", True, max_age=600)  # Adjust max_age as needed
            messages.success(request, 'For reset password pleas verify the OTP sent to your email.')
            return red
            
        else:
            messages.error(request, "The account doesn't exist!")
            return redirect('forgotPassword')
        
    return render(request, 'accounts/forgotPassword.html')

# In your view function where you render the template

def resend_otp(request, uid):
    try:
        profile = Account.objects.get(uid=uid)
        otp = random.randint(100000, 999999)
        
        
         # Determine the redirect URL based on the session variable
        if request.session.get('otp', False):
            redirect_url = reverse('otp_verify', kwargs={'uid': uid})
            request.session['otp'] = otp
            request.session['otp_timestamp'] = str(timezone.now())  # Convert datetime to string
        else:
            request.session['otp_fp'] = otp
            request.session['otp_timestamp'] = str(timezone.now())  # Convert datetime to string
            redirect_url = reverse('otp_fp_verify', kwargs={'uid': uid})

        # Send the OTP via email
        send_mail(
            "User Data",
            f"Verify your email by OTP: {otp}",
            settings.EMAIL_HOST_USER,
            [profile.email],
            fail_silently=False
        )
        
        
        messages.success(request, 'OTP has been resent.')
    except ObjectDoesNotExist:
        messages.error(request, 'Error: Account not found.')
    except Exception as e:
        messages.error(request, f'Error: {e}')

    return redirect(redirect_url)


def otp_fp_verify(request, uid):
    try:
        profile = Account.objects.get(uid=uid)
        if request.method == "POST":
            stored_otp = request.session.get('otp_fp')
            entered_otp = request.POST.get('otp')

            if stored_otp and entered_otp and int(stored_otp) == int(entered_otp):
                # Clear OTP session variables after successful verification
                del request.session['otp_fp']
                del request.session['otp_timestamp']
                
                request.session['uid'] = profile.uid
                messages.success(request, 'Now you can edit your password.')
                
                # Redirect to the reset_password page after successful activation
                return redirect('reset_password', uid=profile.uid)

            messages.error(request, 'Wrong OTP. Try again')

    except ObjectDoesNotExist:
        messages.error(request, 'Error: Account not found.')
    except MultipleObjectsReturned:
        messages.error(request, 'Error: Multiple accounts found for the given UID.')

    return render(request, "accounts/otp_fp.html", {'id': uid})


def reset_password(request,uid):
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password == confirm_password:
            #uid = request.session.get('uid')
            
            if uid:
                try:
                    user = Account.objects.get(uid=uid)
                    user.set_password(password)
                    user.save()
                    # Update the session auth hash to prevent logout after password change
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Password reset successful')
                    return redirect('login')
                except Account.DoesNotExist:
                    messages.error(request, 'User does not exist.')
                    return redirect('reset_password')
            else:
                messages.error(request, 'Session data missing. Please try again.')
                return redirect('reset_password')
        else:
            messages.error(request, 'Passwords do not match.')
            return redirect('reset_password')
    else:
        return render(request, "accounts/reset_password.html",{'uid': uid})
    

# =================================orders=============================================================================================
def my_orders(request):


    return render(request,'accounts/dashboard.html')

@login_required(login_url='login')
def edit_profile(request):
    try:
        userprofile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        # If UserProfile doesn't exist for the user, create a new one
        userprofile = UserProfile.objects.create(user=request.user)

    #userprofile = get_object_or_404(UserProfile, user=request.user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect('dashboard')  # Redirect to the dashboard or profile page after successful update
        else:
            messages.error(request, "There was an error updating your profile. Please correct the errors below.")
            return redirect('dashboard')  # Redirect to the dashboard or profile page after successful update

    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile':userprofile,
        
    }

    return render(request, 'accounts/dashboard.html', context)

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if new_password == current_password:
            messages.error(request, "New password cannot be the same as the current password")
        elif new_password == confirm_password:
            if user.check_password(current_password):
                user.set_password(new_password)
                user.save()
                messages.success(request, 'Password updated successfully')
                return redirect('dashboard')
            else:
                messages.error(request, 'Please enter a valid current password')
        else:
            messages.error(request, "Passwords do not match!")

    return redirect('dashboard')



@login_required(login_url='login')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    payment = order.payment
    subtotal = 0
    tax=0
    shipping_fee=0
    for item in order_detail:
        item.item_total = item.product_price*item.quantity
        subtotal += item.item_total
    
    tax = (2*subtotal)/100
    if subtotal>= 1000:
        shipping_fee=0
    else:
        shipping_fee=100
    grand_total = subtotal+tax+ shipping_fee

    context = {
        'order_detail':order_detail,
        'order':order,
        'subtotal':subtotal,
        'shipping_fee':shipping_fee,
        'tax':tax,
        'shipping_fee':shipping_fee,
        'grand_total':grand_total,
        'payment': payment
    }

    return render(request, 'accounts/order_detail.html',context)



@login_required(login_url='login')
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    user = request.user
    email = order.email
    payment = order.payment

    if request.method == "POST":
        amount_refunded = payment.amount_paid

        if payment.status == 'SUCCESS':
            payment.status == 'REFUND'
            payment.save()
            wallet, created = Wallet.objects.get_or_create(user=user)

            # Update wallet balance by adding the refunded amount
            #wallet.balance += Decimal(amount_refunded)
            #wallet.save()
            # This process is done in db side
            # Create a transaction record for the refund
            transaction = Transaction.objects.create(
                wallet=wallet,
                amount=amount_refunded,
                type='credit'  # Assuming 'credit' means money is added to the wallet
            )

        elif payment.status == 'PENDING':
                payment.status == 'FAILURE'
                payment.save()
                
        order.status = 'Cancelled'
        order.save()
        # Send cancellation mail
        send_mail("Order cancellation: ", f"Your order:{order.order_number}- for {order.full_name} is cancelled", settings.EMAIL_HOST_USER, [email], fail_silently=False)
        messages.success(request, 'Your order succesfully cancelled!!')
    
    return redirect('dashboard')

@login_required(login_url='login')
def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    user = request.user
    email = order.email
    payment = order.payment

    if request.method == "POST":
        
        amount_refunded = payment.amount_paid

        if payment.status == 'SUCCESS':
            payment.status == 'REFUND'
            payment.save()
        order.status = 'Return'
        order.save()

        wallet, created = Wallet.objects.get_or_create(user=user)

        ## Update wallet balance by adding the refunded amount
        #wallet.balance += Decimal(amount_refunded)
        #wallet.save()
        #transaction.save()


        # Create a transaction record for the refund
        transaction = Transaction.objects.create(
            wallet=wallet,
            amount=amount_refunded,
            type='credit'  # Assuming 'credit' means money is added to the wallet
        )


        # Send cancellation mail
        send_mail("Order Return: ", f"Your order:{order.order_number}- for {order.full_name} is returned, Check wallets for refunds", settings.EMAIL_HOST_USER, [email], fail_silently=False)
        messages.success(request, 'Your order succesfully cancelled!!')
    
    return redirect('dashboard')




# =================================wishlists=============================================================================================

def get_or_create_wishlist(request):
    wishlist_id = request.session.get('wishlist_id')
    if not wishlist_id:
        wishlist = WishList.objects.create()
        wishlist_id = wishlist.wishlist_id
        request.session['wishlist_id'] = wishlist_id
    else:
        wishlist = get_object_or_404(WishList, wishlist_id=wishlist_id)
    return wishlist

@login_required(login_url='login')
def wishlist(request):
    wishlist = get_or_create_wishlist(request)
    wishlist_items = WishlistItem.objects.filter(user=request.user).all()
    context = {
        'wishlist_items': wishlist_items
    }
    return render(request, 'accounts/wishlist.html', context)


@login_required(login_url='login')
def add_to_wishlist(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_or_create_wishlist(request)
    print(wishlist)
    is_item_exists = WishlistItem.objects.filter(wishlist=wishlist, product=product, user=current_user).exists()
    if is_item_exists:
        messages.error(request, 'This product is already added to wishlist')
    else:
        WishlistItem.objects.create(user=current_user, wishlist=wishlist, product=product)
        messages.success(request, "Product is added to wish list!!")
        # Get the URL to redirect to (default to home page if HTTP_REFERER is not available)
    redirect_url = request.META.get('HTTP_REFERER', reverse('home'))
    return redirect(redirect_url)



@login_required(login_url='login')
def remove_from_wishlist(request, item_id):
    product = get_object_or_404(Product, id=item_id)
    current_user = request.user
    # Filter wishlist items by product and user
    items = WishlistItem.objects.filter(product=product, user=current_user)
    if items.exists():
        # If multiple items are found, delete all of them
        items.delete()
        messages.success(request, 'The product is removed from wishlist!!')
    else:
        messages.error(request, 'The product is not found in the wishlist!!')
    
    redirect_url = request.META.get('HTTP_REFERER', reverse('home'))
    return redirect(redirect_url)


# =================================End wishlists=============================================================================================

# =================================Start Wallet===================================================================================================


#def handle_refund(request):
#    if request.method == 'POST':
#        # Assuming you receive data about payment status change in the request
#        payment_id = request.POST.get('payment_id')
#        new_status = request.POST.get('new_status')

#        # Check if the payment status has changed to "Refund"
#        if new_status == 'Refund':
#            try:
#                payment = Payment.objects.get(pk=payment_id)
#                user = payment.user
#                amount_refunded = payment.amount_paid

#                # Retrieve or create the user's wallet
#                wallet, created = Wallet.objects.get_or_create(user=user)

#                # Update wallet balance by adding the refunded amount
#                wallet.balance += amount_refunded
#                wallet.save()
#                #transaction.save()


#                # Create a transaction record for the refund
#                transaction = Transaction.objects.create(
#                    wallet=wallet,
#                    amount=amount_refunded,
#                    type='credit'  # Assuming 'credit' means money is added to the wallet
#                )
                                


#                return HttpResponse("Refund processed successfully")
#            except Payment.DoesNotExist:
#                return HttpResponse("Payment does not exist")
#            except Exception as e:
#                return HttpResponse(f"Error processing refund: {str(e)}")

#    return HttpResponse("Invalid request")

# =================================End Wallet===================================================================================================

@login_required(login_url='login')
def order_invoice(request,order_id):

    order = Order.objects.get(order_number=order_id)
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    payment = order.payment
    
    subtotal = 0
    est_subtotal =0
    tax=0
    shipping_fee=0
    for item in order_detail:
        item.item_total = item.product_price*item.quantity
        item.est_item_total = item.product.price*item.quantity
        subtotal += item.item_total
        est_subtotal += item.est_item_total

    if order.coupon is not None:
        discount_amount = float(order.coupon.discount_amount)
    else:
        discount_amount=0
    
    tax = (2*subtotal)/100
    if subtotal>= 1000:
        shipping_fee=0
    else:
        shipping_fee=100
    grand_total = subtotal+tax+ shipping_fee - discount_amount

    context = {
        'order_detail':order_detail,
        'order':order,
        'subtotal':subtotal,
        'shipping_fee':shipping_fee,
        'tax':tax,
        'shipping_fee':shipping_fee,
        'grand_total':grand_total,
        'payment': payment,
        'discount_amount':discount_amount
    }

    return render(request, 'orders/invoice_template.html',context)



def generate_pdf_from_template(template_name, context, filename):
    # Render the template with the given context
    html_content = render_to_string(template_name, context)

    # Create a response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'

    # Generate PDF from HTML content
    pisa_status = pisa.CreatePDF(
        html_content,
        dest=response
    )

    # If PDF generation failed, return an error response
    if pisa_status.err:
        return HttpResponse('PDF generation failed.')

    return response


def generate_invoice_pdf(request,order_id):
    
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    payment = order.payment
    subtotal = 0
    tax=0
    shipping_fee=0
    for item in order_detail:
        item.item_total = item.product_price*item.quantity
        subtotal += item.item_total
    
    tax = (2*subtotal)/100
    if subtotal>= 1000:
        shipping_fee=0
    else:
        shipping_fee=100

    if order.coupon is not None:
        discount_amount = float(order.coupon.discount_amount)
    else:
        discount_amount=0
    

    grand_total=round(subtotal + tax + shipping_fee - discount_amount, 2)

    context = {
        'order_detail':order_detail,
        'order':order,
        'subtotal':subtotal,
        'shipping_fee':shipping_fee,
        'tax':tax,
        'shipping_fee':shipping_fee,
        'grand_total':grand_total,
        'payment': payment,
        'discount_amount':discount_amount
    }


    # Generate PDF from the invoice template
    pdf_response = generate_pdf_from_template('orders/invoice_template.html', context, 'pdf_invoice')

    return pdf_response

def generate_excel_from_template(template_name, context, filename):
    # Render the template with the given context
    html_content = render_to_string(template_name, context)

    # Parse HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Create a new workbook and add a sheet
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet('Sheet1')

    # Write data from HTML to Excel sheet
    for row_idx, row in enumerate(soup.find_all('tr')):
        for col_idx, cell in enumerate(row.find_all(['td', 'th'])):
            sheet.write(row_idx, col_idx, cell.text.strip())

    # Create a response object
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{filename}.xls"'

    # Write workbook content to response
    workbook.save(response)

    return response

def generate_invoice_xls(request,order_id):
    # Retrieve parameters from request.GET
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    payment = order.payment
    subtotal = 0
    tax=0
    shipping_fee=0
    for item in order_detail:
        item.item_total = item.product_price*item.quantity
        subtotal += item.item_total
    
    tax = (2*subtotal)/100
    if subtotal>= 1000:
        shipping_fee=0
    else:
        shipping_fee=100
    grand_total = subtotal+tax+ shipping_fee

    context = {
        'order_detail':order_detail,
        'order':order,
        'subtotal':subtotal,
        'shipping_fee':shipping_fee,
        'tax':tax,
        'shipping_fee':shipping_fee,
        'grand_total':grand_total,
        'payment': payment
    }

    #html_content = render_to_string('invoice_template.html', context)
    # Generate PDF from the invoice template
    excel_response = generate_excel_from_template('orders/invoice_template.html', context, 'excel_invoice')

    return excel_response

    # Generate Excel file
    excel_file_path = f'invoice_{order_number}.xls'
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Invoice')
    # Write data to Excel sheet
    ws.write(0, 0, 'Order Number')
    ws.write(0, 1, 'Payment ID')
    # Add more headers as needed
    ws.write(1, 0, order_number)
    ws.write(1, 1, payment_id)
    # Add more data as needed
    wb.save(excel_file_path)



    
    # Read the generated P
    with open(excel_file_path, 'rb') as excel_file:
        excel_content = excel_file.read()



    excel_response = HttpResponse(excel_content, content_type='application/vnd.ms-excel')
    excel_response['Content-Disposition'] = f'attachment; filename="{excel_file_path}"'

    # Delete the temporary PDF file
    os.remove(excel_file_path)


    return excel_response


