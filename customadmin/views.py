import os
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import Account
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.models import *
from orders.models import Order, OrderProduct, Payment
from store.models import *
from category.models import Category
from django.db.models.functions import ExtractMonth
from django.utils.dateparse import parse_date
from django.db.models import Q

import xhtml2pdf.pisa as pisa
from django.template.loader import render_to_string




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
        messages.danger(request,'error'+e)    
        return render(request, 'customadmin/admin_login.html', {'messages': 'An error occurred'})


def admin_logout(request):
    logout(request)
    messages.success(request, 'The admin logout successfully')
    return HttpResponseRedirect(reverse('admin_login'))

#==========================================================================================================

def sales(request):
    
    orders = Order.objects.all()
    orders_count = orders.count()
    users = Account.objects.filter(is_active=True)
    user_count = users.count()
    sales_count = OrderProduct.objects.all().count()


    total_revenue = 0
    payment = Payment.objects.filter(status='SUCCESS')
    for i in payment:
        total_revenue += float(i.amount_paid) 
    total_revenue = round(total_revenue,2)
    #order_products = OrderProduct.objects.filter(order_id= order.id)
    context = {
        'orders':orders,
        'orders_count':orders_count,
        'user_count':user_count,
        'total_revenue':total_revenue,
        'sales_count':sales_count
        
    }

    return render(request, 'customadmin/reports/sales.html', context)


def filter_orders(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Check if both start_date and end_date are provided
        if start_date and end_date:
            
            if start_date > end_date:
                messages.error(request, 'Start date must be before end date.')
                # Redirect back to the same page or any other appropriate URL
                return HttpResponseRedirect(reverse('sales'))  # Use the correct name here
            else:
                request.session['start_date'] = start_date
                request.session['end_date'] = end_date
                # Filter orders based on the submitted date range
                users = Account.objects.filter(is_active=True)
                orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
                orders_count = orders.count()
                user_count = users.count()
                sales_count = OrderProduct.objects.filter(created_at__gte=start_date, created_at__lte=end_date).count()


                total_revenue = 0
                payment = Payment.objects.filter(status='SUCCESS', created_at__gte=start_date, created_at__lte=end_date)
                for i in payment:
                    total_revenue += float(i.amount_paid) 
                total_revenue = round(total_revenue, 2)
                
                
                context = {
                    'start_date': start_date,
                    'end_date': end_date,
                    'orders': orders,
                    'orders_count': orders_count,
                    'total_revenue':total_revenue,
                    'sales_count':sales_count,
                    'user_count':user_count
                }
                return render(request, 'customadmin/reports/sales.html', context)
        
        else:
            
            # If start_date or end_date is missing, display an error message
            messages.error(request, 'Please provide both start date and end date.')
            # Redirect back to the same page or any other appropriate URL
            return HttpResponseRedirect(reverse('sales'))  # Use the correct name here
    else:
        # Render the template with the form initially
        return render(request, 'customadmin/reports/sales.html')
    


def generate_pdf_from_template(template_name, context, filename):
    # Render the template with the given context
    html_content = render_to_string(template_name, context)

    # Create a response object
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'

    # Generate PDF from HTML content
    pisa_status = pisa.CreatePDF(
        html_content,
        dest=response
    )

    # If PDF generation failed, return an error response
    if pisa_status.err:
        return HttpResponse('PDF generation failed.')

    return response
def generate_sales_pdf(request):
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        if start_date :
            users = Account.objects.filter(is_active=True)
            user_count = users.count()
            sales_count = OrderProduct.objects.filter(created_at__gte=start_date, created_at__lte=end_date).count()

            # Check if both start_date and end_date are provided
            orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
            orders_count = orders.count()

            total_revenue = 0
            payment = Payment.objects.filter(status='SUCCESS', created_at__gte=start_date, created_at__lte=end_date)
            for i in payment:
                total_revenue += float(i.amount_paid) 
            total_revenue = round(total_revenue, 2)

            context = {
                'start_date': start_date,
                'end_date': end_date,
                'orders': orders,
                'orders_count': orders_count,
                'total_revenue': total_revenue,
                'sales_count': sales_count,
                'user_count': user_count,
            }

            # Generate PDF from the invoice template
            pdf_response = generate_pdf_from_template('customadmin/reports/sales_report.html', context, 'Sales_report-from{start_date} to {end_date}')

            return pdf_response
        else:
            orders = Order.objects.all()
            orders_count = orders.count()
            users = Account.objects.filter(is_active=True)
            user_count = users.count()
            sales_count = OrderProduct.objects.all().count()


            total_revenue = 0
            payment = Payment.objects.filter(status='SUCCESS')
            for i in payment:
                total_revenue += float(i.amount_paid) 
            total_revenue = round(total_revenue,2)
            #order_products = OrderProduct.objects.filter(order_id= order.id)
            context = {
                'orders':orders,
                'orders_count':orders_count,
                'user_count':user_count,
                'total_revenue':total_revenue,
                'sales_count':sales_count
                
            }
            # Generate PDF from the invoice template
            pdf_response = generate_pdf_from_template('customadmin/reports/sales_report.html', context, f"Sales_report")

            return pdf_response

    else:
        # Render the form for inputting start and end dates
        return render(request, 'sales_report_form.html')
