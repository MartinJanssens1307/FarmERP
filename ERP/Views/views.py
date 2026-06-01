from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy

from ERP.forms.forms import LoginForm, RegistrationForm, CreateCompanyForm
from ERP.models import Company, CompanyAccess
from .utils import get_current_company

#General views
def index(request):
    return render(request, "ERP/index.html")

def construction(request):
    return render(request, "ERP/construction.html")

#Authentication views
class Login(LoginView):
    authentication_form = LoginForm

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

@login_required
def company_data(request):
    company = get_current_company(request)
    if request.method=='POST':
        #get_object_or_404(Company, pk=request.session.get('current_company_id'))
        form = CreateCompanyForm(request.POST, instance=company)
        if form.is_valid():
            tenant=form.save()
            CompanyAccess.objects.get_or_create(user=request.user, company=tenant, role='OW')
            return redirect('index')
    form = CreateCompanyForm(instance=company)
    context = {"form":form}
    return render(request, 'ERP/Company/company_form.html', context)