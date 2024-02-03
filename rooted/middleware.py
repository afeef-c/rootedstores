from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.urls import reverse

class BlockedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Check if user is authenticated
        if request.user.is_authenticated:
            # Check if user is blocked
            user = request.user
            if user.is_blocked:
                # Log out the blocked user
                logout(request)
                # Redirect to the "blocked" page
                return self.handle_blocked_user(request, response)

        return response

    def handle_blocked_user(self, request, response):
        # Clear all cookies
        response.cookies.clear()

        # Redirect to the "blocked" page
        return redirect('blocked_page')
