from django.test import RequestFactory, TestCase
from django.urls import reverse

from ERP.models import Company
from Fields.models import CadastralParcel
from Fields.views import delete_parcel, parcel_detail, parcel_list, plot_create_view


class ParcelDetailViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.company = Company.objects.create(name="Test Company")
        self.parcel = CadastralParcel.objects.create(
            company=self.company,
            name="Test Parcel",
            geojson_data={"type": "FeatureCollection", "features": []},
        )

    def test_detail_view_renders_parcel_information(self):
        request = self.factory.get(f"/app/fields/parcels/{self.parcel.pk}/")
        request.tenant = self.company

        response = parcel_detail(request, parcel_id=self.parcel.pk)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.parcel.name)
        self.assertContains(response, "GeoJSON")
        self.assertContains(response, "Preview on map")
        self.assertContains(response, "fa-solid")

    def test_delete_view_removes_parcel(self):
        request = self.factory.delete(f"/app/fields/parcels/{self.parcel.pk}/delete/")
        request.tenant = self.company

        response = delete_parcel(request, parcel_id=self.parcel.pk)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(CadastralParcel.objects.filter(pk=self.parcel.pk).exists())

    def test_parcel_list_page_renders_map_view(self):
        request = self.factory.get(reverse("parcels"))
        request.tenant = self.company

        response = parcel_list(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "parcels-map")
        self.assertContains(response, self.parcel.name)

    def test_create_view_renders_create_form(self):
        request = self.factory.get(reverse("plot_create"))
        request.tenant = self.company

        response = plot_create_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Create Parcel")
        self.assertContains(response, "id=\"map\"")
