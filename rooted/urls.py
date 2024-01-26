
from django.contrib import admin
from django.urls import include, path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('dj-admin/', admin.site.urls),
    path('admin/', include('customadmin.urls')),
    path('',views.home, name='home'),
    path('store/', include('store.urls')),
    path('cart/', include('cart.urls')),
    path('accounts/', include('accounts.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    

