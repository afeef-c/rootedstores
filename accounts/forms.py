from collections.abc import Mapping
from typing import Any
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Account, UserProfile

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter password',
        'class':'form-control'
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm password'
    }))

    class Meta:
        model = Account 
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'password']

    def __init__(self, *args, **kwargs):
        super(RegistrationForm,self).__init__(*args,**kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Enter first name'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Enter last name'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Enter Phone number'
        self.fields['email'].widget.attrs['placeholder'] = 'Enter Email adddress'
        
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super(RegistrationForm,self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                'Password does not match !!'
            )
    

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