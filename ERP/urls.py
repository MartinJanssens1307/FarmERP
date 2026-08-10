from django.urls import path, include

from ERP.Views import views

urlpatterns = [
# --- General paths ---
    path("", views.index, name="index"),
    path("equipment", views.construction, name="equipment"),
    path("finance", views.construction, name="finance"),
    path('login/', views.Login.as_view(), name='login'),
    path('register/', views.register, name='register'),
    path("create_company", views.company_data, name="company_data"),
]