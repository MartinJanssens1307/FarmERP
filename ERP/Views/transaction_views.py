from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db import transaction as db_transaction

from ERP.models import Transaction, TransactionLineItem
from ERP.forms.forms import CreateTransactionForm, TransactionLineItemFormSet

def transaction_list(request):
    transactions = Transaction.objects.filter(tenant=request.tenant).order_by('-creation_date')
    context = {'transaction_list':transactions}
    return render(request, 'ERP/transactions/transaction_list.html', context)

def transaction_create(request):
    if request.method == "POST":
        form = CreateTransactionForm(request.POST, tenant=request.tenant)
        formset = TransactionLineItemFormSet(request.POST, form_kwargs={'tenant': request.tenant})
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                transaction = form.save(commit=False)
                transaction.tenant = request.tenant
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
        formset = TransactionLineItemFormSet(form_kwargs={'tenant': request.tenant})
    context = {'form':form, 'formset':formset}
    return render(request, 'ERP/transactions/transaction_create_form.html', context)

def transaction_details(request, pk):
    transaction = get_object_or_404(Transaction.objects.prefetch_related('line_items'), pk=pk)
    return render(request, 'ERP/transactions/transaction_details.html', {'transaction':transaction, 'line_items':transaction.line_items.all()})

@require_http_methods(["POST", "DELETE"])
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, id=pk)
    if transaction.status != 'completed':  
        transaction.delete()
        return HttpResponse('')

def get_line_item(request):
    formset=TransactionLineItemFormSet(form_kwargs={'tenant': request.tenant})
    form=formset.empty_form
    return render(request, 'ERP/transactions/_line_item_row.html', {'form':form})

def transactions_partial(request, customer_id):
    transactions=Transaction.objects.filter(customer=customer_id, tenant=request.tenant)
    return render(request, 'ERP/transactions/transaction_list.html#transaction_list', {'transaction_list':transactions})

def transaction_print(request, pk):
    transaction=get_object_or_404(Transaction.objects.prefetch_related('line_items'), pk=pk)
    context={
        'transaction': transaction,
        'line_items': transaction.line_items.all(),
        'billing':transaction.billing_snapshot,
        'issuer':transaction.issuer_snapshot
    }
    return render(request, 'ERP/transactions/transaction_print.html', context)

def transaction_validate(request, pk):
    transaction = get_object_or_404(Transaction, id=pk)
    transaction.validate_and_freeze()
    response = render(request, 'ERP/transactions/transaction_details.html#transaction_actions', {
        'transaction': transaction
    })
    # This header is the magic link
    response['HX-Trigger'] = 'transaction-updated'
    return response