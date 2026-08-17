import google.generativeai as genai
import json
import streamlit as st

def analyser_offre_pdf(pdf_bytes):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Modèle stable
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Tu es un expert en analyse de devis solaires photovoltaïques.
        Lis ce document PDF et extrais les informations suivantes au format JSON strict.
        
        Règles d'extraction :
        - prs : Cherche le numéro du projet. Il commence par "PRS" suivi de chiffres (ex: PRS076108). S'il n'y est pas, écris "INCONNU".
        - prix_total : Prix total TTC ou Net à payer (chiffres uniquement). 0 si introuvable.
        - puissance_kwp : Puissance en kWc (chiffres uniquement). 0 si introuvable.
        - batterie_kwh : Capacité de la batterie en kWh (chiffres uniquement). 0 si introuvable.
        - materiel : Courte phrase résumant le matériel principal.
        
        Format attendu : {"prs": "PRS076108", "prix_total": 25400, "puissance_kwp": 12.4, "batterie_kwh": 10.0, "materiel": "Panneaux Meyer Burger"}
        """
        
        doc = {"mime_type": "application/pdf", "data": pdf_bytes}
        response = model.generate_content([prompt, doc])
        
        texte_brut = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texte_brut)

    except Exception as e:
        st.error(f"Erreur lors de l'analyse IA : {e}")
        return None