
from django.urls import path
from . import views


urlpatterns = [
    path('', views.account , name='account'),
    path('register/', views.register , name='register' ),
    path('login/', views.login , name='login' ),
    path('logout/', views.logout , name='logout' ),
    path('dashboard/', views.dashboard , name='dashboard'),
    path('forgotPassword/', views.forgotPassword , name='forgotPassword'),
    path('resend_otp/<str:uid>/', views.resend_otp, name='resend_otp'),

    
    path('otp/<str:uid>/', views.otp_verify, name='otp_verify'),
    path('otp_fp/<str:uid>/', views.otp_fp_verify, name='otp_fp_verify'),
    
    path('reset_password/<str:uid>/', views.reset_password, name='reset_password'),

    path('my_orders/',views.my_orders, name='my_orders'),
    path('edit_profile/',views.edit_profile, name='edit_profile'),
    path('change_password/',views.change_password, name='change_password'),
    path('order_detail/<str:order_id>',views.order_detail, name='order_detail'),
    path('order_invoice/<str:order_id>',views.order_invoice, name='order_invoice'),
    path('cancel_order/<int:order_id>',views.cancel_order, name='cancel_order'),
    path('return_order/<int:order_id>',views.return_order, name='return_order'),
    #===========wishlist===============
    
    path('wishlist', views.wishlist, name='wishlist'),
    path('add_to_wishlist/<int:product_id>', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove_from_wishlist/<int:item_id>', views.remove_from_wishlist, name='remove_from_wishlist'),

    
]




    