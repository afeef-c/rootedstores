from decimal import Decimal
from django.db import models

from accounts.models import Account, Wallet
from store.models import Product, Variation
from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# Create your models here.

class Payment(models.Model):
    
    STATUS = (
    ('SUCCESS', 'Success'),
    ('FAILURE', 'Failure'),
    ('PENDING', 'Pending'),
    ('COD','COD'),
    ('REFUND', 'Refund'),
    )

    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100, null=True)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)
    status = models.CharField(max_length=100, choices=STATUS, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user}-{self.payment_method}"

@receiver(post_save, sender=Payment)
def update_wallet_balance(sender, instance, **kwargs):
    if instance.status == 'REFUND':
        # Get or create the wallet instance for the user
        wallet, created = Wallet.objects.get_or_create(user=instance.user)
        refund_amount = Decimal(instance.amount_paid)

        # Update wallet balance
        wallet.balance += refund_amount
        wallet.save()



class Order(models.Model):
    
    STATUS = (
        ('Pending','Pending'),
        ('Confirmed','Confirmed'),
        ('Shipped','Shipped'),
        ('Cancelled','Cancelled'),
        ('Completed','Completed'),
        ('Delivered','Delivered'),
        ('Return','Returned')
    )

    user = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL,blank=True, null=True )
    order_number = models.CharField(max_length=20)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line_1 = models.CharField(max_length=50)
    address_line_2 = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=15)
    order_note = models.CharField(max_length=100, blank=True)
    order_total = models.FloatField()
    tax = models.FloatField()
    shipping_fee = models.FloatField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS, default='Processing')
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL,blank=True, null=True)


    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def full_address(self):

        return f"{self.address_line_1} , {self.address_line_2} "


    def __str__(self) -> str:
        return self.first_name
    
    def save(self, *args, **kwargs):
        # Check if the status is changed to Cancelled or Return
        if self.status in ['Cancelled', 'Return']:
            # Check if the payment status is not already set to Refund
            if self.payment and self.payment.status != 'REFUND':
                self.payment.status = 'REFUND'
                self.payment.save()
                self.send_status_email()

        # Check if the status is changed to Completed or Delivered
        elif self.status in ['Completed', 'Delivered']:
            # Check if the payment status is not already set to Success
            if self.payment and self.payment.status != 'SUCCESS':
                self.payment.status = 'SUCCESS'
                self.payment.save()
                self.send_status_email()

        super().save(*args, **kwargs)

    def send_status_email(self):
        subject = 'Order Status Update'
        message = f'Your order status has been updated to: {self.status}. Payment status: {self.payment.status}'
        sender_email = settings.DEFAULT_FROM_EMAIL
        recipient_email = self.user.email

        send_mail(subject, message, sender_email, [recipient_email])
    

class OrderProduct(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variation, blank=True)
    quantity = models.IntegerField()
    product_price = models.FloatField(null=True)
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.product.product_name
    

#============================== Coupon =========================================================
    
    
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_valid(self):
        now = timezone.now()
        return self.valid_from <= now <= self.valid_until

    def __str__(self):
        return self.code
    



