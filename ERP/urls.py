from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("customers", views.customers, name="customers"),
    path("customers/<int:id>", views.customer, name="customer"),
    path("crops", views.construction, name="crops"),
    path("equipment", views.construction, name="equipment"),
    path("finance", views.construction, name="finance"),
]