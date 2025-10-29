from django import forms
from ..models import Customer, Transaction
from .mixins import TailwindFormMixin

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'address', 'phone', 'email', 'role']

class CreateCustomerForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = '__all__'

class CustomerMainForm(TailwindFormMixin, forms.ModelForm):
    """
    This form will automatically have Tailwind styling on all fields 
    because it inherits from TailwindFormMixin.
    """
    class Meta:
        model = Customer
        fields = ['name', 'address', 'phone', 'email', 'role']