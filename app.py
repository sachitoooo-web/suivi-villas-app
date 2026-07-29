import streamlit as st
import json
from supabase import create_client, Client
from ingestion import lire_excel_calendrier
from datetime import datetime, timedelta

# Configuration de la page (Design épuré, mode large)
st.set_page_config(
    page_title="Suivi Projets Villas", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés pour un rendu propre et moderne
st.markdown("""
    <style>
    .main { background-color: #fafafa; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: 600; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

# 1. Connexion Supabase
@st.cache_resource
def initialiser_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = initialiser_supabase()

# 2. Chargement Configuration JSON
@st.cache_data
def charger_config_checklists():
    with open("checklists_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

config = charger_config_checklists()

# En-tête principal élégant
st.title("⚡ Pilotage des Chantiers Villas")
st.markdown("Suivi centralisé des installations photovoltaïques et batteries.")
st.markdown("---")

onglet_suivi, onglet_maj = st.tabs(["📊 Suivi & Pilotage Projets", "📥 Synchronisation Excel"])

# ==========================================
# ONGLET 1 : PILOTAGE & DESIGN ÉPURÉ
# ==========================================
with onglet_suivi:
    reponse_db = supabase.table("projects").select("*").execute()
    projets_enregistres = reponse_db.data
    
    if len(projets_enregistres) > 0:
        # Barre de sélection / recherche fluide
        liste_noms = [p["project_name"] for p in projets_enregistres]
        
        col_search, col_space = st.columns([2, 1])
        with col_search:
            projet_choisi = st.selectbox("🔍 Rechercher un chantier :", liste_noms)
        
        # Infos du projet sélectionné
        infos_projet = next(p for p in projets_enregistres if p["project_name"] == projet_choisi)
        projet_id = infos_projet["id"]
        type_du_projet = infos_projet["project_type"]
        date_debut_str = infos_projet.get("start_date")
        
        # Carte d'identité du projet (Design en colonnes claires)
        st.markdown("")
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            c1.metric(label="Type d'installation", value=type_du_projet)
            
            date_debut_obj = None
            if date_debut_str:
                date_debut_obj = datetime.strptime(date_debut_str, "%Y-%m-%d")
                c2.metric(label="Date de Chantier / Début", value=date_debut_obj.strftime('%d/%m/%Y'))
            else:
                c2.metric(label="Date de Chantier / Début", value="Non définie")
                
            # Récupération des tâches pour calcul de progression
            reponse_tasks = supabase.table("tasks").select("*").eq("project_id", projet_id).execute()
            taches_db = {t["task_name"]: t for t in reponse_tasks.data}
            
            # Compteur de progression
            total_applicables = 0
            validees = 0
            for phase_nom, liste_taches in config.items():
                for tache_config in liste_taches:
                    if type_du_projet in tache_config["types_projets"]:
                        total_applicables += 1
                        nom_t = tache_config["tache"]
                        if nom_t in taches_db and taches_db[nom_t].get("status") == "VALIDE":
                            validees += 1
                            
            progression = int((validees / total_applicables) * 100) if total_applicables > 0 else 0
            c3.metric(label="Progression globale", value=f"{progression}%")
            st.progress(progression / 100)

        st.markdown("### 📋 Chemin Critique & Jalons")
        
        # Affichage en 2 colonnes ergonomiques pour les 5 phases
        col_gauche, col_droite = st.columns(2)
        colonnes_repartition = [col_gauche, col_gauche, col_gauche, col_droite, col_droite]
        
        for idx, (phase_nom, liste_taches) in enumerate(config.items()):
            with colonnes_repartition[idx]:
                with st.container(border=True):
                    st.markdown(f"**📌 {phase_nom.replace('_', ' ').upper()}**")
                    st.markdown("")
                    
                    for tache_config in liste_taches:
                        nom_t = tache_config["tache"]
                        
                        if type_du_projet in tache_config["types_projets"]:
                            if nom_t not in taches_db:
                                nouveau = {"project_id": projet_id, "task_name": nom_t, "status": "EN_ATTENTE", "phase": int(phase_nom[0])}
                                supabase.table("tasks").insert(nouveau).execute()
                                taches_db[nom_t] = nouveau
                                
                            date_texte = ""
                            if date_debut_obj and tache_config.get("jours_avant_debut") is not None:
                                d_limite = date_debut_obj - timedelta(days=tache_config["jours_avant_debut"])
                                date_texte = f" *(📅 Limite: {d_limite.strftime('%d/%m')})*"
                                
                            statut_actuel = (taches_db[nom_t].get("status") == "VALIDE")
                            coche = st.checkbox(f"{nom_t}{date_texte}", value=statut_actuel, key=f"{projet_id}_{nom_t}")
                            
                            if coche != statut_actuel:
                                nouveau_statut = "VALIDE" if coche else "EN_ATTENTE"
                                supabase.table("tasks").update({"status": nouveau_statut}).eq("project_id", projet_id).eq("task_name", nom_t).execute()
                                st.rerun()
                        else:
                            st.markdown(f"<span style='color: grey; text-decoration: line-through;'>{nom_t} (Non applicable)</span>", unsafe_allow_html=True)
                    st.markdown("")
    else:
        st.info("👋 Aucun projet enregistré. Rendez-vous dans l'onglet 'Synchronisation Excel' pour importer votre planning.")

# ==========================================
# ONGLET 2 : SYNCHRONISATION
# ==========================================
with onglet_maj:
    st.subheader("Mise à jour du planning")
    st.write("Glissez votre fichier Excel ci-dessous. Les nouveaux chantiers seront ajoutés et les dates synchronisées sans effacer vos validations manuelles.")
    
    with st.container(border=True):
        fichier_upload = st.file_uploader("Fichier Excel du planning (.xlsx)", type=["xlsx"])

    if fichier_upload is not None:
        with st.spinner("Analyse du calendrier en cours..."):
            projets_extraits = lire_excel_calendrier(fichier_upload)
            
            if len(projets_extraits) > 0:
                for p in projets_extraits:
                    date_db = None
                    if p["Date de Début"] != "Non définie":
                        date_obj = datetime.strptime(p["Date de Début"], "%d/%m/%Y")
                        date_db = date_obj.strftime("%Y-%m-%d")
                    
                    reponse_recherche = supabase.table("projects").select("*").eq("project_name", p["Nom du Projet"]).execute()
                    
                    if len(reponse_recherche.data) == 0:
                        nouveau_projet = {
                            "project_name": p["Nom du Projet"],
                            "project_type": p["Type"],
                            "start_date": date_db
                        }
                        supabase.table("projects").insert(nouveau_projet).execute()
                    else:
                        projet_existant = reponse_recherche.data[0]
                        if date_db and projet_existant.get("start_date") != date_db:
                            supabase.table("projects").update({"start_date": date_db}).eq("id", projet_existant["id"]).execute()
                            
                st.success(f"✅ Synchronisation réussie ! {len(projets_extraits)} chantiers actifs pris en compte.")
            else:
                st.warning("Aucun chantier valide trouvé à partir du 1er août 2026.")