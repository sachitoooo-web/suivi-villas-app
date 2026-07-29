import streamlit as st
import json
from supabase import create_client, Client
from ingestion import lire_excel_calendrier
from datetime import datetime, timedelta

# 1. Connexion à Supabase
@st.cache_resource
def initialiser_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = initialiser_supabase()

# 2. Lecture du fichier JSON (Configuration des phases)
@st.cache_data
def charger_config_checklists():
    with open("checklists_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

config = charger_config_checklists()

st.set_page_config(page_title="Suivi Projets Villas", page_icon="☀️", layout="wide")
st.title("☀️ Pilotage des Chantiers Villas")

onglet_suivi, onglet_maj = st.tabs(["📊 Suivi & Pilotage", "📥 Synchronisation Excel"])

# ==========================================
# ONGLET 1 : FICHE PROJET ET PILOTAGE MANUEL
# ==========================================
with onglet_suivi:
    st.subheader("Rechercher et auditer un projet")
    
    reponse_db = supabase.table("projects").select("*").execute()
    projets_enregistres = reponse_db.data
    
    if len(projets_enregistres) > 0:
        # Barre de recherche (selectbox permet de taper du texte)
        liste_noms = [p["project_name"] for p in projets_enregistres]
        projet_choisi = st.selectbox("🔍 Tape le nom du client ou du projet :", liste_noms)
        
        # Récupération des infos du projet sélectionné
        infos_projet = next(p for p in projets_enregistres if p["project_name"] == projet_choisi)
        projet_id = infos_projet["id"]
        type_du_projet = infos_projet["project_type"]
        date_debut_str = infos_projet.get("start_date")
        
        # Affichage de l'en-tête du projet
        col_info1, col_info2 = st.columns(2)
        col_info1.info(f"⚡ Type : **{type_du_projet}**")
        
        # Formatage de la date de début pour l'affichage
        date_debut_obj = None
        if date_debut_str:
            date_debut_obj = datetime.strptime(date_debut_str, "%Y-%m-%d")
            col_info2.success(f"🏗️ Début des travaux : **{date_debut_obj.strftime('%d/%m/%Y')}**")
        else:
            col_info2.warning("⏳ Début des travaux : **Non définie**")
            
        st.markdown("---")
        
        # Récupération de l'état des cases à cocher depuis la base de données
        reponse_tasks = supabase.table("tasks").select("*").eq("project_id", projet_id).execute()
        taches_db = {t["task_name"]: t for t in reponse_tasks.data}

        # Affichage des 5 phases sur deux colonnes
        col_gauche, col_droite = st.columns(2)
        colonnes_repartition = [col_gauche, col_gauche, col_gauche, col_droite, col_droite]
        
        # On parcourt les 5 phases du fichier JSON
        for idx, (phase_nom, liste_taches) in enumerate(config.items()):
            with colonnes_repartition[idx]:
                st.markdown(f"### {phase_nom.replace('_', ' ')}")
                
                for tache_config in liste_taches:
                    nom_t = tache_config["tache"]
                    
                    # Si la tâche s'applique à ce type de projet (ex: PV)
                    if type_du_projet in tache_config["types_projets"]:
                        
                        # Création de la tâche dans la base de données si elle n'existe pas encore
                        if nom_t not in taches_db:
                            nouveau = {"project_id": projet_id, "task_name": nom_t, "status": "EN_ATTENTE", "phase": int(phase_nom[0])}
                            supabase.table("tasks").insert(nouveau).execute()
                            taches_db[nom_t] = nouveau
                            
                        # Calcul de la date limite (ex: J-14)
                        date_texte = ""
                        if date_debut_obj and tache_config.get("jours_avant_debut") is not None:
                            d_limite = date_debut_obj - timedelta(days=tache_config["jours_avant_debut"])
                            date_texte = f" *(📅 {d_limite.strftime('%d/%m')})*"
                            
                        # Affichage de la case à cocher (reliée à la base de données)
                        statut_actuel = (taches_db[nom_t].get("status") == "VALIDE")
                        coche = st.checkbox(f"{nom_t}{date_texte}", value=statut_actuel, key=f"{projet_id}_{nom_t}")
                        
                        # Si tu cliques sur la case, ça met à jour Supabase !
                        if coche != statut_actuel:
                            nouveau_statut = "VALIDE" if coche else "EN_ATTENTE"
                            supabase.table("tasks").update({"status": nouveau_statut}).eq("project_id", projet_id).eq("task_name", nom_t).execute()
                            st.rerun() # Rafraîchit l'écran pour confirmer l'action
                    else:
                        st.write(f"~~{nom_t}~~")
                        
    else:
        st.warning("Aucun projet dans la base. Va dans l'onglet 'Synchronisation Excel'.")

# ==========================================
# ONGLET 2 : SYNCHRONISATION INTELLIGENTE
# ==========================================
with onglet_maj:
    st.subheader("Mise à jour via Excel")
    st.write("Les nouveaux projets seront ajoutés. Les dates de début seront mises à jour. **Tes cases cochées ne seront jamais effacées.**")
    
    fichier_upload = st.file_uploader("Glisse ton fichier de planning Excel ici", type=["xlsx"])

    if fichier_upload is not None:
        projets_extraits = lire_excel_calendrier(fichier_upload)
        
        if len(projets_extraits) > 0:
            st.success(f"Scan terminé. Analyse de {len(projets_extraits)} projets...")
            
            for p in projets_extraits:
                # Formatage de la date pour Supabase (AAAA-MM-JJ)
                date_db = None
                if p["Date de Début"] != "Non définie":
                    date_obj = datetime.strptime(p["Date de Début"], "%d/%m/%Y")
                    date_db = date_obj.strftime("%Y-%m-%d")
                
                # On cherche si le projet existe déjà
                reponse_recherche = supabase.table("projects").select("*").eq("project_name", p["Nom du Projet"]).execute()
                
                if len(reponse_recherche.data) == 0:
                    # Le projet n'existe pas -> ON CRÉE
                    nouveau_projet = {
                        "project_name": p["Nom du Projet"],
                        "project_type": p["Type"],
                        "start_date": date_db
                    }
                    supabase.table("projects").insert(nouveau_projet).execute()
                else:
                    # Le projet existe déjà -> ON MET À JOUR LA DATE UNIQUEMENT (si elle a changé)
                    projet_existant = reponse_recherche.data[0]
                    if date_db and projet_existant.get("start_date") != date_db:
                        supabase.table("projects").update({"start_date": date_db}).eq("id", projet_existant["id"]).execute()
                        
            st.success("✅ Base de données parfaitement synchronisée !")
        else:
            st.warning("Aucun projet actif trouvé.")