from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db import transaction as db_transaction

from ERP.models import Transaction, Product
from ERP.forms.forms import CreateTransactionForm, TransactionLineItemFormSet, TransactionLineItemForm
import json

def transaction_list(request):
    transactions = Transaction.objects.filter(tenant=request.tenant).order_by('-creation_date')
    context = {'transaction_list':transactions}
    return render(request, 'ERP/transactions/transaction_list.html', context)

def transaction_create(request):
    if request.method == "POST":
        form = CreateTransactionForm(request.POST, tenant=request.tenant)
        formset = TransactionLineItemFormSet(
            request.POST, 
            prefix='line_items',
            form_kwargs={'tenant': request.tenant}
        )       
        
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                transaction = form.save(commit=False)
                transaction.tenant = request.tenant
                transaction.created_by=request.user
                transaction.save()
               
                formset.instance = transaction
                formset.save()
                
                totals = transaction.calculate_totals()
                transaction.total_gross = totals['gross']
                transaction.total_net = totals['net']
                transaction.total_vat = totals['vat']
         
                transaction.save()
            return redirect('transaction_details', pk=transaction.pk)
    else:
        form = CreateTransactionForm(tenant=request.tenant)
        formset = TransactionLineItemFormSet(prefix='line_items', form_kwargs={'tenant': request.tenant})
        
    return render(request, 'ERP/transactions/transaction_create_form.html', {'form': form, 'formset': formset})

def transaction_details(request, pk):
    transaction = get_object_or_404(
        Transaction.objects.prefetch_related('line_items__product'),
        pk=pk,
        tenant=request.tenant,
    )
    return render(request, 'ERP/transactions/transaction_details.html', {'transaction':transaction, 'line_items':transaction.line_items.all()})

@require_http_methods(["POST", "DELETE"])
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, id=pk, tenant=request.tenant)
    if transaction.status != 'completed':  
        transaction.delete()
        return HttpResponse('')

def get_line_item(request):
    # Pass the matching formset prefix explicitly
    formset = TransactionLineItemFormSet(
        form_kwargs={'tenant': request.tenant},
        prefix='line_items'
    )
    
    form = formset.empty_form
    current_index = request.GET.get('new_index', '0')
    
    # Override the __prefix__ placeholder cleanly matching Django's layout
    form.prefix = f"line_items-{current_index}"
    
    return render(request, 'ERP/transactions/_line_item_row.html', {'form': form})

def transactions_partial(request, customer_id):
    transactions=Transaction.objects.filter(customer=customer_id, tenant=request.tenant)
    return render(request, 'ERP/transactions/transaction_list.html#transaction_list', {'transaction_list':transactions})

def transaction_print(request, pk):
    transaction = get_object_or_404(
        Transaction.objects.prefetch_related('line_items__product'),
        pk=pk,
        tenant=request.tenant,
    )
    context={
        'transaction': transaction,
        'line_items': transaction.line_items.all(),
        'billing':transaction.billing_snapshot,
        'issuer':transaction.issuer_snapshot
    }
    return render(request, 'ERP/transactions/transaction_print.html', context)

@require_http_methods(["POST"])
def transaction_validate(request, pk):
    transaction = get_object_or_404(Transaction, id=pk, tenant=request.tenant)
    
    validation_errors = transaction.get_validation_errors()
    
    if validation_errors:
        response = render(request, 'ERP/transactions/transaction_details.html#transaction_actions', {
        'transaction': transaction})
        # On déclenche un événement personnalisé 'transaction-errors' avec les données JSON
        response['HX-Trigger'] = json.dumps({
            "transaction-errors": {
                "errors": validation_errors
            }
        })
        return response

    transaction.validate_and_freeze()
    response = render(request, 'ERP/transactions/transaction_details.html#transaction_actions', {
        'transaction': transaction
    })
    # This header is the magic link
    response['HX-Trigger'] = 'transaction-updated'
    return response

@require_http_methods(["GET"])
def update_line(request):
    """
    API endpoint that returns a product's base price and VAT rate as JSON.
    Invoked by HTMX when a user changes a product selection in a transaction line item.
    """
    # Dynamically locate the product field key regardless of formset prefix strings
    product_key = next((key for key in request.GET.keys() if 'product' in key), None)
    
    if not product_key:
        return JsonResponse({'price': 0.00, 'vat': 0.00})
        
    product_id = request.GET.get(product_key)

    # Handle empty selection placeholders gracefully (e.g., "---------")
    if not product_id:
        return JsonResponse({'price': 0.00, 'vat': 0.00})
        
    try:
        product = Product.objects.get(pk=product_id, tenant=request.tenant)
        return JsonResponse({
            'price': float(product.unit_price) if product.unit_price is not None else 0.00,
            'vat': float(product.vat_rate) if product.vat_rate is not None else 0.00
        })
    except (Product.DoesNotExist):
        return JsonResponse({'price': 0.00, 'vat': 0.00})