from django.urls import path
from django.views.generic import TemplateView

from . import views
from .views import CustomerDetailView, CustomerListView, CustomerCreateView, Login

urlpatterns = [
#General paths
    path("", views.index, name="index"),
    path("customers/delete/<int:pk>", views.delete_customer, name="delete_customer"),
    path("crops", views.construction, name="crops"),
    path("equipment", views.construction, name="equipment"),
    path("finance", views.construction, name="finance"),
    path('login/', Login.as_view(), name='login'),
    path('register/', views.register, name='register'),
#reworked paths
    path("create_customer", CustomerCreateView.as_view(), name="create_customer"),
    path("customers", CustomerListView.as_view(), name="customers"),
    path("customer/<int:pk>", CustomerDetailView.as_view(), name="customer"),
#partial paths
    path("customer/<int:pk>/update", views.CustomerUpdate.as_view(), name="customer_update"),
]