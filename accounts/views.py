import random
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import *
from .models import Account
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required

from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .forms import RegistrationForm
from .message_handler import MessageHandler  # Import your MessageHandler class

User = get_user_model()  # Use the get_user_model() function to get the User model

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            
            otp=random.randint(1000,9999)
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                password=password,
                otp=f'{otp}'
            )
            user.phone_number = phone_number

            # Check if 'methodOtp' exists in request.POST
            
            MessageHandler(request.POST['phone_number'],otp).send_otp_via_message()
            #MessageHandler(request.POST['phone_number'],otp).send_otp_via_whatsapp()
            #if request.POST['methodOtp']=="methodOtpWhatsapp":
            #    messagehandler=MessageHandler(request.POST['phone_number'],otp).send_otp_via_whatsapp()
            #else:
            #    messagehandler=MessageHandler(request.POST['phone_number'],otp).send_otp_via_message()
            
            red=redirect(f'/accounts/otp/{user.uid}/')
            red.set_cookie("can_otp_enter",True,max_age=600)
            messages.success(request, 'You are successfully registered with us plese veryfy OTP ')
            return red
                
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})



def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        
        user = auth.authenticate(email=email, password=password)
            
        if user is not None:
            auth.login(request, user)
            messages.success(request, 'You are logged in')
            return redirect('dashbord')
        else:
            messages.error(request, 'Invalid login credentials!!')
            return redirect('login')

    return render(request, 'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request,'You are logged out ')
    return redirect('login')



def otpVerify(request, uid):
    if request.method == "POST":
        try:
            profile = Account.objects.get(uid=uid)

            # Check if the 'can_otp_enter' cookie is set
            if request.COOKIES.get('can_otp_enter') is not None:
                if profile.otp == request.POST.get('otp'):
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
def  dashbord(request):

    return render(request, 'accounts/dashbord.html')
