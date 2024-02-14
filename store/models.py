from datetime import datetime
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from accounts.models import *
from category.models import Category, CategoryOffer
from django.utils.text import slugify
from django.db.models.signals import pre_save

# Create your models here.

class Product(models.Model):
    product_name    = models.CharField(max_length=225,unique=True)
    slug            = models.SlugField(max_length=225,unique=True, editable=False)
    description     = models.TextField(max_length=255,blank=True)
    price           = models.IntegerField()
    images          = models.ImageField(upload_to='photos/product')
    stock           = models.IntegerField()
    is_available    = models.BooleanField(default=True)
    category        = models.ForeignKey(Category, on_delete=models.CASCADE)
    #merchant        = models.ForeignKey(MerchantUser, on_delete=models.SET_NULL, blank=True, null=True) 
     # Foreign key reference to Merchant model
    created_date    = models.DateTimeField(auto_now_add =True)
    modified_date   = models.DateTimeField(auto_now=True)

    def get_url(self):

        return reverse('product_detail',args=[self.category.slug, self.slug])
    
    #def discount(self):
    #    return int((self.old_price-self.price)*100/self.old_price)
    
    def __str__(self) -> str:
        return self.product_name
    
    def get_discounted_price(self):
        offer = self.offer_set.filter(start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
        if offer:
            discount = offer.discount_percentage
            discounted_price = self.price - (self.price * discount / 100)
            return discounted_price
        return self.price
    
    def get_category_offer(self):
        return CategoryOffer.objects.filter(category=self.category, start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
    
    def get_category_discounted_price(self):
        category_offer = CategoryOffer.objects.filter(category=self.category, start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
        if category_offer:
            discount = category_offer.discount_percentage
            discounted_price = self.price - (self.price * discount / 100)
            return discounted_price
        return self.price
    
    def get_offer_price(self):
        category_offer = CategoryOffer.objects.filter(category=self.category, start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
        offer = self.offer_set.filter(start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
        if category_offer and offer:
            discount = category_offer.discount_percentage+offer.discount_percentage
            discounted_price = self.price - (self.price * discount / 100)
            return discounted_price
        elif offer and not category_offer:
            discount = offer.discount_percentage
            discounted_price = self.price - (self.price * discount / 100)
            return discounted_price
        elif category_offer and not offer:
            discount = category_offer.discount_percentage
            discounted_price = self.price - (self.price * discount / 100)
            return discounted_price
        
        return self.price

    def get_offer_percent(self):
        category_offer = CategoryOffer.objects.filter(category=self.category, start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
        offer = self.offer_set.filter(start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()

        if category_offer and offer:
            discount = category_offer.discount_percentage+offer.discount_percentage
            return discount
        elif offer and not category_offer:
            discount = offer.discount_percentage
            return discount
        elif category_offer and not offer:
            discount = category_offer.discount_percentage
            return discount

@receiver(pre_save, sender=Product)
def create_product_slug(sender, instance, **kwargs):
    # Auto-populate slug only if it's not provided
    if not instance.slug:
        instance.slug = slugify(instance.product_name)


class ProductImages(models.Model):
    images = models.ImageField(upload_to="product-images", default="product.jpg")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL,related_name='p_images' , null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product images"

class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category = 'color', is_active=True)

    def sizes(self):
        return super(VariationManager, self).filter(variation_category = 'size', is_active=True)

variation_category_choice = (
    ('color','color'),
    ('size','size')
)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=100, choices=variation_category_choice)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    class Meta:
        # Add a unique constraint to ensure uniqueness within each combination of product, variation_category, and variation_value
        unique_together = [['product', 'variation_category', 'variation_value']]

    def __str__(self) -> str:
        return f"{self.product.product_name} - {self.variation_value}"


class Offer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def is_valid(self):
        now = datetime.now()
        return self.start_date <= now <= self.end_date


#class ProductOffer(models.Model):
#    product = models.ForeignKey(Product, on_delete=models.CASCADE)
#    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
#    start_date = models.DateTimeField(default=timezone.now)
#    end_date = models.DateTimeField()


#class Referral(models.Model):
#    user = models.ForeignKey(Account, on_delete=models.CASCADE)
#    referral_code = models.CharField(max_length=20, unique=True)
#    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
