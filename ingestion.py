import openpyxl
import re
import datetime

def scanner_planning_excel(fichier_upload):
    """
    Lit le fichier Excel, recherche les cellules vertes contenant 'PRS',
    cherche la cellule jaune correspondante sur la même ligne pour la date de début,
    et filtre les projets à partir d'une certaine date (ex: 1er août 2026).
    """
    # data_only=True permet de lire les valeurs et non les formules
    wb = openpyxl.load_workbook(fichier_upload, data_only=True)
    projets_trouves = []
    
    # Expression régulière pour capter les formats PRS (ex: PRS076108)
    regex_prs = re.compile(r'(PRS\d{5,7})', re.IGNORECASE)
    
    # On scanne les onglets des années 2025 et 2026
    onglets_a_scanner = [nom for nom in wb.sheetnames if '2025' in nom or '2026' in nom]
    
    for nom_onglet in onglets_a_scanner:
        ws = wb[nom_onglet]
        
        # 1. Trouver la ligne du calendrier (celle avec les dates)
        ligne_des_dates = None
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=False)):
            for cell in row:
                if isinstance(cell.value, datetime.datetime):
                    ligne_des_dates = i + 1
                    break
            if ligne_des_dates:
                break
                
        if not ligne_des_dates:
            continue
            
        # 2. Scanner les cellules sous la ligne du calendrier
        for row_idx, row in enumerate(ws.iter_rows(min_row=ligne_des_dates + 1, values_only=False), start=ligne_des_dates + 1):
            projet_nom = None
            prs_code = None
            date_debut = None
            est_mon_projet = False
            
            for col_idx, cell in enumerate(row):
                if cell.value and isinstance(cell.value, str):
                    match_prs = regex_prs.search(cell.value)
                    
                    if match_prs:
                        prs_code = match_prs.group(1).upper()
                        projet_nom = str(cell.value).replace('\n', ' ').strip()
                        
                        # Vérification de la couleur Verte
                        if cell.fill and cell.fill.start_color and cell.fill.start_color.rgb:
                            couleur_hex = str(cell.fill.start_color.rgb).upper()
                            
                            # Liste des verts standards (dont celui de ton image)
                            verts_acceptes = ['00B050', '28A745', '39B54A', '32CD32', '00FF00', '92D050']
                            
                            if any(vert in couleur_hex for vert in verts_acceptes):
                                est_mon_projet = True
                            # Hack de secours pour les verts très saturés si la nuance change légèrement
                            elif len(couleur_hex) == 8 and couleur_hex[2:4] < '88' and couleur_hex[4:6] > 'A0':
                                est_mon_projet = True

            # 3. Si c'est un projet vert, chercher le top départ (Jaune)
            if est_mon_projet and prs_code:
                for col_idx, cell in enumerate(row):
                    if cell.fill and cell.fill.start_color and cell.fill.start_color.rgb:
                        couleur_hex = str(cell.fill.start_color.rgb).upper()
                        
                        # Détection du jaune standard ou doré
                        if 'FFFF00' in couleur_hex or 'FFC000' in couleur_hex:
                            cell_date = ws.cell(row=ligne_des_dates, column=col_idx + 1)
                            if isinstance(cell_date.value, datetime.datetime):
                                date_debut = cell_date.value.date().isoformat()
                                break
                
                # S'il n'y a pas de jaune, on met la date du jour par sécurité
                if not date_debut:
                    date_debut = datetime.date.today().isoformat()
                    
                # --- FILTRE DE DATE ---
                # On définit la date limite au 1er août 2026
                date_limite = datetime.date(2026, 8, 1)
                
                # On transforme notre date texte en vraie date pour pouvoir comparer
                date_projet_obj = datetime.date.fromisoformat(date_debut)
                
                # On n'ajoute le projet que s'il est après ou égal à la date limite
                if date_projet_obj >= date_limite:
                    projets_trouves.append({
                        "prs": prs_code,
                        "nom": projet_nom,
                        "date_debut": date_debut,
                        "cdp": "Sacha"
                    })

    return projets_trouves