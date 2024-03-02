from django import forms
from django.forms import inlineformset_factory
from orders.models import Coupon, Order

from store.models import Offer, Product
from store.models import ProductImages

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImages
        fields = ['images']

ProductImageFormSet = inlineformset_factory(
    parent_model=Product,  # The parent model for the formset
    model=ProductImages,   # The model for the formset
    form=ProductImageForm,  # The form class for individual image upload
    extra=3,  # The number of extra forms to display in the formset
    max_num=10,  # The maximum number of total forms in the formset
    can_delete=True,  # Whether the user can delete forms from the formset
)


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = '__all__'
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }




class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_amount', 'valid_from', 'valid_until', 'is_active']
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
        }

