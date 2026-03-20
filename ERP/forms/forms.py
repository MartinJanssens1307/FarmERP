from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.forms import inlineformset_factory, BaseInlineFormSet
from ERP.models import Address, Customer, Product, Transaction, TransactionLineItem
from .mixins import TailwindFormMixin

class LoginForm(TailwindFormMixin, AuthenticationForm):
    pass

class RegistrationForm(TailwindFormMixin, UserCreationForm):
    pass

class CreateCustomerForm(TailwindFormMixin, forms.ModelForm):
    """
    This form will automatically have Tailwind styling on all fields 
    because it inherits from TailwindFormMixin.
    """
    class Meta:
        model = Customer
        fields = ('title', 'name', 'first_name', 'phone', 'email', 'tva_number')
        widgets = {
            'email': forms.EmailInput(attrs={'type': 'email'}),
            'phone_number': forms.TextInput(attrs={'type': 'tel'}),
        }

class CreateAddressForm(TailwindFormMixin, forms.ModelForm):
     class Meta:
          model = Address
          exclude = ['partner']

class CreateProductForm(TailwindFormMixin, forms.ModelForm):
     class Meta:
          model = Product
          fields = ('name', 'description', 'unit_measure', 'unit_price', 'type')

# Define the form for the individual line item (used by the formset)
class TransactionLineItemForm(TailwindFormMixin, forms.ModelForm):
    # Use ModelChoiceField with a custom queryset to restrict product choices 
    # to those owned by the current user (if Product has an 'owner' field)
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(), # You'll need to filter this in the view later
        label="Product"
    )
    total_gross = forms.DecimalField(required=False)
    
    class Meta:
        model = TransactionLineItem
        fields = ['product', 'quantity', 'unit_price_net','vat_rate_percentage','total_gross'] 

# 1. On crée une classe qui hérite du comportement de base
class BaseTransactionLineItemFormSet(BaseInlineFormSet):
    def validate_unique(self):
        # En ne faisant rien ici, on désactive la vérification des doublons
        return 

# 2. On passe cette classe à la factory via l'argument 'formset'
# Create the Formset Factory
# We link the Parent model (Transaction) to the Child model (TransactionLineItem)
TransactionLineItemFormSet = inlineformset_factory(
    Transaction, 
    TransactionLineItem,
    form=TransactionLineItemForm, # Ton formulaire de ligne
    formset=BaseTransactionLineItemFormSet, # <--- C'est ici qu'on branche la logique
    extra=1,
    can_delete=True
)


class CreateTransactionForm(TailwindFormMixin, forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['customer','type','status']