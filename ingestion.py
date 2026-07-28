import openpyxl

# 1. Règles d'intelligence
def determiner_type_projet(texte_cellule):
    titre = str(texte_cellule).upper() 
    if "BATTERIE" in titre:
        return "BATTERIE"
    return "PV"

def verifier_regle_securite(code_couleur):
    couleur = str(code_couleur).upper()
    # Si la couleur contient du rouge ou du blanc
    if "FF0000" in couleur or "FFFFFF" in couleur:
        return False # Non applicable
    return True # Applicable

# 2. Le nouveau scanner 2D pour ton calendrier
def lire_excel_calendrier(fichier_binaire):
    # On lit le fichier qui viendra du glisser-déposer
    classeur = openpyxl.load_workbook(fichier_binaire, data_only=True)
    feuille = classeur.active
    
    # On utilise un "dictionnaire" pour éviter les doublons (si un projet dure 3 jours)
    projets_trouves = {} 
    
    # On scanne la grille complète, case par case
    for ligne in feuille.iter_rows():
        for cellule in ligne:
            # S'il y a du texte dans la case
            if cellule.value:
                texte = str(cellule.value)
                
                # Astuce : On repère les vrais projets grâce au préfixe "PRS"
                if "PRS" in texte:
                    type_proj = determiner_type_projet(texte)
                    
                    try:
                        couleur = cellule.fill.fgColor.rgb
                    except:
                        couleur = None
                        
                    securite = verifier_regle_securite(couleur)
                    
                    # On nettoie le texte (on enlève les sauts de ligne pour faire un titre propre)
                    nom_propre = texte.replace("\n", " ").strip()
                    
                    # Si on n'a pas encore vu ce projet, on l'ajoute à la liste
                    if nom_propre not in projets_trouves:
                        projets_trouves[nom_propre] = {
                            "nom": nom_propre,
                            "type": type_proj,
                            "securite_applicable": securite
                        }
                        
    # On renvoie la liste finale sans doublons
    return list(projets_trouves.values())