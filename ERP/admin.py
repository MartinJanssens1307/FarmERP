from django.contrib import admin
from .models import Customer, Product
from django.apps import apps

# Register your models here.
models = apps.get_app_config('ERP').get_models()
for model in models:
    admin.site.register(model)