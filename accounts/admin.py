from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from django.utils.html import format_html


# Register your models here.
class AccountAdmin(UserAdmin):
    list_display = ('email','username','first_name','last_name','date_joined','is_active','is_superadmin')
    list_display_links=('email','username','first_name','last_name')
    readonly_fields = ('last_login','date_joined')
    ordering = ('-date_joined',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(Account,AccountAdmin)

class UserProfilAdmin(admin.ModelAdmin):
    def thumbnail(self, object):
        return format_html('<img src="{}" width="30" style="border-radius:50%">'.format(object.profile_pic.url))

    thumbnail.shor_description = 'Profile Picture'
    list_display = ('thumbnail','user','city','state','country')

admin.site.register(UserProfile,UserProfilAdmin)
admin.site.register(AddressBook)
admin.site.register(WishlistItem)
admin.site.register(WishList)