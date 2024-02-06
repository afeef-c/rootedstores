from django.utils import timezone
import random
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from cart.models import Cart, CartItem
from cart.views import _cart_id
from orders.models import Order, OrderProduct

from .forms import *
from .models import Account
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


@login_required(login_url='login')
def  dashboard(request):
    orders = Order.objects.order_by('created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()
    
    userprofile = get_object_or_404(UserProfile,user=request.user)

    user_form = UserForm(instance=request.user)
    profile_form = UserProfileForm(instance=userprofile)

    context={
        'orders_count':orders_count,
        'orders':orders,
        'user_form':user_form,
        'profile_form':profile_form,
        'userprofile':userprofile,
    }
    return render(request, 'accounts/dashboard.html',context)


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



def otp_fp_verify(request, uid):
    if request.method == "POST":
        try:
            profile = Account.objects.get(uid=uid)

            # Check if the 'can_otp_enter' cookie is set to True
            if request.COOKIES.get('can_otp_enter') == 'True':
                stored_otp = request.session.get('otp_fp')
                entered_otp = request.POST.get('otp')

                if stored_otp and entered_otp and int(stored_otp) == int(entered_otp):
                    # Clear OTP session variables after successful verification
                    del request.session['otp_fp']
                    del request.session['otp_timestamp']
                    
                    request.session['uid'] = profile.uid

                    messages.success(request, 'Now you can edit your password.')
                    
                    # Redirect to the reset_password page after successful activation
                    #red = redirect('reset_password')
                    red = redirect(f'/accounts/reset_password/{profile.uid}/')
                    red.set_cookie('verified', True)
                    return red

                messages.error(request, 'Wrong OTP. Try again')

            else:
                messages.error(request, 'OTP verification expired. Please try again.')
            
            return redirect(request.path)  # Redirect to the same page on OTP failure

        except (ObjectDoesNotExist, MultipleObjectsReturned):
            # Handle the case where the user is not found or multiple accounts are found
            messages.error(request, 'Error: Account not found or multiple accounts found for the given UID.')
            return redirect('forgotPassword')  # Redirect to an error page or handle it appropriately

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
    

def my_orders(request):

    return render(request,'orders')

@login_required(login_url='login')
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)

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

    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
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

    context = {
        'order_detail':order_detail,
        'order':order
    }

    return render(request, 'accounts/order_detail.html',context)