from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView,CreateView,UpdateView,DetailView,DeleteView
from accounts.models import *
from store.models import *
from category.models import Category
from django.contrib.messages.views import SuccessMessageMixin
from django.core.files.storage import FileSystemStorage
from django.contrib.messages.views import messages
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@login_required(login_url='admin_login')
def admin_home(request):
    return render(request,'customadmin/admin_home.html', {'user': request.user})
#============================Categories =======================================================================

class CategoriesListView(ListView):
    model = Category
    template_name = "customadmin/category_list.html"
    context_object_name = "categories"

class CategoriesCreate(SuccessMessageMixin, CreateView):
    model = Category
    success_message = "New category added!"
    fields = "__all__"
    template_name = "customadmin/category_create.html"


class CategoriesUpdate(SuccessMessageMixin, UpdateView):
    model = Category
    success_message = " Category updated!"
    fields = "__all__"
    template_name = "customadmin/category_update.html"
#====================================Users=================================================================================
class UsersListView(ListView):
    model = Account
    template_name = "customadmin/user_list.html"
    context_object_name = "users"


class UserCreateView(SuccessMessageMixin, CreateView):
    model = Account
    template_name = "customadmin/user_create.html"
    fields = ['first_name','last_name','username','email','password','phone_number','profile_pic','is_admin','is_active','is_merchant','is_staff']
    success_message = "New user added!"
    success_url = reverse_lazy('users_list') 

    def form_valid(self, form):

        responce = super().form_valid(form)

        return responce
    def get_success_message(self, cleaned_data):
        # Customize the success message based on the form data
        # You can access form.cleaned_data to retrieve form input values
        return f"User {cleaned_data['username']} created successfully."
    
class UserUpdate(SuccessMessageMixin, UpdateView):
    model = Account
    template_name = "customadmin/user_update.html"
    fields = ['first_name','last_name','username','email','password','phone_number','profile_pic','is_admin','is_active','is_merchant','is_staff']
    success_message = "New user added!"
    success_url = reverse_lazy('users_list') 

    def form_valid(self, form):

        responce = super().form_valid(form)

        return responce
    def get_success_message(self, cleaned_data):
        return f"User {cleaned_data['username']} updated successfully."

@method_decorator(login_required, name='dispatch')
class UserDeleteView(SuccessMessageMixin,DeleteView):
    model = Account
    template_name = 'customadmin/user_delete.html'  
    success_message = " User {{user.ussername}} deleted!"
    success_url = reverse_lazy('users_list') 

    def get_object(self, queryset=None):
        user_id = self.kwargs.get('pk')
        return Account.objects.get(pk=user_id)
    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete User Account'
        return context
    
    def get_success_message(self, cleaned_data):
        return f"User deleteded successfully."

#============================================Products=======================================================================
class ProductListView(ListView):
    model = Product
    template_name = "customadmin/product_list.html"
    context_object_name = "products"

class ProductCreateView(SuccessMessageMixin, CreateView):
    model = Product
    template_name = "customadmin/add_product.html"
    fields = '__all__'
    success_message = "New product added!"
    success_url = reverse_lazy('products_list') 

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['category'].queryset = Category.objects.all().order_by('cat_name')
        form.fields['merchant'].queryset = Account.objects.filter(is_merchant=True)
        return form

    def form_valid(self, form):
        # Handle the creation of associated ProductImages
        images = self.request.FILES.getlist('images')
        for image in images:
            product_image = ProductImages(images=image, product=self.object)
            product_image.save()

        return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return f"Product {cleaned_data['product_name']} created successfully."


class ProductUpdate(SuccessMessageMixin, UpdateView):
    model = Product
    template_name = "customadmin/product_update.html"
    fields = '__all__'
    success_message = "The Product added!"
    success_url = reverse_lazy('products_list') 

    def form_valid(self, form):

        responce = super().form_valid(form)

        return responce
    def get_success_message(self, cleaned_data):
        return f"Product: {cleaned_data['product_name']} updated successfully."
    
@method_decorator(login_required, name='dispatch')
class ProductDeleteView(SuccessMessageMixin, DeleteView):
    model = Product
    template_name = 'customadmin/product_delete.html'
    success_message = "Product {{ product.product_name }} deleted successfully!"
    success_url = reverse_lazy('products_list')

    def get_object(self, queryset=None):
        product_id = self.kwargs.get('pk')
        return Product.objects.get(pk=product_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Product'
        return context
#========================Variations=============================================================================
class VariationtListView(ListView):
    model = Variation
    template_name = "customadmin/variation_list.html"
    context_object_name = "variations"

class VariationCreateView(SuccessMessageMixin, CreateView):
    model = Variation
    template_name = "customadmin/add_variations.html"
    fields = '__all__'
    success_message = "New variations added!"
    success_url = reverse_lazy('variations_list') 

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['product'].queryset = Product.objects.all().order_by('product_name')
        return form

    #def form_valid(self, form):
    #    # Handle the creation of associated ProductImages
    #    images = self.request.FILES.getlist('images')
    #    for image in images:
    #        product_image = ProductImages(images=image, product=self.object)
    #        product_image.save()

    #    return super().form_valid(form)

    def get_success_message(self, cleaned_data):
        return f"Variattion created successfully."


class VariationUpdate(SuccessMessageMixin, UpdateView):
    model = Variation
    template_name = "customadmin/product_update.html"
    fields = '__all__'
    success_message = "The Product added!"
    success_url = reverse_lazy('products_list') 

    def form_valid(self, form):

        responce = super().form_valid(form)

        return responce
    def get_success_message(self, cleaned_data):
        return f"Product: {cleaned_data['product_name']} updated successfully."
