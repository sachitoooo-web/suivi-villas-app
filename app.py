import streamlit as st
from ingestion import lire_excel_calendrier

st.set_page_config(page_title="Suivi Projets Villas", page_icon="☀️", layout="wide")

st.title("☀️ Dashboard de Suivi - Chantiers Villas")
st.markdown("---")

st.subheader("📥 Mise à jour des projets via Excel")
st.write("Glisse ton fichier de planning ici. Seuls tes projets (Vert) actifs à partir du 1er août 2026 seront extraits, avec leur date de début (Jaune).")

fichier_upload = st.file_uploader("Fichier Excel (.xlsx)", type=["xlsx"])

if fichier_upload is not None:
    st.info("Scan du calendrier en cours...")
    
    # Lancement du script
    projets_extraits = lire_excel_calendrier(fichier_upload)
    
    if len(projets_extraits) > 0:
        st.success(f"Scan terminé ! {len(projets_extraits)} de tes chantiers détectés à partir du mois d'août.")
        # Affichage du résultat
        st.dataframe(projets_extraits, use_container_width=True)
    else:
        st.warning("Aucun projet t'appartenant n'a été trouvé à partir du 1er août.")

else:
    st.warning("En attente de ton fichier Excel pour analyser le planning.")