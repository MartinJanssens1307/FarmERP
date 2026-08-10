from django.urls import path, include
from Fields import views

urlpatterns = [
    path("parcels", views.parcel_list, name="parcels"),
    path("parcels/<int:parcel_id>/", views.parcel_detail, name="parcel_detail"),
    path("parcels/<int:parcel_id>/delete/", views.delete_parcel, name="parcel_delete"),
    path("create_plot", views.plot_create_view, name="plot_create"),
    path('api/cadastre/<int:z>/<int:x>/<int:y>/', views.cadastre_proxy, name='cadastre_proxy'),
    path('api/cadastre/identify/', views.cadastre_identify, name='cadastre_identify'),]