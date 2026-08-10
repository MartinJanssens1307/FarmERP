from django.urls import include, path


urlpatterns = [
    # ERP protected area
    path("", include("ERP.urls_app")),
    # Fields protected area
    path("fields/", include("Fields.urls")),
]