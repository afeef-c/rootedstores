from datetime import timezone
from django.db import models
from django.urls import reverse

# Create your models here.

class Category(models.Model):
    cat_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=255, blank=True)
    cat_image = models.ImageField(upload_to='photos/category', blank=True)
    is_available    = models.BooleanField(default=True)
    

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

    def is_valid(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
