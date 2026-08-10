from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from ERP.models import Customer
from ERP.forms.forms import CreateCustomerForm
from ERP.services_peppol import check_peppol_customer
 
def customer_list(request):
    customers = Customer.objects.filter(tenant=request.tenant)
    context = {'customer_list':customers}
    return render(request, 'ERP/Customer/customer_list.html', context)

def customer_create(request):
    if request.method =="POST":
        form = CreateCustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.tenant = request.tenant
            customer.save()
            return render(request, 'ERP/Customer/customer_detail.html', {'customer':customer})
    
    form = CreateCustomerForm()
    context = {"form":form}
    return render(request, 'ERP/Customer/customer_form.html', context)

def customer_details(request, pk):
    customer = get_object_or_404(Customer.objects.prefetch_related('addresses'), pk=pk, tenant=request.tenant)
    if request.headers.get('HX-Request'):
        return render(request, 'ERP/Customer/customer_detail.html#display_content', {'customer':customer})
    return render(request, 'ERP/Customer/customer_detail.html', {'customer':customer, 'addresses':customer.addresses.all()})

def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk, tenant=request.tenant)
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
    customer = get_object_or_404(Customer, pk=pk, tenant=request.tenant)
    customer.delete()
    return HttpResponse('')

@require_http_methods(["POST"])
def verify_customer_peppol_status(request, pk):
    """Vue dédiée HTMX pour vérifier et mettre à jour le statut Peppol d'un client"""
    customer = get_object_or_404(Customer, id=pk, tenant=request.tenant)
    
    # Appel à notre service validé
    peppol_identifier = customer.get_peppol_scheme_format()
    result = check_peppol_customer(peppol_identifier)
    
    if result.get("success"):
        customer.peppol_status = 'ACT'
    else:
        customer.peppol_status = 'IN'
        
    customer.last_peppol_check = timezone.now()
    customer.save()
    
    # On renvoie uniquement le fragment de template du badge
    return render(request, "ERP/Customer/customer_detail.html#peppol_badge", {"customer": customer})