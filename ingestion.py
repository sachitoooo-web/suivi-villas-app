import openpyxl
from datetime import datetime

def lire_excel_calendrier(fichier_binaire):
    classeur = openpyxl.load_workbook(fichier_binaire, data_only=True)
    feuille = classeur.active
    
    projets = {}
    date_limite = datetime(2026, 8, 1)
    
    for ligne in feuille.iter_rows(min_row=3):
        for cellule in ligne:
            valeur = cellule.value
            
            if valeur and isinstance(valeur, str) and "PRS" in valeur:
                nom_propre = valeur.replace("\n", " ").strip()
                is_battery = "BATTERIE" in nom_propre.upper()
                type_proj = "BATTERIE" if is_battery else "PV"
                
                if nom_propre not in projets:
                    projets[nom_propre] = {
                        "Nom du Projet": nom_propre,
                        "Type": type_proj,
                        "EstMonProjet": False,
                        "Date de Début": "Non définie",
                        "EstApresAout": False
                    }
                
                try:
                    couleur_hex = str(cellule.fill.fgColor.rgb)
                except:
                    couleur_hex = "INCONNUE"
                    
                date_val = feuille.cell(row=2, column=cellule.column).value
                est_valide_temporellement = False
                
                if isinstance(date_val, datetime) and date_val >= date_limite:
                    est_valide_temporellement = True
                
                # Case Verte : Ton projet
                if couleur_hex == "FF00B050" or couleur_hex == "FF4CAF50":
                    projets[nom_propre]["EstMonProjet"] = True
                    if est_valide_temporellement:
                        projets[nom_propre]["EstApresAout"] = True
                    
                    # Subtilité Batterie : La case verte sert de date de chantier (1 jour)
                    if is_battery and isinstance(date_val, datetime) and projets[nom_propre]["Date de Début"] == "Non définie":
                        if est_valide_temporellement:
                            projets[nom_propre]["Date de Début"] = date_val.strftime("%d/%m/%Y")
                            
                # Case Jaune : Début des travaux (uniquement pour le PV)
                elif couleur_hex == "FFFFFF00":
                    if not is_battery and isinstance(date_val, datetime) and projets[nom_propre]["Date de Début"] == "Non définie":
                        projets[nom_propre]["Date de Début"] = date_val.strftime("%d/%m/%Y")
                    if est_valide_temporellement:
                        projets[nom_propre]["EstApresAout"] = True

    mes_projets_finaux = []
    for p in projets.values():
        if p["EstMonProjet"] and p["EstApresAout"]:
            mes_projets_finaux.append({
                "Nom du Projet": p["Nom du Projet"],
                "Type": p["Type"],
                "Date de Début": p["Date de Début"]
            })
            
    return mes_projets_finaux