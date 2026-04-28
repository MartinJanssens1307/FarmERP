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