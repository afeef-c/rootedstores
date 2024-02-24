from django.shortcuts import render
from store.models import Product
from django.contrib.auth.decorators import login_required
from django.db.models import F


from django.contrib import messages

def home(request):
    products = Product.objects.all().order_by('-created_date')
    products_with_offers = Product.objects.filter(offer__isnull=False).distinct()

    
    context ={
        'products':products,
        'products_with_offers':products_with_offers
    }

    return render(request, 'home.html', context)

def blocked_page(request):
    messages.error(request,f" Sorry {request.user}  You are blocked !! contact us for more informations")
    return render(request, 'blocked_page.html')