import os
import base64
import requests

def get_ibanity_oauth_token():
    """Récupère le jeton d'accès OAuth2 auprès d'Ibanity Flowin"""
    token_url = "https://api.ibanity.com/einvoicing/oauth2/token"
    cert_path = os.getenv("IBANITY_CERT_PATH")
    
    client_id = os.getenv("IBANITY_CLIENT_ID")
    client_secret = os.getenv("IBANITY_CLIENT_SECRET")
    
    # Encodage requis : client_id:client_secret en Base64
    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    base64_credentials = base64.b64encode(credentials).decode("utf-8")
    
    headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/vnd.api+json"
    }
    
    payload = {
        "grant_type": "client_credentials"
    }
    
    response = requests.post(token_url, headers=headers, data=payload, cert=cert_path)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception(f"Impossible d'obtenir le token OAuth2: {response.status_code} - {response.text}")


def check_peppol_customer(customer_reference="9925:BE0010012671"):
    """Vérifie l'existence d'un client sur le réseau Peppol via Flowin"""
    try:
        # 1. Étape OAuth2
        access_token = get_ibanity_oauth_token()
        
        # 2. Requête de recherche
        url = "https://api.ibanity.com/einvoicing/peppol/customer-searches"
        cert_path = os.getenv("IBANITY_CERT_PATH")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json"
        }
        
        payload = {
            "data": {
                "type": "customerSearch",
                "attributes": {
                    "customerReference": customer_reference
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, cert=cert_path)
        
        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Erreur Ibanity ({response.status_code}): {response.text}"}
            
    except Exception as e:
        return {"success": False, "error": f"Erreur de connexion : {str(e)}"}