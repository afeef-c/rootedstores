from django.db import models
from django.urls import reverse
from accounts.models import *
from category.models import Category

# Create your models here.

class Product(models.Model):
    product_name    = models.CharField(max_length=225,unique=True)
    slug            = models.SlugField(max_length=225,unique=True)
    description     = models.TextField(max_length=255,blank=True)
    price           = models.IntegerField()
    images          = models.ImageField(upload_to='photos/product')
    stock           = models.IntegerField()
    is_available    = models.BooleanField(default=True)
    category        = models.ForeignKey(Category, on_delete=models.CASCADE)
    merchant        = models.ForeignKey(MerchantUser, on_delete=models.SET_NULL, blank=True, null=True)  # Foreign key reference to Merchant model
    created_date    = models.DateTimeField(auto_now_add =True)
    modified_date   = models.DateTimeField(auto_now=True)

    def get_url(self):

        return reverse('product_detail',args=[self.category.slug, self.slug])
    
    
    def __str__(self) -> str:
        return self.product_name
    
class ProductImages(models.Model):
    images = models.ImageField(upload_to="product-images", default="product.jpg")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL,related_name='p_images' , null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product images"

    
