
from django.urls import path
from . import views


urlpatterns = [
    path('', views.account , name='account'),
    path('register/', views.register , name='register' ),
    path('login/', views.login , name='login' ),
    path('logout/', views.logout , name='logout' ),
    #path('dashbord/', views.dashbord , name='dashbord'),
    #path('', views.dashbord , name='dashbord'),
    
    path('otp/<str:uid>/', views.otpVerify, name='otp'),

]




    