import google.generativeai as genai
import json
import streamlit as st

def analyser_offre_pdf(pdf_bytes):
    """
    Envoie le PDF de l'offre à l'API Google Gemini et extrait les données clés (CA, kWc, kWh, matériel).
    """
    try:
        # 1. Connexion sécurisée : On récupère la clé API depuis les paramètres de Streamlit Cloud
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 2. Choix du moteur IA : Le modèle "Flash" est optimisé pour lire les PDF instantanément
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 3. Le "Prompt" : Notre cahier des charges strict pour que l'IA ne fasse pas d'erreur
        prompt = """
        Tu es un expert en analyse de devis et contrats d'installations solaires photovoltaïques.
        Lis ce document PDF et extrais les informations suivantes. 
        Tu dois OBLIGATOIREMENT répondre avec un format JSON strict et valide, sans aucun autre texte autour.
        
        Règles d'extraction :
        - prix_total : Le prix total TTC ou le "Net à payer" par le client (sans compter les déductions fiscales ou subventions). Uniquement des chiffres. 0 si non trouvé.
        - puissance_kwp : La puissance installée des panneaux en kWc. Uniquement des chiffres. 0 si non trouvé.
        - batterie_kwh : La capacité de la batterie en kWh. Uniquement des chiffres. 0 si non trouvé.
        - materiel : Une courte phrase résumant le matériel principal (Panneaux, Onduleur, Batterie, Borne).
        
        Format de réponse attendu (exemple) :
        {
            "prix_total": 25400.50,
            "puissance_kwp": 12.4,
            "batterie_kwh": 10.0,
            "materiel": "Panneaux: 30x Meyer Burger 390W, Onduleur: Fronius Symo, Batterie: BYD 10kWh"
        }
        """
        
        # 4. Préparation du document PDF pour l'envoi
        doc = {
            "mime_type": "application/pdf",
            "data": pdf_bytes
        }
        
        # 5. Lancement de l'analyse
        response = model.generate_content([prompt, doc])
        
        # 6. Nettoyage et formatage du résultat
        # Parfois, l'IA rajoute des balises Markdown (```json ... ```), on les retire pour avoir un code pur
        texte_brut = response.text.replace("```json", "").replace("```", "").strip()
        
        # Transformation du texte en véritable dictionnaire Python compréhensible par notre application
        donnees = json.loads(texte_brut)
        return donnees

    except Exception as e:
        # En cas d'erreur (ex: clé API non valide, PDF illisible), on l'affiche proprement sur l'interface
        st.error(f"Erreur lors de l'analyse IA : {e}")
        return None