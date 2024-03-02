
from django.urls import path

from .views import *


urlpatterns = [
    path('', cart , name='cart' ),
    path('add_cart/<int:product_id>/', add_cart , name='add_cart' ),
    path('remove_cart/<int:product_id>/<int:cart_item_id>', remove_cart , name='remove_cart' ),
    path('remove_cart_item/<int:product_id>/<int:cart_item_id>', remove_cart_item , name='remove_cart_item' ),
    
    path('placeorder/', placeorder , name='placeorder' ),
    path('submit_coupon/', submit_coupon, name='submit_coupon'),
    path('cancel_order/<int:order_id>', cancel_p_order, name='cancel_order'),

    
]
