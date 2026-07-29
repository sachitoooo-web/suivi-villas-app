import streamlit as st
from supabase import create_client, Client
from ingestion import lire_excel_calendrier

# 1. Connexion sécurisée à Supabase
@st.cache_resource
def initialiser_supabase():
    url = st.secrets["SUPABASE_URL"]
    cle = st.secrets["SUPABASE_KEY"]
    return create_client(url, cle)

supabase: Client = initialiser_supabase()

st.set_page_config(page_title="Suivi Projets Villas", page_icon="☀️", layout="wide")
st.title("☀️ Dashboard de Suivi - Chantiers Villas")
st.markdown("---")

st.subheader("📥 Mise à jour des projets via Excel")
st.write("Glisse ton fichier de planning ici. Les projets seront automatiquement sauvegardés dans la base de données.")

fichier_upload = st.file_uploader("Fichier Excel (.xlsx)", type=["xlsx"])

if fichier_upload is not None:
    st.info("Scan du calendrier en cours...")
    
    # On extrait les données
    projets_extraits = lire_excel_calendrier(fichier_upload)
    
    if len(projets_extraits) > 0:
        st.success(f"Scan terminé ! {len(projets_extraits)} chantiers détectés.")
        
        # Affichage visuel
        st.dataframe(projets_extraits, use_container_width=True)
        
        # 2. SAUVEGARDE EN BASE DE DONNÉES
        st.write("⏳ Enregistrement dans la base de données...")
        
        for p in projets_extraits:
            # On vérifie d'abord si le projet existe déjà pour ne pas créer de doublons
            reponse_recherche = supabase.table("projects").select("*").eq("project_name", p["Nom du Projet"]).execute()
            
            if len(reponse_recherche.data) == 0:
                # S'il n'existe pas, on l'ajoute !
                nouveau_projet = {
                    "project_name": p["Nom du Projet"],
                    "project_type": p["Type"],
                    "security_applicable": True # Par défaut pour le moment
                }
                supabase.table("projects").insert(nouveau_projet).execute()
                
        st.success("✅ Tous les projets sont sauvegardés dans Supabase !")
        
    else:
        st.warning("Aucun projet t'appartenant n'a été trouvé à partir du 1er août.")