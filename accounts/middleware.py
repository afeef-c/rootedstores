from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from .models import Account
from django.contrib import messages

class RedirectAuthenticatedUserMiddleware:
    """
    Middleware to redirect authenticated users from login/registration pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Hardcoded URLs for login and registration pages
            login_url = '/accounts/login/'  # Replace with your actual login URL
            registration_url = '/accounts/register/'  # Replace with your actual registration URL
            
            if request.path == login_url or request.path == registration_url:
                return redirect('/')  # Redirect to home page or any other page you want
        return self.get_response(request)



