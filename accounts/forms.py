from collections.abc import Mapping
from typing import Any
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Account, UserProfile
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
import re


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter password',
            'class': 'form-control'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = Account 
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        placeholders = {
            'first_name': 'Enter first name',
            'last_name': 'Enter last name',
            'phone_number': 'Enter Phone number',
            'email': 'Enter Email address'
        }
        for field in self.fields:
            self.fields[field].widget.attrs['placeholder'] = placeholders.get(field, '')

    def clean_password(self):
        password = self.cleaned_data['password']
        validate_password(password)  # Django's built-in password validation
        return password

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number']
        # Basic phone number validation
        if not phone_number.isdigit():
            raise ValidationError('Phone number should contain only digits.')
        if len(phone_number) != 10:
            raise ValidationError('Please enter a valid phone number!.')
        
        # You can add more specific validation logic here
        return phone_number

    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        if len(first_name) < 2:
            raise ValidationError('First name must be at least 5 characters long.')
        if re.match(r'^[a-zA-Z]+$', first_name) is None:
            raise ValidationError('First name cannot consist solely of special characters.')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        if re.match(r'^[a-zA-Z]+$', last_name) is None:
            raise ValidationError('Last name cannot consist solely of special characters.')
        return last_name

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')

        email = cleaned_data.get('email')
        if Account.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')

        # Add more specific validation logic for other fields if needed

        return cleaned_data
    


class OTPVerificationForm(forms.Form):
    otp = forms.CharField(label='Enter OTP', max_length=6, min_length=6, widget=forms.TextInput(attrs={'autocomplete': 'off'}))

class UserForm(forms.ModelForm):
    
    class Meta:
        model = Account
        fields = ('first_name','last_name','email','phone_number')

class UserProfileForm(forms.ModelForm):
    profile_pic = forms.ImageField(required=False, error_messages={'invalid': "Image files only"}, widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = ('address_line_1','address_line_2','city','state','country','profile_pic')