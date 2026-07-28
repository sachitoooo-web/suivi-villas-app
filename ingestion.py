import openpyxl
from datetime import datetime

def lire_excel_calendrier(fichier_binaire):
    classeur = openpyxl.load_workbook(fichier_binaire, data_only=True)
    feuille = classeur.active
    
    projets = {}
    
    # La date limite : 1er août 2026
    date_limite = datetime(2026, 8, 1)
    
    # On scanne à partir de la ligne 3 (pour sauter les dates en haut)
    for ligne in feuille.iter_rows(min_row=3):
        for cellule in ligne:
            valeur = cellule.value
            
            if valeur and isinstance(valeur, str) and "PRS" in valeur:
                nom_propre = valeur.replace("\n", " ").strip()
                
                # Initialisation du projet s'il n'existe pas encore dans notre liste
                if nom_propre not in projets:
                    projets[nom_propre] = {
                        "Nom du Projet": nom_propre,
                        "Type": "BATTERIE" if "BATTERIE" in nom_propre.upper() else "PV",
                        "EstMonProjet": False,
                        "Date de Début": "Non définie",
                        "EstApresAout": False # Filtre pour le 1er août
                    }
                
                # 1. Capture de la couleur
                try:
                    couleur_hex = str(cellule.fill.fgColor.rgb)
                except:
                    couleur_hex = "INCONNUE"
                    
                # 2. Capture de la date sur la ligne 2
                date_val = feuille.cell(row=2, column=cellule.column).value
                est_valide_temporellement = False
                
                if isinstance(date_val, datetime) and date_val >= date_limite:
                    est_valide_temporellement = True
                
                # 3. Application des règles Vert et Jaune
                if couleur_hex == "FF00B050" or couleur_hex == "FF4CAF50": # Ton Vert (Tolérance sur 2 nuances)
                    projets[nom_propre]["EstMonProjet"] = True
                    if est_valide_temporellement:
                        projets[nom_propre]["EstApresAout"] = True
                        
                elif couleur_hex == "FFFFFF00": # Jaune (Début des travaux)
                    if isinstance(date_val, datetime) and projets[nom_propre]["Date de Début"] == "Non définie":
                        # On enregistre la date au format lisible (JJ/MM/AAAA)
                        projets[nom_propre]["Date de Début"] = date_val.strftime("%d/%m/%Y")
                    if est_valide_temporellement:
                        projets[nom_propre]["EstApresAout"] = True

    # 4. On filtre pour ne renvoyer QUE tes projets (Vert) qui sont actifs après le 1er août
    mes_projets_finaux = []
    for p in projets.values():
        if p["EstMonProjet"] and p["EstApresAout"]:
            mes_projets_finaux.append({
                "Nom du Projet": p["Nom du Projet"],
                "Type": p["Type"],
                "Date de Début": p["Date de Début"]
            })
            
    return mes_projets_finaux