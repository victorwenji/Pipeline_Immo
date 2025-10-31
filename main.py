from flask import Flask, render_template_string, session, redirect, url_for, request
import csv
import os
import glob

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_super_secure_2025'  # Changez cette clé en production

# Identifiants statiques (à personnaliser)
UTILISATEURS = {
    'admin': 'admin123',
    'user': 'password',
    'citya': 'citya2025'
}

# Template de connexion
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connexion - Citya Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .login-container {
            background: white;
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 450px;
            animation: slideIn 0.5s ease-out;
        }
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(-30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .logo {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo-icon {
            font-size: 4em;
            margin-bottom: 10px;
        }
        h1 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 40px;
            font-size: 0.95em;
        }
        .form-group {
            margin-bottom: 25px;
        }
        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 0.95em;
        }
        input {
            width: 100%;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: all 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn-login {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 10px;
        }
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
        }
        .btn-login:active {
            transform: translateY(0);
        }
        .error-message {
            background: #ff6b6b;
            color: white;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            animation: shake 0.5s;
        }
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-10px); }
            75% { transform: translateX(10px); }
        }
        .info-box {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-top: 30px;
            border-left: 4px solid #667eea;
        }
        .info-box h3 {
            color: #667eea;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .info-box ul {
            list-style: none;
            padding-left: 0;
        }
        .info-box li {
            color: #666;
            font-size: 0.9em;
            margin: 8px 0;
            padding-left: 20px;
            position: relative;
        }
        .info-box li:before {
            content: "👤";
            position: absolute;
            left: 0;
        }
        .remember-me {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 15px;
        }
        .remember-me input[type="checkbox"] {
            width: auto;
            cursor: pointer;
        }
        .remember-me label {
            margin: 0;
            font-weight: normal;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <div class="logo-icon">🏠</div>
            <h1>Immo Flex</h1>
            <p class="subtitle">Connectez-vous pour accéder aux annonces</p>
        </div>

        {% if error %}
        <div class="error-message">
            ❌ {{ error }}
        </div>
        {% endif %}

        <form method="POST" action="{{ url_for('login') }}">
            <div class="form-group">
                <label for="username">Nom d'utilisateur</label>
                <input type="text" id="username" name="username" placeholder="Entrez votre nom d'utilisateur" required autofocus>
            </div>

            <div class="form-group">
                <label for="password">Mot de passe</label>
                <input type="password" id="password" name="password" placeholder="Entrez votre mot de passe" required>
            </div>

            <div class="remember-me">
                <input type="checkbox" id="remember" name="remember">
                <label for="remember">Se souvenir de moi</label>
            </div>

            <button type="submit" class="btn-login">Se connecter →</button>
        </form>

        <div class="info-box">
            <h3>Comptes de test</h3>
            <ul>
                <li><strong>admin</strong> / admin123</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

# Template HTML intégré (dashboard)
TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Annonces Citya</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            background: white;
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .header-left {
            flex: 1;
        }
        .header-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .user-info {
            background: #f8f9fa;
            padding: 10px 20px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #667eea;
            font-weight: 600;
        }
        .btn-logout {
            padding: 10px 25px;
            background: #ff6b6b;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            transition: background 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .btn-logout:hover {
            background: #ee5a52;
        }
        h1 { color: #667eea; font-size: 2.5em; margin-bottom: 10px; }
        .subtitle { color: #666; font-size: 1.1em; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .filters {
            background: white;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .filter-group {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        .filter-input {
            flex: 1;
            min-width: 200px;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s;
        }
        .filter-input:focus {
            outline: none;
            border-color: #667eea;
        }
        .btn {
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: background 0.3s;
        }
        .btn:hover { background: #5568d3; }
        .annonces-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }
        .annonce-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        .annonce-card:hover { transform: translateY(-5px); }
        .annonce-image {
            width: 100%;
            height: 200px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 3em;
        }
        .annonce-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .annonce-content { padding: 20px; }
        .annonce-type {
            display: inline-block;
            padding: 5px 15px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            font-size: 0.8em;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .annonce-titre {
            font-size: 1.1em;
            color: #333;
            margin: 10px 0;
            font-weight: 600;
            line-height: 1.4;
            min-height: 60px;
        }
        .annonce-ville {
            color: #666;
            margin: 5px 0;
            font-size: 0.95em;
        }
        .annonce-details {
            display: flex;
            gap: 15px;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        .detail-item {
            display: flex;
            align-items: center;
            gap: 5px;
            color: #666;
            font-size: 0.9em;
        }
        .badge {
            display: inline-block;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.8em;
            font-weight: bold;
            margin: 5px 5px 5px 0;
        }
        .badge-success {
            background: #51cf66;
            color: white;
        }
        .badge-warning {
            background: #ffd43b;
            color: #333;
        }
        .badge-info {
            background: #74c0fc;
            color: white;
        }
        .badge-danger {
            background: #ff6b6b;
            color: white;
        }
        .score-bar {
            background: #e9ecef;
            height: 8px;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #51cf66 0%, #40c057 100%);
            transition: width 0.3s;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }
        .info-item {
            font-size: 0.85em;
            color: #666;
        }
        .info-item strong {
            color: #333;
            display: block;
            margin-bottom: 3px;
        }
        .annonce-prix {
            font-size: 1.8em;
            color: #667eea;
            font-weight: bold;
            margin: 15px 0;
        }
        .annonce-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 15px;
            border-top: 1px solid #e0e0e0;
        }
        .voir-plus {
            padding: 10px 25px;
            background: #764ba2;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s;
        }
        .voir-plus:hover { background: #5d3a7d; }
        .no-results {
            text-align: center;
            padding: 50px;
            background: white;
            border-radius: 15px;
            color: #666;
        }
        @media (max-width: 768px) {
            .annonces-grid { grid-template-columns: 1fr; }
            h1 { font-size: 1.8em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-left">
                <h1>🏠 Dashboard Annonces Citya</h1>
                <p class="subtitle">{{ total_annonces }} annonces trouvées</p>
            </div>
            <div class="header-right">
                <div class="user-info">
                    👤 {{ username }}
                </div>
                <a href="{{ url_for('logout') }}" class="btn-logout">Déconnexion</a>
            </div>
        </header>

        {% if total_annonces > 0 %}
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Total Annonces</div>
                <div class="stat-value">{{ total_annonces }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Prix Moyen</div>
                <div class="stat-value">{{ prix_moyen }} k€</div>
            </div>
            {% if surface_moyenne > 0 %}
            <div class="stat-card">
                <div class="stat-label">Surface Moyenne</div>
                <div class="stat-value">{{ surface_moyenne }} m²</div>
            </div>
            {% endif %}
            {% if bonnes_affaires > 0 %}
            <div class="stat-card">
                <div class="stat-label">Bonnes Affaires</div>
                <div class="stat-value" style="color: #51cf66;">{{ bonnes_affaires }}</div>
            </div>
            {% endif %}
            {% for type, count in types_biens.items() %}
            <div class="stat-card">
                <div class="stat-label">{{ type }}</div>
                <div class="stat-value">{{ count }}</div>
            </div>
            {% endfor %}
        </div>

        <div class="filters">
            <div class="filter-group">
                <input type="text" id="filtreVille" class="filter-input" placeholder="🔍 Filtrer par ville...">
                <select id="filtreType" class="filter-input">
                    <option value="">Tous les types</option>
                    {% for type in types_biens.keys() %}
                    <option value="{{ type }}">{{ type }}</option>
                    {% endfor %}
                </select>
                <input type="number" id="filtrePrixMin" class="filter-input" placeholder="Prix min (€)">
                <input type="number" id="filtrePrixMax" class="filter-input" placeholder="Prix max (€)">
                <button class="btn" onclick="appliquerFiltres()">Filtrer</button>
                <button class="btn" onclick="reinitialiserFiltres()" style="background: #999;">Réinitialiser</button>
            </div>
        </div>

        <div class="annonces-grid" id="annoncesGrid">
            {% for annonce in annonces %}
            <div class="annonce-card" data-ville="{{ annonce.ville }}" data-type="{{ annonce.type_bien }}" data-prix="{{ annonce.prix_euros }}">
                <div class="annonce-image">
                    {% if annonce.photo %}
                        <img src="{{ annonce.photo }}" alt="{{ annonce.titre }}" onerror="this.parentElement.innerHTML='🏠'">
                    {% else %}
                        🏠
                    {% endif %}
                </div>
                <div class="annonce-content">
                    <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px;">
                        <span class="annonce-type">{{ annonce.type_bien }}</span>
                        
                        {% if annonce.gamme_prix %}
                        <span class="badge badge-info">{{ annonce.gamme_prix }}</span>
                        {% endif %}
                        
                        {% if annonce.bonne_affaire == 'True' or annonce.bonne_affaire == True %}
                        <span class="badge badge-success">💰 Bonne affaire</span>
                        {% endif %}
                        
                        {% if annonce.donnees_completes == 'True' or annonce.donnees_completes == True %}
                        <span class="badge badge-info">✓ Complet</span>
                        {% endif %}
                    </div>
                    
                    <h3 class="annonce-titre">{{ annonce.titre }}</h3>
                    <p class="annonce-ville">📍 {{ annonce.ville }}</p>
                    
                    {% if annonce.score_completude %}
                    <div style="margin: 15px 0;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.85em; color: #666; margin-bottom: 5px;">
                            <span>Score complétude</span>
                            <span><strong>{{ annonce.score_completude }}%</strong></span>
                        </div>
                        <div class="score-bar">
                            <div class="score-fill" style="width: {{ annonce.score_completude }}%"></div>
                        </div>
                    </div>
                    {% endif %}
                    
                    <div class="annonce-details">
                        {% if annonce.surface_m2 %}
                        <span class="detail-item">📏 {{ annonce.surface_m2 }} m²</span>
                        {% endif %}
                        {% if annonce.nombre_pieces %}
                        <span class="detail-item">🛏️ {{ annonce.nombre_pieces }} pièces</span>
                        {% endif %}
                    </div>

                    <div class="annonce-prix">{{ annonce.prix_display }}</div>
                    
                    {% if annonce.date_extraction %}
                    <div style="font-size: 0.8em; color: #999; margin: 10px 0;">
                        📅 Extrait le {{ annonce.date_formatted }}
                    </div>
                    {% endif %}

                    <div class="annonce-footer">
                        <a href="{{ annonce.url }}" target="_blank" class="voir-plus">Voir l'annonce →</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="no-results">
            <h2>😔 Aucune annonce trouvée</h2>
            <p>Vérifiez que le fichier CSV existe dans le même dossier que app.py</p>
            <p><strong>Fichiers CSV recherchés :</strong></p>
            <ul style="list-style: none; margin-top: 10px;">
                <li>✓ annonces_nettoyees.csv</li>
                <li>✓ citya_*.csv</li>
                <li>✓ *.csv</li>
            </ul>
        </div>
        {% endif %}
    </div>

    <script>
        function appliquerFiltres() {
            const ville = document.getElementById('filtreVille').value.toLowerCase();
            const type = document.getElementById('filtreType').value;
            const prixMin = parseInt(document.getElementById('filtrePrixMin').value) || 0;
            const prixMax = parseInt(document.getElementById('filtrePrixMax').value) || Infinity;

            const cards = document.querySelectorAll('.annonce-card');
            let visibleCount = 0;

            cards.forEach(card => {
                const cardVille = card.getAttribute('data-ville').toLowerCase();
                const cardType = card.getAttribute('data-type');
                const cardPrix = parseInt(card.getAttribute('data-prix'));

                const matchVille = !ville || cardVille.includes(ville);
                const matchType = !type || cardType === type;
                const matchPrix = cardPrix >= prixMin && cardPrix <= prixMax;

                if (matchVille && matchType && matchPrix) {
                    card.style.display = 'block';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            if (visibleCount === 0) {
                document.getElementById('annoncesGrid').innerHTML = '<div class="no-results">😔 Aucune annonce ne correspond à vos critères</div>';
            }
        }

        function reinitialiserFiltres() {
            document.getElementById('filtreVille').value = '';
            document.getElementById('filtreType').value = '';
            document.getElementById('filtrePrixMin').value = '';
            document.getElementById('filtrePrixMax').value = '';
            
            const cards = document.querySelectorAll('.annonce-card');
            cards.forEach(card => {
                card.style.display = 'block';
            });
        }

        document.getElementById('filtreVille').addEventListener('input', appliquerFiltres);
    </script>
</body>
</html>
"""

def trouver_fichier_csv():
    """Trouve automatiquement le fichier CSV d'annonces"""
    # Chemin spécifique d'abord
    chemin_specifique = r'D:\PMN_2025\Pipeline_Immo\Data_Cleaner\citya_immobilier_clean.csv'
    
    if os.path.exists(chemin_specifique):
        print(f"✅ Fichier CSV trouvé: {chemin_specifique}")
        return chemin_specifique
    
    # Sinon chercher dans le dossier courant
    patterns = [
        'citya_immobilier_clean.csv',
        'annonces_nettoyees.csv',
        'citya_*.csv',
        'annonces_*.csv',
        '*.csv'
    ]
    
    for pattern in patterns:
        fichiers = glob.glob(pattern)
        if fichiers:
            fichier = max(fichiers, key=os.path.getmtime)
            print(f"✅ Fichier CSV trouvé: {fichier}")
            return fichier
    
    print("❌ Aucun fichier CSV trouvé")
    return None

def charger_annonces_csv():
    """Charge les annonces depuis le fichier CSV"""
    fichier = trouver_fichier_csv()
    if not fichier:
        return []
    
    try:
        annonces = []
        with open(fichier, 'r', encoding='utf-8-sig') as f:
            # Détecter le séparateur
            premiere_ligne = f.readline()
            f.seek(0)
            separateur = ';' if ';' in premiere_ligne else ','
            
            reader = csv.DictReader(f, delimiter=separateur)
            for row in reader:
                annonces.append(row)
        
        print(f"✅ {len(annonces)} annonces chargées depuis {fichier}")
        return annonces
    except Exception as e:
        print(f"❌ Erreur chargement CSV: {e}")
        return []

def nettoyer_valeur(valeur):
    """Nettoie une valeur (gère None, NaN, etc.)"""
    if valeur is None or valeur == '' or str(valeur).lower() in ['nan', 'none', 'null']:
        return None
    return str(valeur).strip()

def format_prix(prix):
    """Formate un prix pour l'affichage"""
    try:
        prix_num = int(float(prix))
        return f"{prix_num:,}".replace(',', ' ') + " €"
    except:
        return str(prix)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Vérifier les identifiants
        if username in UTILISATEURS and UTILISATEURS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            print(f"✅ Connexion réussie: {username}")
            return redirect(url_for('index'))
        else:
            print(f"❌ Échec de connexion pour: {username}")
            return render_template_string(
                LOGIN_TEMPLATE,
                error="Nom d'utilisateur ou mot de passe incorrect"
            )
    
    # Si déjà connecté, rediriger vers le dashboard
    if session.get('logged_in'):
        return redirect(url_for('index'))
    
    return render_template_string(LOGIN_TEMPLATE, error=None)

@app.route('/logout')
def logout():
    """Déconnexion"""
    username = session.get('username', 'Unknown')
    session.clear()
    print(f"👋 Déconnexion: {username}")
    return redirect(url_for('login'))

@app.route('/')
def index():
    """Page d'accueil (protégée)"""
    # Vérifier si l'utilisateur est connecté
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username', 'Utilisateur')
    annonces_brutes = charger_annonces_csv()
    
    if not annonces_brutes:
        return render_template_string(
            TEMPLATE,
            annonces=[],
            total_annonces=0,
            prix_moyen='0',
            surface_moyenne=0,
            types_biens={}
        )
    
    # Traiter les annonces
    annonces = []
    prix_list = []
    surface_list = []
    types_count = {}
    bonnes_affaires = 0
    
    for row in annonces_brutes:
        # Adapter les noms de colonnes (flexible)
        annonce = {
            'url': nettoyer_valeur(row.get('url', '')),
            'titre': nettoyer_valeur(row.get('titre_original') or row.get('titre', 'Sans titre')),
            'ville': nettoyer_valeur(row.get('ville', 'Ville inconnue')),
            'code_postal': nettoyer_valeur(row.get('code_postal', '')),
            'type_bien': nettoyer_valeur(row.get('type_bien', 'Autre')),
            'prix_euros': nettoyer_valeur(row.get('prix_euros') or row.get('prix_num') or row.get('prix', '0')),
            'surface_m2': nettoyer_valeur(row.get('surface_m2', '')),
            'nombre_pieces': nettoyer_valeur(row.get('nombre_pieces', '')),
            'photo': nettoyer_valeur(row.get('url_photo_principale') or row.get('photo', '')),
            
            # Nouvelles colonnes
            'gamme_prix': nettoyer_valeur(row.get('gamme_prix', '')),
            'score_completude': nettoyer_valeur(row.get('score_completude', '')),
            'bonne_affaire': nettoyer_valeur(row.get('bonne_affaire', '')),
            'donnees_completes': nettoyer_valeur(row.get('donnees_completes', '')),
            'date_extraction': nettoyer_valeur(row.get('date_extraction', ''))
        }
        
        # Format d'affichage du prix
        try:
            prix_num = float(annonce['prix_euros'])
            if prix_num >= 1000:  # Prix en milliers
                annonce['prix_display'] = f"{int(prix_num):,}".replace(',', ' ') + " k€"
            else:
                annonce['prix_display'] = f"{int(prix_num * 1000):,}".replace(',', ' ') + " €"
            
            if prix_num > 0:
                prix_list.append(prix_num)
        except:
            annonce['prix_display'] = 'Prix non disponible'
        
        # Surface
        try:
            if annonce['surface_m2']:
                surface = float(annonce['surface_m2'])
                if surface > 0:
                    surface_list.append(surface)
        except:
            pass
        
        # Formater le score de complétude
        try:
            if annonce['score_completude']:
                annonce['score_completude'] = float(annonce['score_completude'])
        except:
            annonce['score_completude'] = None
        
        # Formater la date
        try:
            if annonce['date_extraction']:
                from datetime import datetime
                dt = datetime.fromisoformat(annonce['date_extraction'].replace('Z', '+00:00'))
                annonce['date_formatted'] = dt.strftime('%d/%m/%Y à %H:%M')
        except:
            annonce['date_formatted'] = ''
        
        # Compter les bonnes affaires
        if str(annonce['bonne_affaire']).lower() in ['true', '1', 'yes']:
            bonnes_affaires += 1
        
        # Compter les types
        type_bien = annonce['type_bien'] or 'Autre'
        types_count[type_bien] = types_count.get(type_bien, 0) + 1
        
        annonces.append(annonce)
    
    # Calculer les stats
    prix_moyen = int(sum(prix_list) / len(prix_list)) if prix_list else 0
    surface_moyenne = int(sum(surface_list) / len(surface_list)) if surface_list else 0
    
    return render_template_string(
        TEMPLATE,
        annonces=annonces,
        total_annonces=len(annonces),
        prix_moyen=int(sum(prix_list) / len(prix_list)) if prix_list else 0,
        surface_moyenne=surface_moyenne,
        types_biens=types_count,
        username=username,
        bonnes_affaires=bonnes_affaires
    )

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DÉMARRAGE DE L'APPLICATION FLASK (CSV)")
    print("="*60)
    print("\n📂 Recherche du fichier CSV...")
    
    fichier = trouver_fichier_csv()
    if fichier:
        print(f"\n✅ Application prête!")
        print(f"\n🌐 Ouvrez votre navigateur sur:")
        print(f"   👉 http://localhost:5001")
        print(f"   👉 http://127.0.0.1:5001")
        print("\n⏹️  Pour arrêter: Ctrl+C\n")
    else:
        print("\n⚠️  ATTENTION: Aucun fichier CSV trouvé!")
        print("   Placez votre fichier CSV dans le même dossier que app.py\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)