import streamlit as st
from supabase import create_client, Client
from streamlit_calendar import calendar
import datetime
from ia_extraction import analyser_offre_pdf
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Soleol - Pilotage Projets", layout="wide", initial_sidebar_state="expanded")

# --- CONNEXION SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- CHARGEMENT DES DONNÉES ---
def get_projects():
    response = supabase.table("solar_projects").select("*").execute()
    return response.data

# --- MISE À JOUR D'UNE CASE À COCHER ---
def update_checkbox(project_id, column_name, new_value):
    supabase.table("solar_projects").update({column_name: new_value}).eq("id", project_id).execute()
    st.toast("✅ Mise à jour enregistrée")

# ==========================================
# BARRE LATÉRALE : CRÉATION DE PROJET VIA IA
# ==========================================
with st.sidebar:
    st.header("🤖 Nouvelle Offre Signée")
    st.write("Glisse le PDF pour extraire les données")
    
    fichier_upload = st.file_uploader("PDF du contrat", type=["pdf"])
    
    if fichier_upload is not None:
        if st.button("Lancer l'extraction IA"):
            with st.spinner("Analyse du contrat en cours..."):
                pdf_bytes = fichier_upload.getvalue()
                donnees = analyser_offre_pdf(pdf_bytes)
                
                if donnees:
                    st.success("Données extraites ! Création du projet...")
                    
                    # On crée le projet avec les données IA + la case "Projet signé" cochée
                    nouveau_projet = {
                        "project_name": "Nouveau Projet (à renommer)",
                        "client_name": "Client IA",
                        "total_price": donnees.get("prix_total", 0),
                        "power_kwp": donnees.get("puissance_kwp", 0),
                        "battery_kwh": donnees.get("batterie_kwh", 0),
                        "equipment_list": donnees.get("materiel", ""),
                        "is_signed": True,
                        # On met une date de début par défaut à demain pour le voir sur le calendrier
                        "start_date": (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
                    }
                    supabase.table("solar_projects").insert(nouveau_projet).execute()
                    st.toast("🚀 Projet ajouté au système !")
                    st.rerun()
                else:
                    st.error("Erreur d'extraction IA.")

# ==========================================
# INTERFACE PRINCIPALE : LE PLANNING (CALENDRIER)
# ==========================================
st.title("📅 Planning Général des Chantiers")

# Récupération de tous les projets
projets = get_projects()

# Préparation des événements pour le calendrier
events = []
for p in projets:
    if p.get("start_date"):
        # On définit la couleur selon l'état du projet
        couleur = "#28a745" if p.get("is_project_finished") else "#007bff"
        events.append({
            "title": p["project_name"],
            "start": p["start_date"],
            "id": str(p["id"]),
            "color": couleur
        })

# Options d'affichage du calendrier
calendar_options = {
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek"
    },
    "initialView": "dayGridMonth",
    "selectable": True,
}

# Affichage du composant Calendrier
cal_state = calendar(events=events, options=calendar_options, custom_css="""
    .fc-event { cursor: pointer; }
    .fc-toolbar-title { font-weight: 600; }
""")

# ==========================================
# VUE DE DÉTAIL (QUAND ON CLIQUE SUR UN PROJET)
# ==========================================
st.divider()

if cal_state.get("eventClick"):
    # On récupère l'ID du projet cliqué dans le calendrier
    clicked_id = int(cal_state["eventClick"]["event"]["id"])
    
    # On cherche les infos complètes de ce projet
    projet_actuel = next((p for p in projets if p["id"] == clicked_id), None)
    
    if projet_actuel:
        st.subheader(f"🛠️ Suivi du projet : {projet_actuel['project_name']}")
        
        # --- BLOC 1 : DONNÉES IA (Finance & Tech) ---
        st.write("### 📊 Données Techniques & Financières (Extraites par l'IA)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Prix Total TTC", f"{projet_actuel['total_price']} CHF")
        col2.metric("Puissance PV", f"{projet_actuel['power_kwp']} kWc")
        col3.metric("Batterie", f"{projet_actuel['battery_kwh']} kWh")
        st.info(f"**Matériel :** {projet_actuel['equipment_list']}")
        
        # --- BLOC 2 : CHECKLIST OPÉRATIONNELLE ---
        st.write("### ✅ Checklist de préparation")
        
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.write("**Administratif**")
            # Astuce Streamlit : le "on_change" permet de mettre à jour Supabase direct quand on coche !
            st.checkbox("Projet signé (PDF)", value=projet_actuel['is_signed'], 
                        on_change=update_checkbox, args=(clicked_id, "is_signed", not projet_actuel['is_signed']))
            st.checkbox("Fichier coûts", value=projet_actuel['is_cost_file_done'],
                        on_change=update_checkbox, args=(clicked_id, "is_cost_file_done", not projet_actuel['is_cost_file_done']))
            st.checkbox("Mise à l'enquête", value=projet_actuel['is_permit_done'],
                        on_change=update_checkbox, args=(clicked_id, "is_permit_done", not projet_actuel['is_permit_done']))
            st.checkbox("Dronage", value=projet_actuel['is_drone_done'],
                        on_change=update_checkbox, args=(clicked_id, "is_drone_done", not projet_actuel['is_drone_done']))
            
        with c2:
            st.write("**Technique & Logistique**")
            st.checkbox("DRT (Dossier Technique)", value=projet_actuel['is_drt_done'],
                        on_change=update_checkbox, args=(clicked_id, "is_drt_done", not projet_actuel['is_drt_done']))
            st.checkbox("Liste du matériel", value=projet_actuel['is_material_list_done'],
                        on_change=update_checkbox, args=(clicked_id, "is_material_list_done", not projet_actuel['is_material_list_done']))
            # On n'affiche le dossier monteur général que s'il y a des panneaux (règle métier)
            if projet_actuel['power_kwp'] > 0:
                st.checkbox("Dossier monteur (Général)", value=projet_actuel['is_general_monteur_done'],
                            on_change=update_checkbox, args=(clicked_id, "is_general_monteur_done", not projet_actuel['is_general_monteur_done']))
            st.checkbox("Dossier électro", value=projet_actuel['is_electro_monteur_done'],
                        on_change=update_checkbox, args=(clicked_id, "is_electro_monteur_done", not projet_actuel['is_electro_monteur_done']))

        with c3:
            st.write("**Validation**")
            st.checkbox("SP (Sur SharePoint)", value=projet_actuel['is_sp_done'],
                        on_change=update_checkbox, args=(clicked_id, "is_sp_done", not projet_actuel['is_sp_done']))
            st.checkbox("CP (Prêt pour monteurs)", value=projet_actuel['is_cp_done'],
                        on_change=update_checkbox, args=(clicked_id, "is_cp_done", not projet_actuel['is_cp_done']))
            st.divider()
            st.checkbox("🏁 Fin de projet (Remise ouvrage)", value=projet_actuel['is_project_finished'],
                        on_change=update_checkbox, args=(clicked_id, "is_project_finished", not projet_actuel['is_project_finished']))

else:
    st.info("👆 Clique sur un projet dans le calendrier pour afficher sa checklist de suivi.")