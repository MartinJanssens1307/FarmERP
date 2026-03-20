from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods

from ERP.models import Address
from ERP.forms.forms import CreateAddressForm, Customer

def address_list(request, customer_id):
    addresses = Address.objects.filter(partner_id=customer_id)
    customer = get_object_or_404(Customer, pk=customer_id)
    return render(request, "ERP/address/address_detail.html", {"addresses": addresses, "customer": customer})

def address_create(request, pk):
    customer = get_object_or_404(Customer, pk=pk, owner=request.user)
    if request.method =="POST":
        form = CreateAddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.partner=customer
            address.save()
            return render(request, 'ERP/address/address_detail.html#address_line', {'address': address,'customer':customer})

    form = CreateAddressForm()
    context = {"form": form, 'customer': customer}
    return render(request, 'ERP/address/address_detail.html#address_row_form', context)

def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, partner__owner=request.user)
    if request.method == "POST":
        form = CreateAddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return render(request, 'ERP/address/address_detail.html#address_line', {'address': address, 'customer': address.partner})
    else:
        form = CreateAddressForm(instance=address)
    
    context = {"form": form, 'address': address, 'customer': address.partner}
    return render(request, 'ERP/address/address_detail.html#address_row_form', context)

def get_address_row(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    return render(request, "ERP/address/address_detail.html#address_line", {"address": address})

@require_http_methods(["DELETE"])
def delete_address(request, pk):
    address = Address.objects.get(pk=pk, partner__owner = request.user)
    address.delete()
    return HttpResponse('')