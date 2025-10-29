from django.urls import path
from django.views.generic import TemplateView

from . import views
from .forms import partials
from .forms.partials import editCustomer
from .views import CustomerDetailView, CustomerListView, CustomerCreateView, SimpleFormTestView

urlpatterns = [
#General paths
    path("", views.index, name="index"),
    path("create_customerx", views.createCustomer, name="createcustomer"),
    path("customersx", views.customers, name="customersx"),
    path("customersx/<int:pk>", views.customer, name="customerx"),
    path("customers/delete/<int:pk>", views.delete_customer, name="delete_customer"),
    path("crops", views.construction, name="crops"),
    path("equipment", views.construction, name="equipment"),
    path("finance", views.construction, name="finance"),
#Partial paths
    path("editCustomer", partials.editCustomer, name="editCustomer"),
    path("about", TemplateView.as_view(template_name="ERP/index.html")),
    path("create_customer", CustomerCreateView.as_view(), name="create_customer"),
    path("customers", CustomerListView.as_view(), name="customers"),
    path("customers/<int:pk>", CustomerDetailView.as_view(), name="customer"),
    path("test_styling", SimpleFormTestView.as_view())
]