# ERP/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from .Views.utils import get_current_company

class TenantSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Zone métier protégée: tout ce qui est sous /app/.
        if not request.path.startswith('/app/'):
            request.tenant = None
            return self.get_response(request)

        # ---- ZONE SÉCURISÉE (/app/...) ----

        # 1. L'utilisateur doit être connecté
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        # 2. L'utilisateur doit avoir une entreprise active
        current_tenant = get_current_company(request)
        if not current_tenant:
            # Connecté mais pas de entreprise ? Redirection forcée vers l'index global
            return redirect('company_data')

        # 3. Tout est OK, on injecte le tenant dans la requête pour les vues
        request.tenant = current_tenant

        return self.get_response(request)