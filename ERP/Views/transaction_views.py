from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db import transaction as db_transaction

from ERP.models import Transaction, TransactionLineItem
from ERP.forms.forms import CreateTransactionForm, TransactionLineItemFormSet

def transaction_create(request):
    if request.method == "POST":
        form = CreateTransactionForm(request.POST)
        formset = TransactionLineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                transaction = form.save(commit=False)
                transaction.owner = request.user
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
        form = CreateTransactionForm()
        formset = TransactionLineItemFormSet()
    context = {'form':form, 'formset':formset}
    return render(request, 'ERP/transactions/transaction_create_form.html', context)

def transaction_details(request, pk):
    transaction = get_object_or_404(Transaction.objects.prefetch_related('line_items'), pk=pk)
    return render(request, 'ERP/transactions/transaction_details.html', {'transaction':transaction, 'line_items':transaction.line_items.all()})

@require_http_methods(["POST", "DELETE"])
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, id=pk)
    transaction.delete()
    return HttpResponse('')

def get_line_item(request):
    formset=TransactionLineItemFormSet()
    form=formset.empty_form
    return render(request, 'ERP/transactions/_line_item_row_copy.html', {'form':form})

def transactions_partial(request):
    transactions=Transaction.objects.filter(owner=request.user)
    return render(request, 'ERP/transactions/transaction_list.html#transaction_list', {'transaction_list':transactions})

def transaction_print(request, pk):
    transaction=get_object_or_404(Transaction.objects.select_related('customer').prefetch_related('line_items'), pk=pk)
    context={
        'transaction': transaction,
        'customer': transaction.customer,
        'line_items': transaction.line_items.all(),
    }
    return render(request, 'ERP/transactions/transaction_print.html', context)