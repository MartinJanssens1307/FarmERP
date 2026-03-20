from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods

from ERP.models import Product
from ERP.forms.forms import CreateProductForm

def product_list(request):
    products = Product.objects.filter(owner=request.user)
    context = {'product_list': products}
    return render(request, 'ERP/inventory/product_list.html', context)

def product_create(request):
    if request.method == "POST":
        form = CreateProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.owner = request.user
            product.save()
            return redirect('product_detail', pk=product.pk)

    form = CreateProductForm()
    context = {"form": form}
    return render(request, 'ERP/inventory/product_form.html', context)

def product_details(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.headers.get('HX-Request'):
        return render(request, 'ERP/inventory/product_detail.html#display_content', {'product': product})
    return render(request, 'ERP/inventory/product_detail.html', {'product': product})

def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    if request.method == "POST":
        form = CreateProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return render(request, 'ERP/inventory/product_detail.html#display_content', {'product': product})
    else:
        form = CreateProductForm(instance=product)

    return render(request, 'ERP/inventory/product_detail.html#form_content', {'product': product, 'form': form})

@require_http_methods(["POST", "DELETE"])
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, owner=request.user)
    product.delete()
    #Separate table line delete (htmx delete) from object page delete (form post)
    if request.method == "DELETE":
        return HttpResponse('')
    return redirect('products')
