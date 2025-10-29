from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.views import View
from django.views.generic import DetailView, ListView
from django.views.generic.edit import CreateView

from .models import Customer, Transaction
from .forms.forms import CustomerForm, CreateCustomerForm, CustomerMainForm

def index(request):
    return render(request, "ERP/index.html")

def construction(request):
    return render(request, "ERP/construction.html")

def createCustomer(request):

    if request.method == "POST":
        form = CreateCustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('customers')
    else:
        form = CreateCustomerForm()

    return render(request, "ERP/customer_form.html", {"form": form})

class CustomerCreateView(CreateView):
    model = Customer
    form_class = CreateCustomerForm

def customers(request):
    customers = Customer.objects.all()
    return render(request, "ERP/customers.html",{
        "customers":customers
        })

class CustomerListView(ListView):
    model = Customer

def customer(request, pk):
    customer = Customer.objects.get(pk=pk)
    transactions = customer.transactions.all()

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

class CustomerDetailView(DetailView):
    model = Customer
    #template_name = "ERP/customer.html"

def delete_customer(request, pk):
    customer = Customer.objects.get(pk=pk)
    customer.delete()
    return redirect('customers')

class SimpleFormTestView(View):
    """
    PURPOSE: Renders the CustomerMainForm just to verify the Tailwind styling 
    from the Mixin is correctly applied.
    """
    def get(self, request):
        # Create a blank form instance
        form = CustomerMainForm()
        return render(request, 'ERP/test_form_display.html', {'form': form})