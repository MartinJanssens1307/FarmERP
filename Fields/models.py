from django.db import models

# Create your models here.
class CadastralParcel(models.Model):
    """
    LEVEL 1 : Cadastral parcel (juridicaly)
    """
    TENURE_CHOICES = [
        ('OWNED', 'Owned'),
        ('LEASED', 'Leased'),
        ('FREE_USE', 'Free use'),
    ]
    company = models.ForeignKey('ERP.Company', on_delete=models.CASCADE)
    capakey = models.CharField(max_length=100, blank=True, help_text="Identifiant cadastral unique (ex: BE)")
    name = models.CharField(max_length=255)
    # Surface géométrique issue du tracé manuel.
    surface = models.FloatField(null=True, blank=True)
    # Surface juridique issue de la donnée cadastrale officielle.
    official_surface = models.FloatField(null=True, blank=True)
    # Contient l'ensemble des formes : limites, point d'accès, obstacles, zones inondables...
    geojson_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}: {self.surface or 0} ha"
            