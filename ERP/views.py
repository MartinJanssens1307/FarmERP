from django.shortcuts import redirect, render
from django.http import HttpResponse

from .models import Customer, Transaction
from django import forms

def index(request):
    return render(request, "ERP/index.html")

def construction(request):
    return render(request, "ERP/construction.html")

def createCustomer(request):
    class CustomerForm(forms.ModelForm):
        class Meta:
            model = Customer
            fields = '__all__'

    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customers')
    else:
        form = CustomerForm()

    return render(request, "ERP/createCustomer.html", {"form": form})

def customers(request):
    customers = Customer.objects.all()
    return render(request, "ERP/customers.html",{
        "customers":customers
        })

def customer(request, id):
    customer = Customer.objects.get(pk=id)
    transactions = customer.transactions.all()

    class CustomerForm(forms.ModelForm):
        class Meta:
            model = Customer
            fields = ['name', 'address', 'phone', 'email']

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('customer', id=id)
    else:
        form = CustomerForm(instance=customer)

    return render(request, "ERP/customer.html",{
        "customer": customer,
        "transactions": transactions,
        "form": form
    })

def delete_customer(request, id):
    customer = Customer.objects.get(pk=id)
    customer.delete()
    return redirect('customers')