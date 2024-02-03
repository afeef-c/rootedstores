
from django.urls import path
from .views import store,product_detail,search,filter_products,sort


urlpatterns = [
    path('', store, name='store' ),
    path('sort/', sort, name='sort' ),
    path('category/<slug:category_slug>/', store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>', product_detail , name='product_detail'),
    path('search/', search, name='search'),
    path('filter-products/', filter_products, name='filter_products'),
]
