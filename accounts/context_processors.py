
from accounts.models import WishlistItem


def w_counter(request):
    wishlist_count=0
    if 'admin' in request.path:
        return{}
    else:
        try:
            
            if request.user.is_authenticated:
                wishlist = WishlistItem.objects.filter(user=request.user).all()
                wishlist_count = wishlist.count()
            else:
                wishlist_count=0

        except WishlistItem.DoesNotExist:
            wishlist_count = 0

    return dict(wishlist_count=wishlist_count)

def wishlist(request):
    

    if request.user.is_authenticated:
        wishlist_items = WishlistItem.objects.filter(user=request.user).all()
        wishlist_product_ids = [item.product.id for item in wishlist_items]
    else:
        wishlist_items=None
        wishlist_product_ids=[]
    

    context = {
        'wishlist_items':wishlist_items,
        'wishlist_product_ids': wishlist_product_ids
    }
    return context

