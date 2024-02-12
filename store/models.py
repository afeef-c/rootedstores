from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from accounts.models import *
from category.models import Category
from django.utils.text import slugify
from django.db.models.signals import pre_save

# Create your models here.

class Product(models.Model):
    product_name    = models.CharField(max_length=225,unique=True)
    slug            = models.SlugField(max_length=225,unique=True, editable=False)
    description     = models.TextField(max_length=255,blank=True)
    price           = models.IntegerField()
    old_price       = models.IntegerField(null=True,blank=True, default=500)
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
    
    
    def __str__(self) -> str:
        return self.product_name
    
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
