import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager

# Create your models here.
class MyAccountManager(BaseUserManager):

    def create_user(self, first_name,last_name,username,email,password=None):

        
        if not email:
            raise ValueError('User must have an email address')
        
        if not username:
            raise ValueError('User must have an email address')
        
        user = self.model(
            email = self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        
        
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, first_name,last_name,username,email,password):
        user = self.create_user(
            email = self.normalize_email(email),
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            
        )

        user.is_admin=True
        user.is_active=True
        user.is_staff=True
        user.is_superadmin=True
        user.save(using=self._db)
        return user
    
    def create_merchant_user(self, first_name, last_name, username, email, phone_number, password=None):
        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_merchant=True  # Set is_merchant to True for merchant users
        )
        
        user.set_password(password)
        user.is_active = True 
        user.save(using=self._db)
        return user
    
    def create_staff_user(self, first_name, last_name, username, email, phone_number, otp, password=None):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_staff=True,
        )
        # Add specific fields for staff users here
        user.save(using=self._db)
        return user



class Account(AbstractBaseUser):
    
    uid=models.CharField(default=f'{uuid.uuid4}',max_length=200)
    first_name       = models.CharField(max_length=50)
    last_name       = models.CharField(max_length=50)
    username        = models.CharField(max_length=50, unique=True)
    email           = models.EmailField(max_length=100, unique=True)
    phone_number    = models.CharField(max_length=15)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True, default='')
    
    date_joined     = models.DateTimeField(auto_now_add=True)
    last_login      = models.DateTimeField(auto_now_add=True)
    is_admin        = models.BooleanField(default=False)

    is_staff        = models.BooleanField(default=False)
    is_active       = models.BooleanField(default=False)
    is_superadmin    = models.BooleanField(default=False)
    is_merchant = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    


    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username','first_name','last_name']

    objects = MyAccountManager()

    def __str__(self) -> str:
        return self.username

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self,add_label):
        return True  
    



class MerchantUser(Account):
    company_name = models.CharField(max_length=50, blank=True, null=True)
    gst_details = models.CharField(max_length=250, blank=True, null=True)
    address     = models.TextField()
    is_added_by_superadmin = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        self.is_merchant = True
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE)
    address_line_1 = models.CharField(blank=True, max_length=100)
    address_line_2 = models.CharField(blank=True, max_length=100)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True, default='')
    city = models.CharField(blank=True, max_length=20)
    state = models.CharField(blank=True, max_length=20)
    pin_code = models.CharField(max_length=20, null=True, blank=True )
    country = models.CharField(blank=True, max_length=20)

    def __str__(self) -> str:
        return self.user.first_name
    
    def full_address(self):
        return f"{self.address_line_1} {self.address_line_2} "

class AddressBook(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(max_length=50)
    address_line1 = models.CharField(max_length=100)
    address_line2 = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pin_code = models.CharField(max_length=20)
    country = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.username}'s Address"