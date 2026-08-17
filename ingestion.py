import openpyxl
import re
import datetime

def scanner_planning_excel(fichier_upload):
    wb = openpyxl.load_workbook(fichier_upload, data_only=True)
    projets_bruts = []
    
    regex_prs = re.compile(r'(PRS\d{5,7})', re.IGNORECASE)
    # Les codes hexadécimaux stricts de TA couleur verte sur Excel
    verts_acceptes = ['00B050', '28A745', '39B54A', '32CD32']
    
    onglets_a_scanner = [nom for nom in wb.sheetnames if '2025' in nom or '2026' in nom]
    
    for nom_onglet in onglets_a_scanner:
        ws = wb[nom_onglet]
        
        # 1. Repérer la ligne des dates pour l'en-tête des colonnes
        ligne_des_dates = None
        dates_colonnes = {}
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=False)):
            for col_idx, cell in enumerate(row):
                if isinstance(cell.value, datetime.datetime):
                    ligne_des_dates = i + 1
                    break
            if ligne_des_dates:
                for col_idx, cell in enumerate(row):
                    if isinstance(cell.value, datetime.datetime):
                        dates_colonnes[col_idx] = cell.value.date()
                break
                
        if not ligne_des_dates:
            continue
            
        # 2. Scanner le tableau
        for row in ws.iter_rows(min_row=ligne_des_dates + 1, values_only=False):
            for col_idx, cell in enumerate(row):
                if cell.value and isinstance(cell.value, str):
                    match_prs = regex_prs.search(cell.value)
                    
                    if match_prs:
                        prs_code = match_prs.group(1).upper()
                        
                        # Vérifier la couleur verte
                        est_mon_projet = False
                        if cell.fill and cell.fill.start_color and cell.fill.start_color.rgb:
                            couleur_hex = str(cell.fill.start_color.rgb).upper()
                            if any(vert in couleur_hex for vert in verts_acceptes):
                                est_mon_projet = True
                                
                        if est_mon_projet:
                            # Associer le projet à la date de sa colonne
                            date_trouvee = dates_colonnes.get(col_idx)
                            if date_trouvee:
                                projets_bruts.append({
                                    "prs": prs_code,
                                    "nom": str(cell.value).replace('\n', ' ').strip(),
                                    "date_debut": date_trouvee,
                                    "cdp": "Sacha"
                                })

    # 3. Consolidation et filtrage (1er Août 2026)
    date_limite = datetime.date(2026, 8, 1)
    projets_uniques = {}
    
    for p in projets_bruts:
        if p["date_debut"] >= date_limite:
            prs = p["prs"]
            # Si le projet est sur plusieurs jours, on garde la date de début la plus ancienne
            if prs not in projets_uniques or p["date_debut"] < projets_uniques[prs]["date_debut"]:
                projets_uniques[prs] = p

    # Formatage final
    projets_finaux = []
    for prs, p in projets_uniques.items():
        projets_finaux.append({
            "prs": prs,
            "nom": p["nom"],
            "date_debut": p["date_debut"].isoformat(),
            "cdp": p["cdp"]
        })
        
    return projets_finaux