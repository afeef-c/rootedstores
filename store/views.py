from django.http import HttpResponse
from django.shortcuts import render,get_object_or_404
from .models import Product,Category
from cart.models import CartItem
from cart.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger,Paginator

# Create your views here.

def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category,slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products,3) 
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
        
    else:    
        products = Product.objects.all().order_by('id')
        paginator = Paginator(products,4) 
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    context ={
        'products':paged_products,
        'product_count':product_count,
    }

    return render(request, 'store/store.html',context)

def product_detail(request, category_slug,product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
        p_images = single_product.p_images.all()
        #p_images = Product.p_images.all()
                
    except Exception as e:
        return e

    context={
        'single_product':single_product,
        'in_cart' : in_cart,
        'p_images': p_images,
    }
    return render(request, 'store/product_detail.html', context)