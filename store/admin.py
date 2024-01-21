from django.contrib import admin
from .models import *

# Register your models here.

class ProductImagesAdmin(admin.TabularInline):
    model = ProductImages

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImagesAdmin]
    list_display = ('product_name','price','stock','category','modified_date','is_available')
    prepopulated_fields = { 'slug' :('product_name',) }


admin.site.register(Product,ProductAdmin)
admin.site.register(ProductImages)