from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

def charger_annonces():
    """Charge les annonces depuis le fichier JSON"""
    try:
        if os.path.exists('./Pipeline_Immo/Script/Selenium/citya_annonces.json'):
            with open('./Pipeline_Immo/Script/Selenium/citya_annonces.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Erreur chargement: {e}")
        return []

def extraire_prix(prix_str):
    """Extrait le prix numérique"""
    if not prix_str:
        return 0
    import re
    match = re.search(r'([\d\s]+)', prix_str)
    if match:
        return int(match.group(1).replace(' ', ''))
    return 0

def extraire_surface(titre):
    """Extrait la surface en m²"""
    if not titre:
        return 0
    import re
    match = re.search(r'(\d+(?:\.\d+)?)\s*m²', titre)
    if match:
        return float(match.group(1))
    return 0

def extraire_pieces(titre):
    """Extrait le nombre de pièces"""
    if not titre:
        return 0
    import re
    match = re.search(r'(\d+)\s*pièces?', titre)
    if match:
        return int(match.group(1))
    return 0

def extraire_type_bien(titre):
    """Extrait le type de bien"""
    if not titre:
        return "Autre"
    titre_lower = titre.lower()
    if 'appartement' in titre_lower:
        return 'Appartement'
    elif 'parking' in titre_lower:
        return 'Parking'
    elif 'maison' in titre_lower:
        return 'Maison'
    elif 'studio' in titre_lower:
        return 'Studio'
    return 'Autre'

@app.route('/')
def index():
    """Page d'accueil avec liste des annonces"""
    annonces = charger_annonces()
    
    # Enrichir les annonces avec des données extraites
    for annonce in annonces:
        annonce['prix_num'] = extraire_prix(annonce.get('prix', ''))
        annonce['surface'] = extraire_surface(annonce.get('titre', ''))
        annonce['pieces'] = extraire_pieces(annonce.get('titre', ''))
        annonce['type_bien'] = extraire_type_bien(annonce.get('titre', ''))
    
    # Statistiques
    stats = {
        'total': len(annonces),
        'prix_moyen': int(sum(a['prix_num'] for a in annonces) / len(annonces)) if annonces else 0,
        'surface_moyenne': int(sum(a['surface'] for a in annonces if a['surface'] > 0) / len([a for a in annonces if a['surface'] > 0])) if any(a['surface'] > 0 for a in annonces) else 0,
        'types': {}
    }
    
    for annonce in annonces:
        type_bien = annonce['type_bien']
        stats['types'][type_bien] = stats['types'].get(type_bien, 0) + 1
    
    return render_template('index.html', annonces=annonces, stats=stats)

@app.route('/api/annonces')
def api_annonces():
    """API JSON pour récupérer les annonces"""
    annonces = charger_annonces()
    
    # Filtres
    ville = request.args.get('ville', '')
    type_bien = request.args.get('type', '')
    prix_min = request.args.get('prix_min', type=int)
    prix_max = request.args.get('prix_max', type=int)
    
    # Enrichir et filtrer
    resultats = []
    for annonce in annonces:
        annonce['prix_num'] = extraire_prix(annonce.get('prix', ''))
        annonce['surface'] = extraire_surface(annonce.get('titre', ''))
        annonce['pieces'] = extraire_pieces(annonce.get('titre', ''))
        annonce['type_bien'] = extraire_type_bien(annonce.get('titre', ''))
        
        # Appliquer les filtres
        if ville and ville.lower() not in annonce.get('ville', '').lower():
            continue
        if type_bien and type_bien != annonce['type_bien']:
            continue
        if prix_min and annonce['prix_num'] < prix_min:
            continue
        if prix_max and annonce['prix_num'] > prix_max:
            continue
        
        resultats.append(annonce)
    
    return jsonify(resultats)

@app.template_filter('format_prix')
def format_prix(value):
    """Formate un prix en euros"""
    try:
        return f"{int(value):,}".replace(',', ' ') + " €"
    except:
        return value

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)