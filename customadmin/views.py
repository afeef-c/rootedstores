from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import Account
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# Create your views here.

def admin_login(request):
     try:
        if request.user.is_authenticated:
            messages.success(request, 'The admin logout successfully')
            return redirect('admin_home')
        
        if request.method == 'POST':
            email = request.POST['email']
            password = request.POST['password']
            
            #user_obj = User.objects.filter(email=email).first()
            user_obj = Account.objects.filter(email=email).first()
            
            if not user_obj:
                messages.info(request, 'Account not found')
                return redirect('admin_login')
            
            user = authenticate(request, email=user_obj.email, password=password)
            
            if user and user.is_superadmin:
                login(request, user)
                messages.success(request, 'The admin loged in successfully')
                return redirect('admin_home')

            messages.info(request, 'Invalid email or password')
            return redirect('admin_login')

        return render(request, 'customadmin/admin_login.html')
     except Exception as e:
        print(e)
        messages.danger(request,'error'+e)    
        return render(request, 'customadmin/admin_login.html', {'messages': 'An error occurred'})


def admin_logout(request):
    logout(request)
    messages.success(request, 'The admin logout successfully')
    return HttpResponseRedirect(reverse('admin_login'))


