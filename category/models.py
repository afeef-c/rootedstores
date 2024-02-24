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
    
