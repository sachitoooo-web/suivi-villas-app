import streamlit as st
from supabase import create_client, Client
from streamlit_calendar import calendar
import datetime
import pandas as pd
from ia_extraction import analyser_offre_pdf
from ingestion import scanner_planning_excel

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
# BARRE LATÉRALE : INGESTION (EXCEL & PDF)
# ==========================================
with st.sidebar:
    
    # --- ZONE 1 : INGESTION DU PLANNING EXCEL ---
    st.header("📅 Synchro Planning")
    st.write("Glisse le grand fichier Excel de planification ici.")
    
    excel_upload = st.file_uploader("Fichier Excel (.xlsx)", type=["xlsx"])
    
    if excel_upload is not None:
        if st.button("Mettre à jour depuis l'Excel"):
            with st.spinner("Lecture des couleurs et des dates..."):
                nouveaux_projets = scanner_planning_excel(excel_upload)
                
                if nouveaux_projets:
                    projets_ajoutes = 0
                    
                    # Enregistrement des projets dans Supabase avec sécurité Anti-Crash
                    for p in nouveaux_projets:
                        try:
                            existant = supabase.table("solar_projects").select("id").eq("project_name", p["nom"]).execute()
                            
                            # Si le projet n'existe pas encore, on le crée
                            if not existant.data:
                                nouveau_projet_db = {
                                    "project_name": p["nom"],
                                    "client_name": p["prs"], # On stocke temporairement le code PRS ici
                                    "start_date": p["date_debut"],
                                    "cdp": p["cdp"]
                                }
                                supabase.table("solar_projects").insert(nouveau_projet_db).execute()
                                projets_ajoutes += 1
                                
                        except Exception as e:
                            # Streamlit va afficher la VRAIE erreur Supabase ici, sans planter
                            st.error(f"Erreur d'insertion pour le projet {p['prs']} : {e}")
                            
                    if projets_ajoutes > 0:
                        st.success(f"{projets_ajoutes} nouveaux chantiers ajoutés au système !")
                        st.rerun()
                    else:
                        st.info("Mise à jour terminée. Aucun nouveau projet à ajouter (ils y sont déjà tous).")
                else:
                    st.warning("Aucun projet vert trouvé avec un code PRS.")

    st.divider()

    # --- ZONE 2 : EXTRACTION IA DES OFFRES ---
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
                    nouveau_projet = {
                        "project_name": "Nouveau Projet (à renommer)",
                        "client_name": "Client IA",
                        "total_price": donnees.get("prix_total", 0),
                        "power_kwp": donnees.get("puissance_kwp", 0),
                        "battery_kwh": donnees.get("batterie_kwh", 0),
                        "equipment_list": donnees.get("materiel", ""),
                        "is_signed": True,
                        "cdp": "Sacha", # Par défaut
                        "start_date": (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
                    }
                    supabase.table("solar_projects").insert(nouveau_projet).execute()
                    st.toast("🚀 Projet ajouté au système !")
                    st.rerun()
                else:
                    st.error("Erreur d'extraction IA.")

# ==========================================
# INTERFACE PRINCIPALE : LES ONGLETS
# ==========================================
st.title("🏗️ Pilotage des Chantiers Soleol")

projets = get_projects()

onglet_planning, onglet_calendrier = st.tabs(["📋 Planning (Vue Excel Colorée)", "📅 Vue Calendrier"])

# --- ONGLET 1 : LE PLANNING COLORÉ ---
with onglet_planning:
    st.write("### Liste et Statut des Projets")
    
    if projets:
        df = pd.DataFrame(projets)
        
        # Sélection des colonnes pertinentes pour la vue globale
        cols = [
            "project_name", "cdp", "start_date", "total_price", "power_kwp",
            "is_signed", "is_cost_file_done", "is_permit_done",
            "is_drt_done", "is_sp_done", "is_cp_done", "is_project_finished"
        ]
        
        df_visuel = df[[c for c in cols if c in df.columns]]
        
        # Fonction pour appliquer les couleurs (Vert = Sacha, Gris/Barré = Terminé)
        def appliquer_couleurs(row):
            background = [''] * len(row)
            if 'cdp' in row and row['cdp'] == 'Sacha':
                background = ['background-color: #d4edda; color: #155724'] * len(row)
            if 'is_project_finished' in row and row['is_project_finished'] == True:
                background = ['background-color: #e2e3e5; color: #383d41; text-decoration: line-through'] * len(row)
            return background

        df_colore = df_visuel.style.apply(appliquer_couleurs, axis=1)
        st.dataframe(df_colore, use_container_width=True, hide_index=True)
        
    else:
        st.info("Aucun projet enregistré dans la base de données.")

# --- ONGLET 2 : LE CALENDRIER INTERACTIF ---
with onglet_calendrier:
    events = []
    for p in projets:
        if p.get("start_date"):
            # Les projets terminés passent en vert foncé dans le calendrier
            couleur = "#28a745" if p.get("is_project_finished") else "#007bff"
            events.append({
                "title": p["project_name"],
                "start": p["start_date"],
                "id": str(p["id"]),
                "color": couleur
            })

    calendar_options = {
        "headerToolbar": {"left": "today prev,next", "center": "title", "right": "dayGridMonth,timeGridWeek"},
        "initialView": "dayGridMonth",
        "selectable": True,
    }

    cal_state = calendar(events=events, options=calendar_options, custom_css=".fc-event { cursor: pointer; } .fc-toolbar-title { font-weight: 600; }")

# ==========================================
# VUE DE DÉTAIL (QUAND ON CLIQUE SUR LE CALENDRIER)
# ==========================================
st.divider()

if cal_state.get("eventClick"):
    clicked_id = int(cal_state["eventClick"]["event"]["id"])
    projet_actuel = next((p for p in projets if p["id"] == clicked_id), None)
    
    if projet_actuel:
        st.subheader(f"🛠️ Suivi du projet : {projet_actuel['project_name']}")
        
        # --- BLOC 1 : DONNÉES IA ---
        st.write("### 📊 Données Techniques & Financières")
        col1, col2, col3 = st.columns(3)
        col1.metric("Prix Total TTC", f"{projet_actuel.get('total_price', 0)} CHF")
        col2.metric("Puissance PV", f"{projet_actuel.get('power_kwp', 0)} kWc")
        col3.metric("Batterie", f"{projet_actuel.get('battery_kwh', 0)} kWh")
        st.info(f"**Matériel :** {projet_actuel.get('equipment_list', '')}")
        
        # --- BLOC 2 : CHECKLIST OPÉRATIONNELLE ---
        st.write("### ✅ Checklist de préparation")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.write("**Administratif**")
            st.checkbox("Projet signé (PDF)", value=bool(projet_actuel.get('is_signed', False)), 
                        on_change=update_checkbox, args=(clicked_id, "is_signed", not projet_actuel.get('is_signed', False)), key=f"signed_{clicked_id}")
            st.checkbox("Fichier coûts", value=bool(projet_actuel.get('is_cost_file_done', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_cost_file_done", not projet_actuel.get('is_cost_file_done', False)), key=f"cost_{clicked_id}")
            st.checkbox("Mise à l'enquête", value=bool(projet_actuel.get('is_permit_done', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_permit_done", not projet_actuel.get('is_permit_done', False)), key=f"permit_{clicked_id}")
            st.checkbox("Dronage", value=bool(projet_actuel.get('is_drone_done', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_drone_done", not projet_actuel.get('is_drone_done', False)), key=f"drone_{clicked_id}")
            
        with c2:
            st.write("**Technique & Logistique**")
            st.checkbox("DRT (Dossier Technique)", value=bool(projet_actuel.get('is_drt_done', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_drt_done", not projet_actuel.get('is_drt_done', False)), key=f"drt_{clicked_id}")
            st.checkbox("Liste du matériel", value=bool(projet_actuel.get('is_material_list_done', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_material_list_done", not projet_actuel.get('is_material_list_done', False)), key=f"matlist_{clicked_id}")
            
            # Affichage conditionnel
            if projet_actuel.get('power_kwp', 0) > 0:
                st.checkbox("Dossier monteur (Général)", value=bool(projet_actuel.get('is_general_monteur_done', False)),
                            on_change=update_checkbox, args=(clicked_id, "is_general_monteur_done", not projet_actuel.get('is_general_monteur_done', False)), key=f"montgen_{clicked_id}")
                
            st.checkbox("Dossier électro", value=bool(projet_actuel.get('is_electro_monteur_done', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_electro_monteur_done", not projet_actuel.get('is_electro_monteur_done', False)), key=f"elec_{clicked_id}")

        with c3:
            st.write("**Validation**")
            st.checkbox("SP (Sur SharePoint)", value=bool(projet_actuel.get('is_sp_done', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_sp_done", not projet_actuel.get('is_sp_done', False)), key=f"sp_{clicked_id}")
            st.checkbox("CP (Prêt pour monteurs)", value=bool(projet_actuel.get('is_cp_done', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_cp_done", not projet_actuel.get('is_cp_done', False)), key=f"cp_{clicked_id}")
            st.divider()
            st.checkbox("🏁 Fin de projet", value=bool(projet_actuel.get('is_project_finished', False)),
                        on_change=update_checkbox, args=(clicked_id, "is_project_finished", not projet_actuel.get('is_project_finished', False)), key=f"fin_{clicked_id}")
else:
    st.info("👆 Clique sur un projet dans le calendrier pour afficher sa checklist de suivi.")