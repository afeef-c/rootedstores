
from django.urls import path,include
from . import views

urlpatterns = [
    
    path('place_order/', views.place_order, name='place_order'),
    
    path('payments/', views.payments, name='payments'),
    path('rozer_payments', views.rozer_payments, name='rozer_payments'),
    path("callback/", views.callback, name="callback"),

    #path('proceed_to_pay/', views.razorpaycheck ),

    path('order_complete',views.order_complete, name='order_complete'),
    path('payment_cancel',views.payment_cancel, name='payment_cancel'),

    path('download_invoice/', views.download_invoice, name='download_invoice'),
    

    
]