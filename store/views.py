from django.http import HttpResponse
from django.shortcuts import render,get_object_or_404

from cart.cart import Cart
from .models import Product,Category
from cart.models import CartItem
from django.core.paginator import EmptyPage, PageNotAnInteger,Paginator
from django.db.models import Q
# Create your views here.

def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug != None:
        categories = get_object_or_404(Category,slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True).order_by('price')

        paginator = Paginator(products,5) 
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    
    else:
        products = Product.objects.all().order_by('price')
        paginator = Paginator(products,5) 
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()

    new_products = Product.objects.all().order_by('-created_date')
    top_new_products = Product.objects.all().order_by('-created_date')[:3]
        
    context ={
        'products':paged_products,
        'product_count':product_count,
        'categories':categories,
        'top_new_products':top_new_products,
        'new_products':new_products,
    }

    return render(request, 'store/store.html',context)


def sort(request):
    products = Product.objects.all()
    top_new_products = Product.objects.all().order_by('-created_date')[:3]
    #if request.method == 'POST':
    if 'sort_by' in request.GET:        
        sort_by =  request.GET['sort_by']
        if sort_by == 'price_low_to_high':
            sort = 'Price low to high'
            products = products.order_by('price')
            
        elif sort_by == 'price_high_to_low':
            sort = 'Price high to low'
            products = products.order_by('-price')    
            
        elif  sort_by == 'default':
            sort = 'Default'
            products = products
        elif sort_by == 'latest':
                    sort = 'Latest '
                    products = products.order_by('-created_date')
        else:
            sort = 'Default'
            products = products
                            
                
            

    context = {
        'products':products,
        'sort':sort,
        'top_new_products':top_new_products,
    }    
    
    return render(request, 'store/store.html' , context)

def product_detail(request, category_slug,product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=Cart(request), product=single_product).exists()
        p_images = single_product.p_images.all()
                
    except Exception as e:
        return e

    context={
        'single_product':single_product,
        'in_cart' : in_cart,
        'p_images': p_images,
    }
    return render(request, 'store/product_detail.html', context)


def search(request):
    top_new_products = Product.objects.all().order_by('-created_date')[:3]
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by("-created_date").filter(Q(description__icontains=keyword)| Q(product_name__icontains=keyword))
            product_count = products.count()
        context = {
            'products':products,
            'product_count':product_count,
            'top_new_products':top_new_products
        }

    return render(request, 'store/store.html',context)

def filter_products(request):
    top_new_products = Product.objects.all().order_by('-created_date')[:3]
    if request.method == 'POST':
        # Retrieve minimum and maximum prices from the form submission
        min_price = int(request.POST.get('min_price'))
        max_price = int(request.POST.get('max_price'))
        # Filter products based on the submitted price range
        products = Product.objects.filter(price__gte=min_price, price__lte=max_price)

        product_count = products.count()
        context = {
            'max_price': max_price,
            'min_price' : min_price,
            'products' : products,
            'product_count': product_count,
            'top_new_products':top_new_products
        }

        # Render the template with the filtered products
        return render(request, 'store/store.html', context)
 # If the request method is not POST (e.g., GET), handle it accordingly
    # For example, you might render the form initially or handle other actions
    else:
        # Render the template with the form
        return render(request, 'store/store.html') 