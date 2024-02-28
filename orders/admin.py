from django.contrib import admin
from .models import *

# Register your models here.
class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment','user','product','quantity', 'ordered')
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number','full_name','phone','updated_at','order_total','status','is_ordered']
    list_filter = ['status','is_ordered']
    search_fields = ['order_number','first_name','last_name','phone','email']
    list_per_page =20
    inlines  = [OrderProductInline]

class OrderProductAdmin(admin.ModelAdmin):
    list_display = ['product','user','order_id','ordered']
    list_filter = ['order_id','ordered']
    group_by = 'order_id'

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount_paid', 'payment_method','status','payment_id','created_at']
    list_filter = ['payment_method','status']
    group_by = 'order_id'


admin.site.register(Payment,PaymentAdmin)
admin.site.register(Order,OrderAdmin)
admin.site.register(OrderProduct,OrderProductAdmin)
admin.site.register(Coupon)

 