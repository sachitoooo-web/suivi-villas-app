import streamlit as st
import json
from supabase import create_client, Client
from ingestion import lire_excel_calendrier

# 1. Connexion à Supabase
@st.cache_resource
def initialiser_supabase():
    url = st.secrets["SUPABASE_URL"]
    cle = st.secrets["SUPABASE_KEY"]
    return create_client(url, cle)

supabase: Client = initialiser_supabase()

# 2. Lecture du fichier de configuration (Ton dictionnaire JSON)
@st.cache_data
def charger_config_checklists():
    with open("checklists_config.json", "r", encoding="utf-8") as f:
        return json.load(f)

config = charger_config_checklists()

# -- DEBUT DE L'INTERFACE WEB --
st.set_page_config(page_title="Suivi Projets Villas", page_icon="☀️", layout="wide")
st.title("☀️ Dashboard de Suivi - Chantiers Villas")

# Création de deux onglets de navigation
onglet_suivi, onglet_maj = st.tabs(["📊 Suivi des Projets", "📥 Mise à jour (Excel)"])

# ONGLET 1 : LA FICHE PROJET ET LES 5 PHASES
with onglet_suivi:
    st.subheader("Détail des documents attendus")
    
    # On va chercher tous les projets sauvegardés dans Supabase
    reponse_db = supabase.table("projects").select("*").execute()
    projets_enregistres = reponse_db.data
    
    if len(projets_enregistres) > 0:
        # On extrait juste les noms pour la liste déroulante
        liste_noms = [p["project_name"] for p in projets_enregistres]
        
        # Le sélecteur de projet
        projet_choisi = st.selectbox("Sélectionne un chantier à auditer :", liste_noms)
        
        # On retrouve les infos de ce projet précis
        infos_projet = next(p for p in projets_enregistres if p["project_name"] == projet_choisi)
        type_du_projet = infos_projet["project_type"]
        
        st.info(f"Type d'installation : **{type_du_projet}**")
        st.markdown("---")
        
        # On affiche les 5 phases en lisant le fichier JSON
        col1, col2 = st.columns(2) # On coupe l'écran en deux pour que ce soit joli
        
        with col1:
            for phase_nom in ["1_Initialisation", "2_Visite_Technique", "3_Planification"]:
                st.markdown(f"### {phase_nom.replace('_', ' ')}")
                taches = config.get(phase_nom, [])
                
                for tache in taches:
                    # On vérifie si la tâche est requise pour CE type de projet
                    if type_du_projet in tache["types_projets"]:
                        # Plus tard, le "value" sera connecté à Supabase pour se cocher tout seul
                        st.checkbox(f"📄 {tache['tache']} *(Mot-clé: {tache['mot_cle_document']})*", value=False)
                    else:
                        # Si ce n'est pas applicable, on le barre
                        st.write(f"~~{tache['tache']}~~ *(Non applicable)*")
                        
        with col2:
            for phase_nom in ["4_Communication", "5_Reception"]:
                st.markdown(f"### {phase_nom.replace('_', ' ')}")
                taches = config.get(phase_nom, [])
                
                for tache in taches:
                    if type_du_projet in tache["types_projets"]:
                        st.checkbox(f"📄 {tache['tache']} *(Mot-clé: {tache['mot_cle_document']})*", value=False)
                    else:
                        st.write(f"~~{tache['tache']}~~ *(Non applicable)*")
                        
    else:
        st.warning("Aucun projet trouvé. Va dans l'onglet 'Mise à jour (Excel)' pour scanner ton planning.")


# ONGLET 2 : LE GLISSER-DEPOSER EXCEL (Ton code précédent)
with onglet_maj:
    st.subheader("Mise à jour de la base de données")
    fichier_upload = st.file_uploader("Glisse ton fichier de planning Excel ici", type=["xlsx"])

    if fichier_upload is not None:
        st.info("Scan du calendrier en cours...")
        projets_extraits = lire_excel_calendrier(fichier_upload)
        
        if len(projets_extraits) > 0:
            st.success(f"{len(projets_extraits)} chantiers détectés. Enregistrement...")
            for p in projets_extraits:
                reponse_recherche = supabase.table("projects").select("*").eq("project_name", p["Nom du Projet"]).execute()
                if len(reponse_recherche.data) == 0:
                    nouveau_projet = {
                        "project_name": p["Nom du Projet"],
                        "project_type": p["Type"],
                        "security_applicable": True 
                    }
                    supabase.table("projects").insert(nouveau_projet).execute()
            st.success("✅ Synchronisation terminée !")
        else:
            st.warning("Aucun nouveau projet trouvé.")