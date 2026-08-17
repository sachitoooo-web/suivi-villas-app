import streamlit as st
from supabase import create_client, Client
from streamlit_calendar import calendar
import datetime
import pandas as pd
from ia_extraction import analyser_offre_pdf
from ingestion import scanner_planning_excel

# --- CONFIGURATION ---
st.set_page_config(page_title="Soleol - Pilotage Projets", layout="wide", initial_sidebar_state="expanded")

@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

def get_projects():
    return supabase.table("solar_projects").select("*").execute().data

def update_checkbox(project_id, column_name, new_value):
    supabase.table("solar_projects").update({column_name: new_value}).eq("id", project_id).execute()
    st.toast("✅ Mise à jour enregistrée")

# ==========================================
# BARRE LATÉRALE
# ==========================================
with st.sidebar:
    st.header("📅 Synchro Excel")
    st.write("Glisse ton fichier PLANNING (2).xlsx")
    
    excel_upload = st.file_uploader("Fichier Excel", type=["xlsx"])
    if excel_upload is not None:
        if st.button("Mettre à jour via Excel"):
            with st.spinner("Analyse du planning..."):
                nouveaux_projets = scanner_planning_excel(excel_upload)
                if nouveaux_projets:
                    projets_ajoutes = 0
                    for p in nouveaux_projets:
                        try:
                            # On vérifie par le code PRS (stocké dans client_name)
                            existant = supabase.table("solar_projects").select("id").eq("client_name", p["prs"]).execute()
                            if not existant.data:
                                nouveau_projet_db = {
                                    "project_name": p["nom"],
                                    "client_name": p["prs"],
                                    "start_date": p["date_debut"],
                                    "cdp": p["cdp"]
                                }
                                supabase.table("solar_projects").insert(nouveau_projet_db).execute()
                                projets_ajoutes += 1
                        except Exception as e:
                            st.error(f"Erreur base de données pour {p['prs']} : {e}")
                            
                    st.success(f"Terminé ! {projets_ajoutes} nouveaux chantiers ajoutés.")
                    st.rerun()
                else:
                    st.warning("Aucun projet Sacha trouvé à partir du 01/08/2026.")

    st.divider()

    st.header("🤖 Contrat PDF")
    st.write("Glisse le devis pour fusionner les données")
    fichier_upload = st.file_uploader("PDF du contrat", type=["pdf"])
    if fichier_upload is not None:
        if st.button("Lancer l'extraction IA"):
            with st.spinner("Lecture du devis..."):
                donnees = analyser_offre_pdf(fichier_upload.getvalue())
                
                if donnees:
                    prs_extrait = donnees.get("prs", "INCONNU")
                    if prs_extrait != "INCONNU":
                        update_data = {
                            "total_price": donnees.get("prix_total", 0),
                            "power_kwp": donnees.get("puissance_kwp", 0),
                            "battery_kwh": donnees.get("batterie_kwh", 0),
                            "equipment_list": donnees.get("materiel", ""),
                            "is_signed": True
                        }
                        # L'IA met à jour la ligne Excel existante !
                        supabase.table("solar_projects").update(update_data).eq("client_name", prs_extrait).execute()
                        st.success(f"✅ Devis lié au projet {prs_extrait} !")
                    else:
                        st.error("Impossible de lier ce devis : le code PRS est introuvable sur le document.")
                    st.rerun()

# ==========================================
# INTERFACE PRINCIPALE
# ==========================================
st.title("🏗️ Pilotage des Chantiers")
projets = get_projects()

onglet_liste, onglet_calendrier = st.tabs(["📋 Liste des Projets", "📅 Vue Calendrier"])

with onglet_liste:
    if projets:
        df = pd.DataFrame(projets)
        cols = ["client_name", "project_name", "start_date", "total_price", "power_kwp", "is_signed", "is_project_finished"]
        df_visuel = df[[c for c in cols if c in df.columns]]
        st.dataframe(df_visuel, use_container_width=True, hide_index=True)
    else:
        st.info("Aucun projet enregistré.")

with onglet_calendrier:
    events = []
    for p in projets:
        if p.get("start_date"):
            events.append({
                "title": f"{p.get('client_name', '')} - {p.get('project_name', '')[:20]}",
                "start": p["start_date"],
                "id": str(p["id"]),
                "color": "#28a745" if p.get("is_project_finished") else "#007bff"
            })
    
    cal_state = calendar(events=events, options={"headerToolbar": {"left": "today prev,next", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "selectable": True})

st.divider()

if cal_state.get("eventClick"):
    clicked_id = int(cal_state["eventClick"]["event"]["id"])
    projet_actuel = next((p for p in projets if p["id"] == clicked_id), None)
    
    if projet_actuel:
        st.subheader(f"🛠️ {projet_actuel['project_name']}")
        
        # Données IA
        col1, col2, col3 = st.columns(3)
        col1.metric("Prix Total TTC", f"{projet_actuel.get('total_price') or 0} CHF")
        col2.metric("Puissance PV", f"{projet_actuel.get('power_kwp') or 0} kWc")
        col3.metric("Batterie", f"{projet_actuel.get('battery_kwh') or 0} kWh")
        st.info(f"**Matériel :** {projet_actuel.get('equipment_list', 'Non renseigné')}")
        
        # Checklists Conditionnelles
        is_pv = float(projet_actuel.get('power_kwp') or 0) > 0 or 'batterie' not in str(projet_actuel.get('project_name', '')).lower()
        
        st.write("### ✅ Checklist")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.checkbox("Projet signé", value=bool(projet_actuel.get('is_signed', False)), on_change=update_checkbox, args=(clicked_id, "is_signed", not projet_actuel.get('is_signed', False)), key=f"s_{clicked_id}")
            st.checkbox("Fichier coûts", value=bool(projet_actuel.get('is_cost_file_done', False)), on_change=update_checkbox, args=(clicked_id, "is_cost_file_done", not projet_actuel.get('is_cost_file_done', False)), key=f"c_{clicked_id}")
            if is_pv:
                st.checkbox("Dronage", value=bool(projet_actuel.get('is_drone_done', False)), on_change=update_checkbox, args=(clicked_id, "is_drone_done", not projet_actuel.get('is_drone_done', False)), key=f"dron_{clicked_id}")
        with c2:
            st.checkbox("DRT", value=bool(projet_actuel.get('is_drt_done', False)), on_change=update_checkbox, args=(clicked_id, "is_drt_done", not projet_actuel.get('is_drt_done', False)), key=f"d_{clicked_id}")
            st.checkbox("Dossier électro", value=bool(projet_actuel.get('is_electro_monteur_done', False)), on_change=update_checkbox, args=(clicked_id, "is_electro_monteur_done", not projet_actuel.get('is_electro_monteur_done', False)), key=f"e_{clicked_id}")
            if is_pv:
                st.checkbox("Dossier monteur général", value=bool(projet_actuel.get('is_general_monteur_done', False)), on_change=update_checkbox, args=(clicked_id, "is_general_monteur_done", not projet_actuel.get('is_general_monteur_done', False)), key=f"m_{clicked_id}")
        with c3:
            st.checkbox("SP", value=bool(projet_actuel.get('is_sp_done', False)), on_change=update_checkbox, args=(clicked_id, "is_sp_done", not projet_actuel.get('is_sp_done', False)), key=f"sp_{clicked_id}")
            st.checkbox("CP", value=bool(projet_actuel.get('is_cp_done', False)), on_change=update_checkbox, args=(clicked_id, "is_cp_done", not projet_actuel.get('is_cp_done', False)), key=f"cp_{clicked_id}")
            st.checkbox("🏁 Fin de projet", value=bool(projet_actuel.get('is_project_finished', False)), on_change=update_checkbox, args=(clicked_id, "is_project_finished", not projet_actuel.get('is_project_finished', False)), key=f"fin_{clicked_id}")