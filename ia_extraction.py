import google.generativeai as genai
import json
import os
from dotenv import load_dotenv

# Chargement de la clé API depuis le fichier .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyser_offre_pdf(pdf_bytes):
    """
    Envoie le PDF de l'offre Soleol à Gemini et extrait les données clés.
    """
    try:
        # On utilise le modèle Flash : extrêmement rapide et parfait pour l'extraction de données
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Le "Prompt" (Cahier des charges strict pour l'IA)
        prompt = """
        Tu es un expert en analyse de devis et contrats d'installations solaires photovoltaïques.
        Lis ce document PDF et extrais les informations suivantes. 
        Tu dois OBLIGATOIREMENT répondre avec un format JSON strict et valide, sans aucun autre texte.
        
        Règles d'extraction :
        - prix_total : Le prix total TTC ou le "Net à payer" par le client (sans compter les déductions fiscales ou subventions). Uniquement des chiffres. 0 si non trouvé.
        - puissance_kwp : La puissance installée des panneaux en kWc. Uniquement des chiffres. 0 si non trouvé.
        - batterie_kwh : La capacité de la batterie en kWh. Uniquement des chiffres. 0 si non trouvé.
        - materiel : Une courte phrase résumant le matériel principal (Panneaux, Onduleur, Batterie, Borne).
        
        Format de réponse attendu :
        {
            "prix_total": 25400.50,
            "puissance_kwp": 12.4,
            "batterie_kwh": 10.0,
            "materiel": "Panneaux: 30x Meyer Burger 390W, Onduleur: Fronius Symo, Batterie: BYD 10kWh"
        }
        """
        
        # Préparation du document PDF pour Gemini
        doc = {
            "mime_type": "application/pdf",
            "data": pdf_bytes
        }
        
        # Lancement de l'analyse
        response = model.generate_content([prompt, doc])
        
        # Nettoyage de la réponse pour s'assurer d'avoir un JSON propre (parfois l'IA rajoute des balises ```json)
        texte_brut = response.text.replace("```json", "").replace("```", "").strip()
        
        # Transformation du texte en véritable dictionnaire Python
        donnees = json.loads(texte_brut)
        return donnees

    except Exception as e:
        print(f"Erreur lors de l'analyse IA : {e}")
        return None