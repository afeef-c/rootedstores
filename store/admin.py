from django.contrib import admin
from .models import *

# Register your models here.

class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_display = ('product_name','price','stock','category','modified_date','is_available')


admin.site.register(Product,ProductAdmin)
admin.site.register(ProductImages)
admin.site.register(Variation)
admin.site.register(Offer)
