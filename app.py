import streamlit as st
from ingestion import lire_excel_calendrier # On importe notre cerveau !

st.set_page_config(page_title="Suivi Projets Villas", page_icon="☀️", layout="wide")

st.title("☀️ Dashboard de Suivi - Chantiers Villas")
st.markdown("---")

st.subheader("📥 Mise à jour des projets")
st.write("Glisse ton fichier de planning Excel ici pour mettre à jour la liste des projets.")

# La zone magique de glisser-déposer
fichier_upload = st.file_uploader("Fichier Excel (.xlsx)", type=["xlsx"])

if fichier_upload is not None:
    # Si un fichier a été déposé, on lance le scanner !
    st.info("Scan du calendrier en cours...")
    
    # On envoie le fichier à notre script Python
    projets_extraits = lire_excel_calendrier(fichier_upload)
    
    st.success(f"Scan terminé ! {len(projets_extraits)} projets uniques trouvés.")
    
    # On affiche les résultats dans un beau tableau
    st.dataframe(projets_extraits, use_container_width=True)

else:
    st.warning("En attente d'un fichier Excel pour afficher les données.")