from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from ERP.models import Customer
from ERP.forms.forms import CreateCustomerForm
 
def customer_list(request):
    customers = Customer.objects.filter(owner=request.user)
    context = {'customer_list':customers}
    return render(request, 'ERP/Customer/customer_list.html', context)

def customer_create(request):
    if request.method =="POST":
        form = CreateCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.owner = request.user
            customer.save()
            return render(request, 'ERP/Customer/customer_detail.html', {'customer':customer})
    
    form = CreateCustomerForm()
    context = {"form":form}
    return render(request, 'ERP/Customer/customer_form.html', context)

def customer_details(request, pk):
    customer = get_object_or_404(Customer.objects.prefetch_related('addresses'), pk=pk, owner=request.user)
    if request.headers.get('HX-Request'):
        return render(request, 'ERP/Customer/customer_detail.html#display_content', {'customer':customer})
    return render(request, 'ERP/Customer/customer_detail.html', {'customer':customer, 'addresses':customer.addresses.all()})

def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, owner=request.user)
    if request.method == "POST":
        form = CreateCustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            return render(request, 'ERP/Customer/customer_detail.html#display_content', {'customer':customer})
    else:
        form = CreateCustomerForm(instance=customer) 
    
    return render(request, 'ERP/Customer/customer_detail.html#form_content', {'customer':customer, 'form':form})

@require_http_methods(["DELETE"])
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk, owner=request.user)
    customer.delete()
    return HttpResponse('')