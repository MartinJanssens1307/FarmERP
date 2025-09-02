from django.shortcuts import redirect, render
from django.http import HttpResponse

from .models import Customer

def index(request):
    return render(request, "ERP/index.html")

def construction(request):
    return render(request, "ERP/construction.html")

def customers(request):
    customers = Customer.objects.all()
    return render(request, "ERP/customers.html",{
        "customers":customers
        })

def customer(request, id):

    customer = Customer.objects.get(pk=id)
    return render(request, "ERP/customer.html",{
        "customer":customer
    })