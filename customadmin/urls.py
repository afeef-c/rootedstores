
from django.urls import path
from . import views,AdminViews



urlpatterns = [
    path('', views.admin_login , name='admin_login'),
    path('admin_logout/', views.admin_logout , name='admin_logout'),
    
    #admin pages
    path('admin_home/', AdminViews.admin_home, name='admin_home'),
    #categories
    path('category_list/', AdminViews.CategoriesListView.as_view(), name='category_list'),
    path('category_create/', AdminViews.CategoriesCreate.as_view(), name='category_create'),
    path('category_update/<slug:pk>', AdminViews.CategoriesUpdate.as_view(), name='category_update'),
    path('category_delete/<slug:pk>', AdminViews.CategoryDeleteView.as_view(), name='category_delete'),
    # user
    path('user_create/', AdminViews.UserCreateView.as_view(), name='user_create'),
    path('users_list/', AdminViews.UsersListView.as_view(), name='users_list'),
    path('user_update/<slug:pk>', AdminViews.UserUpdate.as_view(), name='user_update'),
    path('user_delete/<int:pk>', AdminViews.UserDeleteView.as_view(), name='user_delete'),

    # products
    path('add_product/', AdminViews.ProductCreateView.as_view(), name='add_product'),
    path('products_list/', AdminViews.ProductListView.as_view(), name='products_list'),
    path('product_update/<slug:pk>', AdminViews.ProductUpdate.as_view(), name='product_update'),
    path('product_delete/<int:pk>', AdminViews.ProductDeleteView.as_view(), name='product_delete'),
    
    
    #variations
    path('variations_list/', AdminViews.VariationtListView.as_view(), name='variations_list'),
    path('add_variations/', AdminViews.VariationCreateView.as_view(), name='add_variations'),
    path('update_variation/<slug:pk>', AdminViews.VariationUpdate.as_view(), name='update_variation'),
    path('delete_variation/<int:pk>', AdminViews.VariationDeleteView.as_view(), name='delete_variation'),

    # orders
    path('orders_list/', AdminViews.OrderListView.as_view(), name='orders_list'),
    path('order_update/<slug:pk>', AdminViews.OrderUpdate.as_view(), name='order_update'),

    # payments
    path('payment_list/', AdminViews.PaymentListView.as_view(), name='payment_list'),
    path('payment_update/<slug:pk>', AdminViews.PaymentUpdate.as_view(), name='payment_update'),

    #offers
    path('category_offers/', AdminViews.CategoryOffers.as_view(), name='category_offers'),
    path('product_offers/', AdminViews.ProductOffers.as_view(), name='product_offers'),


]   





    