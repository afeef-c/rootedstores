from django.shortcuts import render
from store.models import Product
from django.contrib.auth.decorators import login_required

from django.contrib import messages

def home(request):
    products = Product.objects.all().order_by('-created_date')
    
    context ={
        'products':products,
    }

    return render(request, 'home.html', context)

def blocked_page(request):
    messages.error(request,f" Sorry {request.user}  You are blocked !! contact us for more informations")
    return render(request, 'blocked_page.html')