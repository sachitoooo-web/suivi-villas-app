import openpyxl

# 1. Tes règles d'intelligence (2 catégories uniquement)
def determiner_type_projet(nom_projet):
    titre = str(nom_projet).upper() 
    
    if "BATTERIE" in titre:
        return "BATTERIE"
    else:
        return "PV"

def verifier_regle_securite(code_couleur_cellule):
    # Si la case n'a pas de couleur, on applique la sécurité par défaut
    if not code_couleur_cellule:
        return True 
        
    couleur = str(code_couleur_cellule).upper()
    
    # Si la couleur contient du rouge ou du blanc
    if "FF0000" in couleur or "FFFFFF" in couleur:
        return False # Non applicable
        
    return True # Applicable

# 2. La machine à lire ton fichier Excel Teams
def lire_excel_projets(chemin_fichier):
    # On ouvre le fichier (data_only=True permet de lire les valeurs, pas les formules)
    classeur = openpyxl.load_workbook(chemin_fichier, data_only=True)
    feuille = classeur.active
    
    projets_trouves = []
    
    # On lit chaque ligne (en sautant la ligne 1 qui contient souvent les titres des colonnes)
    for ligne in feuille.iter_rows(min_row=2):
        cellule_nom = ligne[0] # On part du principe que le nom du client est dans la colonne A
        
        # S'il y a du texte dans la case
        if cellule_nom.value:
            nom = str(cellule_nom.value)
            type_proj = determiner_type_projet(nom)
            
            # On essaie de lire la couleur du fond de la case
            try:
                couleur = cellule_nom.fill.fgColor.rgb
            except:
                couleur = None
                
            securite = verifier_regle_securite(couleur)
            
            # On sauvegarde les infos de ce projet
            projets_trouves.append({
                "nom": nom,
                "type": type_proj,
                "securite_applicable": securite
            })
            
    return projets_trouves