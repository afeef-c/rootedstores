
from django.urls import path
from . import views


urlpatterns = [
    path('', views.account , name='account'),
    path('register/', views.register , name='register' ),
    path('login/', views.login , name='login' ),
    path('logout/', views.logout , name='logout' ),
    path('dashbord/', views.dashbord , name='dashbord'),
    path('forgotPassword/', views.forgotPassword , name='forgotPassword'),
    
    path('otp/<str:uid>/', views.otp_verify, name='otp_verify'),
    path('otp_fp/<str:uid>/', views.otp_fp_verify, name='otp_fp_verify'),
    
    path('reset_password/<str:uid>/', views.reset_password, name='reset_password'),
    
]




    