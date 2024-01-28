from base64 import urlsafe_b64encode
from datetime import datetime
from django.utils import timezone
import random
from sqlite3 import IntegrityError
import uuid
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import *
from .models import Account
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required

from django.core.exceptions import MultipleObjectsReturned
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from .forms import RegistrationForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_bytes


from .message_handler import MessageHandler  # Import your MessageHandler class

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
            messages.success(request, 'You are successfully registered with us plese veryfy OTP ')
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
            auth.login(request, user)
            messages.success(request, 'You are logged in')
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
def  dashbord(request):

    return render(request, 'accounts/dashbord.html')
