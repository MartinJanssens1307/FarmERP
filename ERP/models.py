from django.db import models

# Create your models here.
class Customer(models.Model):
    name = models.CharField(max_length=64)
    address = models.CharField(max_length=64)
    phone = models.CharField(max_length=12, blank=True)
    email = models.CharField(max_length=64, blank=True)
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=64)
    description = models.TextField(max_length=250)
    unit_price = models.IntegerField()
    def __str__(self):
        return self.name
class Transaction(models.Model):
    type = models.CharField(max_length=8, choices=[("sale", "Sale"), ("purchase", "Purchase")])
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="transactions")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="transactions")
    quantity = models.IntegerField()
    amount = models.IntegerField()
    def __str__(self):
        return f"{self.type.capitalize()} with {self.customer} for €{self.amount}"