
from django.contrib import admin
from django.urls import include, path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # honey pot adminpannet not real
    path('admin/', include('admin_honeypot.urls')),

    path('rooted_dj_admin/', admin.site.urls),
    path('rooted_admin/', include('customadmin.urls')),
    path('',views.home, name='home'),
    path('blocked/', views.blocked_page, name='blocked_page'),
    path('store/', include('store.urls')),
    path('cart/', include('cart.urls')),
    path('accounts/', include('accounts.urls')),
    
    #orders
    path('orders/', include('orders.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    

