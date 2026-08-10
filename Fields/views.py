import json, requests, math 
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from .models import CadastralParcel

def parcel_list(request):
    parcels = CadastralParcel.objects.filter(company=request.tenant)
    parcel_data = []
    for parcel in parcels:
        geojson = parcel.geojson_data or {}
        features = geojson.get('features', []) if isinstance(geojson, dict) else []
        parcel_data.append({
            'id': parcel.id,
            'name': parcel.name,
            'capakey': parcel.capakey,
            'surface': parcel.surface,
            'official_surface': parcel.official_surface,
            'geojson': geojson,
            'has_features': bool(features),
        })

    context = {
        'parcels': parcels,
        'parcel_data': json.dumps(parcel_data),
    }
    return render(request, 'fields/plot_list.html', context)


def parcel_detail(request, parcel_id):
    parcel = get_object_or_404(CadastralParcel, pk=parcel_id, company=request.tenant)
    context = {'parcel': parcel}
    return render(request, 'fields/parcel_detail.html', context)


@require_http_methods(["DELETE"])
def delete_parcel(request, parcel_id):
    parcel = get_object_or_404(CadastralParcel, pk=parcel_id, company=request.tenant)
    parcel.delete()
    return HttpResponse('')


def plot_create_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        surface_ha = request.POST.get("surface_ha")
        official_surface_ha = request.POST.get("official_surface_ha")
        capakey = request.POST.get("capakey", "")
        geojson_str = request.POST.get("geojson_data")

        if name and geojson_str:
            # Conversion de la chaîne JSON reçue en dict Python
            geojson_data = json.loads(geojson_str)
            
            plot = CadastralParcel.objects.create(
                company=request.tenant,
                name=name,
                surface=float(surface_ha) if surface_ha else 0.0,
                official_surface=float(official_surface_ha) if official_surface_ha else None,
                capakey=capakey,
                geojson_data=geojson_data
            )
            
            if request.headers.get("HX-Request"):
                # Retourne un petit fragment HTML pour HTMX
                return HttpResponse(f"<li class='p-2 bg-green-50 border rounded my-1'>Parcelle <strong>{plot.name}</strong> ({plot.surface} ha) enregistrée avec succès !</li>")

    plots = CadastralParcel.objects.filter(company=request.tenant)
    return render(request, "fields/plot_create.html", {'plots': plots})

def tile_to_bbox(z, x, y):
    """Convertit les coordonnées de tuiles Leaflet {z}/{x}/{y} en Bounding Box Web Mercator EPSG:3857."""
    initial_resolution = 2 * math.pi * 6378137 / 256
    origin_shift = 2 * math.pi * 6378137 / 2.0
    res = initial_resolution / (2 ** z)
    
    xmin = x * 256 * res - origin_shift
    ymax = origin_shift - y * 256 * res
    xmax = (x + 1) * 256 * res - origin_shift
    ymin = origin_shift - (y + 1) * 256 * res
    return f"{xmin},{ymin},{xmax},{ymax}"

def cadastre_proxy(request, z, x, y):
    """Proxy vers l'API ArcGIS SPW pour servir les tuiles cadastrales wallonnes."""
    bbox = tile_to_bbox(z, x, y)
    url = "https://geoservices.wallonie.be/arcgis/rest/services/PLAN_REGLEMENT/CADMAP_PARCELLES/MapServer/export"
    
    params = {
        'bbox': bbox,
        'bboxSR': '3857',
        'imageSR': '3857',
        'size': '256,256',
        'format': 'png32',
        'transparent': 'true',
        'f': 'image'
    }
    
    try:
        response = requests.get(url, params=params, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
            return HttpResponse(response.content, content_type="image/png")
    except requests.RequestException:
        pass
        
    # Image 1x1 transparente de secours si zone vide ou indisponible
    transparent_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xafa4\x00\x00\x00\x00IEND\aeB`'
    return HttpResponse(transparent_png, content_type="image/png")

def cadastre_identify(request):
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')

    if not lat or not lng:
        return JsonResponse({'error': 'Coordonnées manquantes'}, status=400)

    try:
        lat_f = float(lat)
        lng_f = float(lng)

        # Conversion Lat/Lng -> EPSG:3857 (Web Mercator)
        x = lng_f * 20037508.34 / 180
        y = math.log(math.tan((90 + lat_f) * math.pi / 360)) / (math.pi / 180)
        y = y * 20037508.34 / 180

        url = "https://geoservices.wallonie.be/arcgis/rest/services/PLAN_REGLEMENT/CADMAP_PARCELLES/MapServer/identify"
        params = {
            'geometry': f"{x},{y}",
            'geometryType': 'esriGeometryPoint',
            'sr': '3857',
            'layers': 'all',
            'tolerance': '3',
            'mapExtent': f"{x-10},{y-10},{x+10},{y+10}",
            'imageDisplay': '256,256,96',
            'f': 'json'
        }

        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, params=params, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])

            if results:
                feature = results[0]
                attributes = feature.get('attributes', {})
                geometry = feature.get('geometry', {})

                # 1. Inspection des clés d'attributs possibles
                surface_m2 = 0.0
                possible_keys = [
                    'CAPA_AREA', 'SURFACE', 'SHAPE_Area', 'SHAPE.AREA', 
                    'SHAPE_AREA', 'AREA', 'DESCR_AREA', 'EXP_AREA'
                ]

                for key in possible_keys:
                    val = attributes.get(key)
                    if val is not None and float(val) > 0:
                        surface_m2 = float(val)
                        break

                # 2. Fallback : Si les attributs sont à 0, calcul de la surface géométrique du polygone
                if surface_m2 == 0 and 'rings' in geometry:
                    try:
                        rings = geometry['rings'][0]
                        # Formule de la lacet (Shoelace formula) sur les coordonnées EPSG:3857
                        n = len(rings)
                        area_sum = 0.0
                        for i in range(n):
                            j = (i + 1) % n
                            area_sum += rings[i][0] * rings[j][1]
                            area_sum -= rings[j][0] * rings[i][1]
                        
                        # Facteur de correction de latitude pour la projection Web Mercator
                        lat_rad = math.radians(lat_f)
                        scale_factor = math.cos(lat_rad) ** 2
                        surface_m2 = abs(area_sum) / 2.0 * scale_factor
                    except Exception as geo_err:
                        print("Erreur de calcul géométrique:", geo_err)

                capakey = attributes.get('CAPAKEY') or attributes.get('CaPaKey', 'Inconnu')
                surface_ha = round(surface_m2 / 10000.0, 4)

                return JsonResponse({
                    'capakey': capakey,
                    'surface_m2': round(surface_m2, 2),
                    'surface_ha': surface_ha
                })

        return JsonResponse({'message': 'Aucune parcelle trouvée'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)