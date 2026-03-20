from django.contrib.auth.decorators import login_not_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.db import transaction as db_transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView
from django.views.generic.edit import CreateView

from ERP.models import Transaction
from ERP.forms.forms import LoginForm, RegistrationForm, TransactionLineItemFormSet

#General views
@login_not_required   
def index(request):
    return render(request, "ERP/index.html")

def construction(request):
    return render(request, "ERP/construction.html")

#Authentication views
class Login(LoginView):
    authentication_form = LoginForm

@login_not_required   
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Optionally log the user in immediately after registration
            login(request, user)
            messages.success(request, f"Registration successful. Welcome, {user.username}!")
            return redirect('index')  # Redirect to your customer list
    else:
        form = RegistrationForm()
    return render(request, 'ERP/register.html', {'form': form})
  
#Transaction related views
class TransactionListView(ListView):
    model = Transaction
    template_name = 'ERP/transactions/transaction_list.html'
    context_object_name = 'transaction_list' # Use a clearer variable name in the template
    
    def get_queryset(self):
        # **Security Filter**
        # Only show transactions owned by the current logged-in user
        return Transaction.objects.filter(owner=self.request.user).order_by('-creation_date')

class TransactionCreateView(CreateView):
    model = Transaction
    # Fields for the main header (customer, type, status)
    fields = ['customer', 'type', 'status'] 
    template_name = 'ERP/transactions/transaction_create_form.html'
    success_url = reverse_lazy('transaction_list') # Assuming you will create this list view later

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Security: Limit the customer choices to those owned by the user
        # Filter by Customer instances (not BusinessPartner) owned by the user
        from ERP.models import Customer
        form.fields['customer'].queryset = Customer.objects.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        # Security: Automatically set the owner upon creation
        form.instance.owner = self.request.user
        return super().form_valid(form)

class TransactionUpdateView(UpdateView):
    model = Transaction
    # Fields for the main Transaction header (excluding total_amount, which is calculated)
    fields = ['customer', 'type', 'status'] 
    template_name = 'ERP/transactions/transaction_form.html'
    
    # 1. Ensure security filter is applied
    def get_queryset(self):
        return Transaction.objects.filter(owner=self.request.user)

    # 2. Add the formset to the context for display
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            # Re-bind the formset if validation failed
            data['line_item_formset'] = TransactionLineItemFormSet(
                self.request.POST, 
                instance=self.object,
                queryset=self.object.line_items.all()
            )
        else:
            # Initial load: pass the empty formset instance
            data['line_item_formset'] = TransactionLineItemFormSet(instance=self.object)
        
        # Pass the Products queryset, filtered by owner, to the Formset's Product choice field
        # Note: This is an advanced step, often handled by customizing the Formset initialization
        # For simplicity, ensure the queryset in forms.py is correct or let Django handle it if Product doesn't have an owner FK
        return data

    # 3. Handle saving the main form and the formset atomically
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        formset = TransactionLineItemFormSet(self.request.POST, instance=self.object)

        if form.is_valid() and formset.is_valid():
            with db_transaction.atomic():
                self.object = form.save()
                formset.instance = self.object
                formset.save()
                
                # After saving, trigger the total calculation and save the header again
                self.object.total_amount = self.object.calculate_total()
                self.object.save()
                
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
def add_line_item(request, pk):
    """Handles HTMX request to add one empty line item row."""
    if request.method == 'POST':
        # Get the current transaction object (for the formset instance)
        transaction_obj = get_object_or_404(Transaction, pk=pk, owner=request.user)
        
        # Determine the next available index (Django manages TOTAL_FORMS)
        formset = TransactionLineItemFormSet(request.POST, instance=transaction_obj)
        
        # We need the formset management data from the POST request
        # The key is to access the raw prefix count
        # Default index is set to 0, if not found (shouldn't happen with a formset)
        formset_prefix = formset.prefix
        
        # Extract the current total number of forms submitted
        try:
            total_forms = int(request.POST.get(f'{formset_prefix}-TOTAL_FORMS'))
        except (ValueError, TypeError):
            total_forms = 0

        # Create a new, empty form instance with the correct next index
        new_form = formset.empty_form
        new_form.prefix = f'{formset_prefix}-{total_forms}'
        
        # Render the HTML fragment for the new row
        context = {
            'form': new_form,
            'is_new': True,
        }
        
        # NOTE: We return only the rendered template partial
        return render(request, 'transactions/_line_item_row.html', context)
    
    # Return 400 Bad Request if not a POST request
    return HttpResponse(status=400)

def calculate_totals(request, pk):
    """Handles HTMX request to recalculate line and transaction totals."""
    if request.method == 'POST':
        # 1. Get the transaction object (to pass to the formset)
        # Ensure security filter is applied
        transaction_obj = get_object_or_404(Transaction, pk=pk, owner=request.user)
        
        # 2. Bind the formset with the full POST data sent via hx-include
        formset = TransactionLineItemFormSet(request.POST, instance=transaction_obj)
        
        # 3. Process the formset data
        updated_totals_data = {}
        overall_total = 0.0

        if formset.is_valid():
            for form in formset.forms:
                # Check for forms not marked for deletion and with all necessary data
                if not form.cleaned_data.get('DELETE', False) and form.cleaned_data.get('product'):
                    quantity = form.cleaned_data.get('quantity') or 0
                    price = form.cleaned_data.get('unit_price_net') or 0
                    
                    try:
                        line_total = float(quantity) * float(price)
                    except (ValueError, TypeError):
                        line_total = 0.0

                    # Store the updated line total for OOB swap
                    updated_totals_data[form.prefix] = f"{line_total:.2f}"
                    
                    # Accumulate for the overall total
                    overall_total += line_total
        
        # 4. Render the OOB fragment
        context = {
            'updated_totals_data': updated_totals_data, 
            'overall_total': f"{overall_total:.2f}"
        }
        
        # Render the template that contains the OOB swaps
        return render(request, 'transactions/_total_update_fragment.html', context)
    
    return HttpResponse(status=400)