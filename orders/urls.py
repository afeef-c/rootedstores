
from django.urls import path,include
from . import views

urlpatterns = [
    
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('order_complete',views.order_complete, name='order_complete'),
    path('payment_cancel',views.payment_cancel, name='payment_cancel'),

    path('paypal/', include('paypal.standard.ipn.urls')),
    
]