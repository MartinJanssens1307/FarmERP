from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Max
from django.urls import reverse
from django.utils import timezone

CountryList = [("be", "Belgium"),("fr", "France"),("nl","Netherlands"),("de","Germany")]
# Create your models here.
class Company(models.Model):
    name = models.CharField(max_length=255)
    vat_number = models.CharField(max_length=32, blank=True, null=True)
# Legal address
    street = models.CharField(max_length=255, blank=True)
    number = models.CharField(max_length=20, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(choices=CountryList, blank=True)
# La passerelle ManyToMany vers les Users avec notre table pivot personnalisée
    users = models.ManyToManyField(User, related_name='companies', through='CompanyAccess')

    def __str__(self):
        return self.name
    
class BusinessPartner(models.Model):
    title = models.CharField(max_length=5, blank=True, choices=[('MR', 'Mr'), ('MME', 'Mme')])
    name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=64, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    tenant = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='partners')
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

class CompanyAccess(models.Model):
    ROLE_CHOICES = [('OW', 'Owner'),('EM', 'Employee'),('AC', 'Accountant')]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_permissions')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='user_permissions')
    role = models.CharField(max_length=4, choices=ROLE_CHOICES, default='OW')

    class Meta:
        # Sécurité : Un utilisateur ne peut pas avoir deux rôles différents dans la même ferme
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user.username} - {self.company.name} ({self.get_role_display()})"
        
class Customer(BusinessPartner):
    vat_number = models.CharField(max_length=32, blank=True)
    
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
    description = models.TextField(max_length=250, blank=True)
    unit_measure = models.CharField(max_length=3, blank=True, null=True, choices=[("kg", "Kg"), ("l", "L"), ("t", "Ton"), ("u", "Unit"), ("h", "Hour"),("a", "Are"),("ha", "Hectare")])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    vat_rate = models.IntegerField(blank=True, null=True)
    type = models.CharField(max_length=3, blank=True, null=True, choices=[("o", "Object"), ("s", "Service")], default='o')
    tenant = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')

    def __str__(self):
        return self.name
        
class Transaction(models.Model):
    tenant = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='transactions')
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    creation_date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="transactions")
    total_net = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_vat = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_gross = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    type = models.CharField(max_length=8, choices=[("sale", "Sale"), ("purchase", "Purchase")], default='sale')
    status = models.CharField(max_length=20, choices=[("new", "New"), ("progress", "In Progress"), ("cancelled", "Cancelled"), ("completed", "Completed")], default='new')
    # The math part (still used for Max+1)
    local_sequence = models.PositiveIntegerField(null=True, blank=True, editable=False)
    # The permanent record part (unalterable after save)
    public_id = models.CharField(max_length=30, null=True, blank=True, editable=False)
    # The address snapshot (JSON)
    billing_snapshot = models.JSONField(null=True, blank=True, editable=False)
    issuer_snapshot = models.JSONField(null=True, blank=True, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'public_id'], 
                name='unique_public_id_per_tenant'
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
    
    def get_validation_errors(self):
        """
        Vérifie la conformité légale et métier avant le gel.
        Renvoie une liste de chaînes de caractères (les erreurs), ou une liste vide si tout est OK.
        """
        errors = []

        # 1. Vérification des lignes
        if not self.line_items.exists():
            errors.append("The transaction has no item.")

        # 2. Vérification de l'émetteur (Le Tenant)
        if not self.tenant:
            errors.append("No transaction sender found.")
        elif not self.tenant.vat_number:
            errors.append("You must enter a valid VAT number to validate this transaction.")

        # 3. Vérification du client (Le Destinataire)
        if not self.customer:
            errors.append("There's no customer for this transaction")
        else:
            # Si le client est une entreprise (B2B Belgique/Europe), la TVA est obligatoire
            # Note : Adapte 'is_company' selon le nom de ton champ sur ton modèle Customer
            if not self.customer.vat_number:
                errors.append(f"The customer '{self.customer.name}' has no VAT number.")
            
            # Vérification de l'existence d'une adresse de facturation
            if not self.customer.get_billing_address():
                errors.append(f"The customer '{self.customer.name}' has no billing address.")

        return errors

    def validate_and_freeze(self):
        """
        Orchestre la validation complète de la transaction :
        1. Snapshot des lignes (produits, prix, tva)
        2. Séquence comptable et ID public immuable
        3. Snapshot des données client et adresse de facturation
        4. Snapshot des données tenant
        5. Passage au statut final
        """
        # Sécurité : Si déjà complétée, on ne fait rien (évite les doubles clics/bugs)
        if self.status == 'completed':
            return

        # On englobe TOUT dans une transaction atomique SQL
        # Si une étape plante (ex: plus de réseau, erreur DB), rien n'est enregistré.
        with transaction.atomic():
            
            # --- ÉTAPE 1 : Gravure des lignes d'items ---
            for item in self.line_items.all():
                if item.product:
                    item.product_name_snap = item.product.name
                    item.save()

            # --- ÉTAPE 2 : Calcul de la séquence métier ---
            # Condition gardée : seulement si elle n'a pas déjà un public_id
            if not self.public_id:
                last_no = Transaction.objects.filter(
                    tenant=self.tenant,
                    status='completed'
                ).aggregate(Max('local_sequence'))['local_sequence__max']
                
                self.local_sequence = (last_no or 0) + 1
                
                year = self.creation_date.year if self.creation_date else timezone.now().year
                self.public_id = f"INV-{year}-{self.local_sequence:04d}"

            # --- ÉTAPE 3 : Snapshot du client et de l'adresse ---
            if self.customer:
                address = self.customer.get_billing_address()
                if address:
                    self.billing_snapshot = {
                        "name": f"{self.customer.title} {self.customer.name} {self.customer.first_name}",
                        "vat_number":self.customer.vat_number,
                        "address1": f"{address.street}, {address.number}",
                        "address2": f"{address.postal_code} {address.city}",
                        "address3": f"{address.get_country_display()}"
                    }
            if self.tenant:
                self.issuer_snapshot = {
                "name": self.tenant.name,
                "vat_number": self.tenant.vat_number,
                "address1": f"{self.tenant.street}, {self.tenant.number}",
                "address2": f"{self.tenant.postal_code} {self.tenant.city}",
                "address3": f"{self.tenant.get_country_display()}"
                }
            # --- ÉTAPE 4 : Application du sceau officiel ---
            self.status = "completed"
            
            # Sauvegarde finale de la transaction parent
            self.save()
    
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
    product_name_snap = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        # Automatically calculate the line_total before saving
        self.total_net = self.quantity * self.unit_price_net
        self.total_vat = self.total_net * (self.vat_rate_percentage / 100)
        self.total_gross = self.total_net + self.total_vat
        if self.transaction.status == 'completed' and self.product and not self.product_name_snap:
            self.product_name_snap = self.product
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} on Transaction #{self.transaction.pk}"
    
