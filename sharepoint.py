import os
import requests
import msal

# 1. Fonction pour s'authentifier auprès de Microsoft
def obtenir_token_microsoft():
    # Ces mots de passe secrets seront configurés à l'étape 6 dans Streamlit !
    client_id = os.environ.get("MS_CLIENT_ID")
    client_secret = os.environ.get("MS_CLIENT_SECRET")
    tenant_id = os.environ.get("MS_TENANT_ID")
    
    if not client_id or not client_secret or not tenant_id:
        return None

    # On prépare le "badge" pour Microsoft
    autorite = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id, authority=autorite, client_credential=client_secret
    )
    
    # On demande la permission d'accéder à Microsoft Graph (SharePoint)
    resultat = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    
    if "access_token" in resultat:
        return resultat["access_token"]
    else:
        print("Erreur de connexion à Microsoft :", resultat.get("error"))
        return None

# 2. Fonction pour chercher un document précis dans un dossier projet
def verifier_presence_document(token_microsoft, site_id, nom_projet, mot_cle_document):
    if not token_microsoft:
        return False
        
    # On prépare la requête pour interroger SharePoint
    headers = {
        "Authorization": f"Bearer {token_microsoft}",
        "Accept": "application/json"
    }
    
    # On fait une recherche : "Trouve-moi le fichier contenant ce mot-clé dans le dossier de ce projet"
    # (L'URL exacte dépendra de l'organisation de ton SharePoint, on met la base ici)
    url_recherche = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root/search(q='{mot_cle_document}')"
    
    reponse = requests.get(url_recherche, headers=headers)
    
    if reponse.status_code == 200:
        fichiers_trouves = reponse.json().get("value", [])
        
        # On vérifie si un des fichiers trouvés appartient bien au dossier du projet
        for fichier in fichiers_trouves:
            # Si le chemin du fichier contient le nom du projet (ex: "Joye Michel")
            if nom_projet.upper() in str(fichier.get("parentReference", {}).get("path")).upper():
                return True # On a trouvé le document, tâche validée !
                
    return False # Document non trouvé