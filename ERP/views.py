from django.contrib.auth.decorators import login_not_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView, UpdateView
from django.views.generic.edit import CreateView

from .models import Customer
from .forms.forms import CreateCustomerForm, LoginForm, RegistrationForm

def index(request):
    return render(request, "ERP/index.html")

def construction(request):
    return render(request, "ERP/construction.html")

class CustomerCreateView(CreateView):
    model = Customer
    form_class = CreateCustomerForm
    def form_valid(self, form):
        # Assign the current user as the owner
        form.instance.owner = self.request.user
        return super().form_valid(form)

class CustomerDetailView(DetailView):
    model = Customer

class CustomerListView(ListView):
    model = Customer

def delete_customer(request, pk):
    customer = Customer.objects.get(pk=pk)
    customer.delete()
    return redirect('customers')

class CustomerUpdate(UpdateView):
    model = Customer
    form_class = CreateCustomerForm
    template_name = "ERP/customer_update.html"
    def form_valid(self, form):
        super().form_valid(form)       
        # Success: Return the display fragment
        context = {'customer': self.object}
        return render(self.request, 'ERP/customer_display.html', context)
    
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