import openpyxl
import re
import datetime

def scanner_planning_excel(fichier_upload):
    wb = openpyxl.load_workbook(fichier_upload, data_only=True)
    projets_finaux = []
    regex_prs = re.compile(r'(PRS\d{5,7})', re.IGNORECASE)
    
    # Couleurs strictement considérées comme "Vert Sacha"
    verts_acceptes = ['00B050', '28A745', '39B54A', '32CD32', '00FF00', '92D050']

    # On ne scanne que les onglets récents
    onglets_a_scanner = [nom for nom in wb.sheetnames if '2025' in nom or '2026' in nom]
    
    for nom_onglet in onglets_a_scanner:
        ws = wb[nom_onglet]
        
        # 1. Cartographier le calendrier (Associer chaque colonne à sa Date)
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
            continue # Pas de calendrier trouvé sur cet onglet
            
        # 2. Scanner le tableau à la recherche de tes projets verts
        for row_idx, row in enumerate(ws.iter_rows(min_row=ligne_des_dates + 1, values_only=False), start=ligne_des_dates + 1):
            for col_idx, cell in enumerate(row):
                if cell.value and isinstance(cell.value, str):
                    match_prs = regex_prs.search(cell.value)
                    
                    if match_prs:
                        prs_code = match_prs.group(1).upper()
                        
                        # Vérification CHIRURGICALE de la couleur de la case
                        est_mon_projet = False
                        if cell.fill and cell.fill.start_color and cell.fill.start_color.rgb:
                            couleur_hex = str(cell.fill.start_color.rgb).upper()
                            
                            if any(vert in couleur_hex for vert in verts_acceptes):
                                est_mon_projet = True
                            # Filtre strict : Composante verte forte, et bleue/rouge faibles (exclut les cyans et bleus)
                            elif len(couleur_hex) == 8 and couleur_hex[2:4] < '88' and couleur_hex[4:6] > '90' and couleur_hex[6:8] < '88':
                                est_mon_projet = True
                                
                        if est_mon_projet:
                            # On récupère directement la date associée à la colonne de cette case verte !
                            date_trouvee = dates_colonnes.get(col_idx)
                            
                            if date_trouvee:
                                nom_complet = str(cell.value).replace('\n', ' ').strip()
                                
                                # On vérifie si on l'a déjà ajouté pour ne pas faire de doublons
                                deja_ajoute = False
                                for p in projets_finaux:
                                    if p["prs"] == prs_code:
                                        # Si le projet prend plusieurs jours, on garde la date la plus ancienne (Début)
                                        if date_trouvee < datetime.date.fromisoformat(p["date_debut"]):
                                            p["date_debut"] = date_trouvee.isoformat()
                                        deja_ajoute = True
                                        break
                                
                                if not deja_ajoute:
                                    projets_finaux.append({
                                        "prs": prs_code,
                                        "nom": nom_complet,
                                        "date_debut": date_trouvee.isoformat(),
                                        "cdp": "Sacha"
                                    })
                                    
    # 3. Filtrer les dates : On ne remonte que les projets depuis janvier 2025
    date_limite = datetime.date(2025, 1, 1)
    projets_filtres = [p for p in projets_finaux if datetime.date.fromisoformat(p["date_debut"]) >= date_limite]

    return projets_filtres