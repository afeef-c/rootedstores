from django.contrib import admin
from .models import *

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('cat_name',)}
    list_display = ('cat_name', 'slug')

admin.site.register(Category, CategoryAdmin)
admin.site.register(CategoryOffer)