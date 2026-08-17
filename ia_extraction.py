import google.generativeai as genai
import json
import streamlit as st

def analyser_offre_pdf(pdf_bytes):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # CHANGEMENT ICI : On utilise la version "latest" pour éviter l'erreur 404
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        prompt = """
        Tu es un expert en analyse de devis solaires photovoltaïques.
        Lis ce document PDF et extrais les informations suivantes au format JSON strict (sans texte autour).
        
        Règles d'extraction :
        - prix_total : Prix total TTC ou Net à payer (chiffres uniquement). 0 si introuvable.
        - puissance_kwp : Puissance en kWc (chiffres uniquement). 0 si introuvable.
        - batterie_kwh : Capacité de la batterie en kWh (chiffres uniquement). 0 si introuvable.
        - materiel : Courte phrase résumant le matériel (Panneaux, Onduleur, Batterie).
        
        Exemple : {"prix_total": 25400.50, "puissance_kwp": 12.4, "batterie_kwh": 10.0, "materiel": "30x Meyer Burger 390W, Fronius Symo"}
        """
        
        doc = {"mime_type": "application/pdf", "data": pdf_bytes}
        response = model.generate_content([prompt, doc])
        texte_brut = response.text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(texte_brut)

    except Exception as e:
        st.error(f"Erreur technique IA : {e}")
        return None