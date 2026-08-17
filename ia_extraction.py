import google.generativeai as genai
import json
import streamlit as st

def analyser_offre_pdf(pdf_bytes):
    """
    Envoie le PDF de l'offre à l'API Google Gemini et extraira les données, dont le PRS.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # On utilise le modèle le plus récent pour éviter les erreurs 404
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = """
        Tu es un expert en analyse de devis et contrats d'installations solaires photovoltaïques.
        Lis ce document PDF et extrais les informations suivantes. 
        Tu dois OBLIGATOIREMENT répondre avec un format JSON strict et valide, sans aucun autre texte autour.
        
        Règles d'extraction :
        - prs : Cherche le numéro du projet. Il commence par "PRS" suivi de chiffres (ex: PRS076108). S'il n'y est pas, écris "INCONNU".
        - prix_total : Le prix total TTC ou le "Net à payer" par le client (chiffres uniquement). 0 si non trouvé.
        - puissance_kwp : La puissance installée des panneaux en kWc (chiffres uniquement). 0 si non trouvé.
        - batterie_kwh : La capacité de la batterie en kWh (chiffres uniquement). 0 si non trouvé.
        - materiel : Une courte phrase résumant le matériel principal (Panneaux, Onduleur, Batterie).
        
        Format de réponse attendu :
        {
            "prs": "PRS076108",
            "prix_total": 25400.50,
            "puissance_kwp": 12.4,
            "batterie_kwh": 10.0,
            "materiel": "Panneaux: 30x Meyer Burger 390W, Onduleur: Fronius Symo, Batterie: BYD 10kWh"
        }
        """
        
        doc = {"mime_type": "application/pdf", "data": pdf_bytes}
        response = model.generate_content([prompt, doc])
        
        texte_brut = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texte_brut)

    except Exception as e:
        st.error(f"Erreur lors de l'analyse IA : {e}")
        return None