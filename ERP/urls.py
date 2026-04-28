from django.urls import path

from ERP.Views import views, customer_views, address_views, product_views, transaction_views

urlpatterns = [
# --- General paths ---
    path("", views.index, name="index"),
    path("crops", views.construction, name="crops"),
    path("equipment", views.construction, name="equipment"),
    path("finance", views.construction, name="finance"),
    path('login/', views.Login.as_view(), name='login'),
    path('register/', views.register, name='register'),

# --- Customer paths ---
    path("customers", customer_views.customer_list, name="customers"),
    path("create_customer", customer_views.customer_create, name="create_customer"),
    path("customer/<int:pk>", customer_views.customer_details, name="customer"),
    path("customer/<int:pk>/edit", customer_views.customer_edit, name="customer_edit"),
    path("customer/delete/<int:pk>", customer_views.delete_customer, name="delete_customer"),
# --- Address URLs ---  
    path("addresses/<int:customer_id>", address_views.address_list, name="addresses"),
    path("address/create/<int:pk>", address_views.address_create, name="create_address"),
    path("address/edit/<int:pk>", address_views.address_edit, name="edit_address"),
    path("address_row/<int:address_id>", address_views.get_address_row, name="get_address_row"),
    path("address/delete/<int:pk>", address_views.delete_address, name="delete_address"),

# --- Product URLs ---
    path('products/', product_views.product_list, name='products'),
    path('product/create/', product_views.product_create, name='product_create'),
    path('product/<int:pk>/', product_views.product_details, name='product_detail'),
    path('product/<int:pk>/edit/', product_views.product_edit, name='product_edit'),
    path('product/<int:pk>/delete/', product_views.delete_product, name='delete_product'),

# --- Transaction paths ---
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<int:pk>/delete', transaction_views.transaction_delete, name='transaction_delete'),

# --- Transaction alternate paths ---
    path('transaction/create', transaction_views.transaction_create, name='transaction_creation'),
    path('transaction/add-line/', transaction_views.get_line_item, name='get_line_item'),
    path('transaction/<int:pk>', transaction_views.transaction_details, name='transaction_details'),
    path('transaction_partial/<int:customer_id>', transaction_views.transactions_partial, name='transaction_list_partial'),
    path('transaction_print/<int:pk>', transaction_views.transaction_print, name='transaction_print'),
]