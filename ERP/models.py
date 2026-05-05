from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Max
from django.urls import reverse

# Create your models here.
class BusinessPartner(models.Model):
    title = models.CharField(max_length=5, blank=True, choices=[('MR', 'Mr'), ('MME', 'Mme')])
    name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=64, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='partners')
    ROLES = [('CUS', 'Customer'), ('SUP', 'Supplier'), ('CON', 'Contact'), ('GEN', 'General')]
    role = models.CharField(max_length=3, choices=ROLES, default='CUS')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.name} as {self.role}"
    
class Address(models.Model):
    street = models.CharField(max_length=64)
    number = models.CharField(max_length=12)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=64)
    p_o = models.CharField(max_length=12, verbose_name="p.o box", blank=True)
    CountryList = [("be", "Belgium"),("fr", "France"),("nl","Netherlands"),("de","Germany")]
    country = models.CharField(choices=CountryList)
    partner = models.ForeignKey(BusinessPartner, on_delete=models.CASCADE, related_name='addresses')
    is_shipping = models.BooleanField(default=True)
    is_billing = models.BooleanField(default=True)
    is_shipping_default = models.BooleanField(default=False)
    is_billing_default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['partner'],
                condition=models.Q(is_billing_default=True),
                name='unique_default_billing_per_partner'
            ),
            models.UniqueConstraint(
                fields=['partner'],
                condition=models.Q(is_shipping_default=True),
                name='unique_default_shipping_per_partner'
            )
        ]

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.is_billing_default:
                # transaction.atomic() ensures that if the 'uncheck' fails, 
                # the 'save' also fails. Total data safety.
                Address.objects.filter(
                    partner=self.partner, 
                    is_billing_default=True
                    ).exclude(pk=self.pk).update(is_billing_default=False)
                self.is_billing = True
            if self.is_shipping_default:
                Address.objects.filter(
                    partner=self.partner, 
                    is_shipping_default=True 
                ).exclude(pk=self.pk).update(is_shipping_default=False)
                self.is_shipping = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.street}, {self.number} {self.city}"

class Customer(BusinessPartner):
    tva_number = models.CharField(max_length=32, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.name}"
    
    def get_absolute_url(self):
        return reverse("customer", kwargs={"pk":self.pk})
    
    def get_billing_address(self):
        return (self.addresses.filter(is_billing_default=True).first() or 
                self.addresses.filter(is_billing=True).first() or
                self.addresses.first()
                )

    def get_shipping_address(self):
        return (self.addresses.filter(is_shipping_default=True).first() or 
                self.addresses.filter(is_shipping=True).first())

class Product(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=250)
    unit_measure = models.CharField(max_length=3, choices=[("kg", "Kg"), ("l", "L"), ("t", "Ton"), ("u", "Unit"), ("h", "Hour"),("a", "Are"),("ha", "Hectare")])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=3, choices=[("o", "Object"), ("s", "Service")], default='o')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
        
class Transaction(models.Model):
    creation_date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="transactions")
    total_net = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_vat = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_gross = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    type = models.CharField(max_length=8, choices=[("sale", "Sale"), ("purchase", "Purchase")], default='sale')
    status = models.CharField(max_length=20, choices=[("new", "New"), ("progress", "In Progress"), ("cancelled", "Cancelled"), ("completed", "Completed")], default='new')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    # The math part (still used for Max+1)
    local_sequence = models.PositiveIntegerField(null=True, blank=True, editable=False)
    # The permanent record part (unalterable after save)
    public_id = models.CharField(max_length=30, null=True, blank=True, editable=False)
    # The address snapshot (JSON)
    billing_snapshot = models.JSONField(null=True, blank=True, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['owner', 'public_id'], 
                name='unique_public_id_per_owner'
            )
        ]

    def calculate_totals(self):
        """Calculates the sum of all related line item totals."""
        from django.db.models import Sum
        totals = self.line_items.aggregate(net=Sum('total_net'), vat=Sum('total_vat'), gross=Sum('total_gross'))
        return {
            'gross': totals['gross'] or 0,
            'net': totals['net'] or 0,
            'vat': totals['vat'] or 0
        }
    
    def save(self, *args, **kwargs):
        # Si on valide la transaction et qu'elle n'a pas encore de numéro
        if self.status == 'completed' and not self.public_id:
            with transaction.atomic():
                # 1. Calcul de la séquence (seulement au moment de la validation)
                last_no = Transaction.objects.filter(
                    owner=self.owner,
                    status='completed' # On ne compte que les validées
                ).aggregate(Max('local_sequence'))['local_sequence__max']
                
                self.local_sequence = (last_no or 0) + 1
                
                # 2. On fige le numéro et l'adresse
                year = self.creation_date.year if self.creation_date else 2026
                self.public_id = f"INV-{year}-{self.local_sequence:04d}"
                
                address = self.customer.get_billing_address()
                if address:
                    self.billing_snapshot = {
                        "name": f"{self.customer.title} {self.customer.name} {self.customer.first_name}",
                        "address1": f"{address.street} {address.number}",
                        "address2": f"{address.postal_code} {address.city}",
                        "address3": f"{address.get_country_display()}"
                    }
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.type.capitalize()} with {self.customer} for €{self.total_gross}"
    
class TransactionLineItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price_net = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    total_net = models.DecimalField(max_digits=12, decimal_places=2) # Qty * Price
    total_vat = models.DecimalField(max_digits=12, decimal_places=2) # Net * (VAT/100)
    total_gross = models.DecimalField(max_digits=12, decimal_places=2) # Net + VAT

    def save(self, *args, **kwargs):
        # Automatically calculate the line_total before saving
        self.total_net = self.quantity * self.unit_price_net
        self.total_vat = self.total_net * (self.vat_rate_percentage / 100)
        self.total_gross = self.total_net + self.total_vat
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} on Transaction #{self.transaction.pk}"