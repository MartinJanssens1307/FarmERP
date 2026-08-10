from django.contrib import admin
from .models import CadastralParcel
from django.apps import apps

# Register your models here.
models = apps.get_app_config('Fields').get_models()
for model in models:
    admin.site.register(model)
# Register your models here.
