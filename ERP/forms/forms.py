from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from ..models import Customer, Transaction
from .mixins import TailwindFormMixin

class CreateCustomerForm(TailwindFormMixin, forms.ModelForm):
    """
    This form will automatically have Tailwind styling on all fields 
    because it inherits from TailwindFormMixin.
    """
    class Meta:
        model = Customer
        fields = ('name', 'address', 'phone', 'email', 'role')
        widgets = {
            'email': forms.EmailInput(attrs={'type': 'email'}),
            'phone_number': forms.TextInput(attrs={'type': 'tel'}),
        }

class LoginForm(TailwindFormMixin, AuthenticationForm):
    pass

class RegistrationForm(TailwindFormMixin, UserCreationForm):
    pass