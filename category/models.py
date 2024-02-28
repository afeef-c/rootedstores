from datetime import datetime, timedelta
from django.forms import ValidationError
from django.utils import timezone

from django.db import models
from django.urls import reverse

#from store.models import Product,Offer
import store
# Create your models here.

class Category(models.Model):
    cat_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/category', blank=True)
    is_available = models.BooleanField(default=True)
    

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])   
    
    def get_absolute_url(self):
        return reverse("category_list")

    def __str__(self) -> str:
        return self.cat_name
    

    
class CategoryOffer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)




    def is_upcoming(self):
        now = timezone.now()
        return self.start_date > now
    
    def is_active(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def is_expired(self):
        now = timezone.now()
        return now > self.end_date

    def time_remaining(self):
        now = timezone.now()
        if self.is_active():
            time_difference = self.end_date - now
            total_seconds = int(time_difference.total_seconds())
            days, remainder = divmod(total_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            return {'days': days, 'hours': hours, 'minutes': minutes, 'seconds': seconds}
        else:
            return {'days': 0, 'hours': 0, 'minutes': 0, 'seconds': 0}
        
    def save(self, *args, **kwargs):
        # Ensure discount_percentage is within certain limits
        max_discount_percentage = 85  # Example: Maximum allowed discount percentage
        min_discount_percentage = 0   # Example: Minimum allowed discount percentage
        if self.discount_percentage > max_discount_percentage:
            self.discount_percentage = max_discount_percentage
        elif self.discount_percentage < min_discount_percentage:
            self.discount_percentage = min_discount_percentage
        
        # Check if the total discount percentage exceeds 95% for products in this category
        existing_product_offers = store.models.Offer.objects.filter(product__category=self.category)
        total_discount_percentage = self.discount_percentage

        for offer in existing_product_offers:
            total_discount_percentage += offer.discount_percentage
        
        # If the total discount percentage exceeds 95%, adjust the discount percentage
        if total_discount_percentage > 85:
            self.discount_percentage -= (total_discount_percentage - 85)

         # Check if end_date is greater than start_date
        if self.end_date <= self.start_date:
            raise ValidationError("End date must be after start date")

        
        super().save(*args, **kwargs)
    
