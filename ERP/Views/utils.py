# MonProjet/ERP/utils.py
from ERP.models import Company

def get_current_company(request):
    """
    Récupère de manière sécurisée et performante l'entreprise active.
    Utilise la session pour éviter de requêter la DB à chaque clic htmx.
    """
    if not request.user.is_authenticated:
        return None

    # 1. On regarde si l'ID est déjà en session
    company_id = request.session.get('current_company_id')
    
    if company_id:
        # On valide l'accès en utilisant ton style d'origine (très propre)
        has_access = request.user.company_permissions.filter(company_id=company_id).exists()
        if has_access:
            try:
                return Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                pass
        else:
            # Sécurité : l'accès n'existe plus, on nettoie
            del request.session['current_company_id']

    # 2. Si pas en session (première connexion), on prend sa première entreprise
    access = request.user.company_permissions.first()
    if access:
        # On sauvegarde l'ID en session pour les prochains clics
        request.session['current_company_id'] = access.company.id
        return access.company

    return None

def set_current_company(request, company_id):
    """Permet de basculer d'une entreprise à l'autre (ex: pour le comptable)"""
    if request.user.is_authenticated:
        # Sécurité : On vérifie que l'utilisateur a bien le droit d'accéder à cette entreprise
        has_access = request.user.company_permissions.filter(company_id=company_id).exists()
        if has_access:
            request.session['current_company_id'] = company_id
            return True
    return False