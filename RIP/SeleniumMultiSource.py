from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import json
import time
from datetime import datetime
import os
import sys

# Importer la configuration des sources
from RIP.sourcesConfig import SOURCES, SCRAPING_CONFIG, get_enabled_sources


class MultiSourceScraper:
    def __init__(self, sources_to_scrape=None):
        """
        Initialiser le scraper multi-sources
        
        Args:
            sources_to_scrape: Liste des sources à scraper (None = toutes les sources activées)
        """
        # Configuration Chrome
        chrome_options = Options()
        if SCRAPING_CONFIG['headless']:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument(f'user-agent={SCRAPING_CONFIG["user_agent"]}')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, SCRAPING_CONFIG['timeout'])
        
        # Déterminer les sources à scraper
        if sources_to_scrape is None:
            self.sources = get_enabled_sources()
        else:
            self.sources = {k: SOURCES[k] for k in sources_to_scrape if k in SOURCES}
        
        self.annonces = []
        self.stats = {source: {'total': 0, 'success': 0, 'errors': 0} 
                     for source in self.sources.keys()}
    
    def extraire_texte_multi(self, element, selecteurs, source_name=""):
        """Extraire du texte avec plusieurs sélecteurs"""
        for selecteur in selecteurs:
            try:
                el = element.find_element(By.CSS_SELECTOR, selecteur)
                if el and el.text.strip():
                    return el.text.strip()
            except (NoSuchElementException, AttributeError):
                continue
        return None
    
    def extraire_photos_multi(self, element, selecteurs):
        """Extraire les photos avec plusieurs sélecteurs"""
        photos = set()
        for selecteur in selecteurs:
            try:
                images = element.find_elements(By.CSS_SELECTOR, selecteur)
                for img in images:
                    src = img.get_attribute('src')
                    if src and 'http' in src:
                        # Filtrer les logos et icônes
                        if not any(x in src.lower() for x in ['logo', 'icon', 'avatar', 'placeholder']):
                            photos.add(src)
            except:
                continue
        return list(photos)
    
    def accepter_cookies(self):
        """Accepter les cookies si présents"""
        selecteurs_cookies = [
            'button[id*="accept"]',
            'button[id*="consent"]',
            'button[class*="accept"]',
            'button[class*="cookie"]',
            '#didomi-notice-agree-button',
            '.didomi-continue-without-agreeing',
            '[data-testid*="consent-accept"]',
        ]
        
        for selecteur in selecteurs_cookies:
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, selecteur)
                if btn.is_displayed():
                    btn.click()
                    time.sleep(1)
                    return True
            except:
                continue
        return False
    
    def scraper_liste_annonces(self, source_key, url, max_annonces):
        """Scraper la liste des annonces pour une source"""
        print(f"\n{'='*70}")
        print(f"Source: {SOURCES[source_key]['name']}")
        print(f"URL: {url}")
        print(f"{'='*70}")
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # Accepter les cookies
            self.accepter_cookies()
            time.sleep(1)
            
            urls_annonces = set()
            page = 1
            max_pages = 5
            
            config = SOURCES[source_key]['selectors']['liste']
            
            while page <= max_pages and len(urls_annonces) < max_annonces:
                print(f"\n  Page {page}...")
                
                # Extraire les liens des annonces
                for selecteur in config['cartes']:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selecteur)
                        for elem in elements:
                            href = elem.get_attribute('href')
                            if href and href.startswith('http'):
                                urls_annonces.add(href)
                                if len(urls_annonces) >= max_annonces:
                                    break
                    except Exception as e:
                        continue
                
                print(f"    → {len(urls_annonces)} annonces trouvées")
                
                if len(urls_annonces) >= max_annonces:
                    break
                
                # Chercher le bouton suivant
                next_found = False
                for selecteur in config['pagination']:
                    try:
                        next_btn = self.driver.find_element(By.CSS_SELECTOR, selecteur)
                        if next_btn.is_displayed() and next_btn.is_enabled():
                            self.driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                            time.sleep(1)
                            next_btn.click()
                            time.sleep(3)
                            next_found = True
                            break
                    except:
                        continue
                
                if not next_found:
                    print("    → Pas de page suivante")
                    break
                
                page += 1
            
            return list(urls_annonces)[:max_annonces]
            
        except Exception as e:
            print(f"  ✗ Erreur lors du scraping de la liste: {e}")
            return []
    
    def scraper_annonce(self, source_key, url):
        """Scraper une annonce individuelle"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            config = SOURCES[source_key]['selectors']['annonce']
            
            # Données de base
            data = {
                'source': source_key,
                'source_name': SOURCES[source_key]['name'],
                'url': url,
                'date_extraction': datetime.now().isoformat(),
            }
            
            # Extraire chaque champ
            champs = [
                'titre', 'prix', 'type_bien', 'surface', 
                'pieces', 'chambres', 'ville', 'code_postal',
                'description', 'reference', 'dpe', 'ges'
            ]
            
            for champ in champs:
                if champ in config:
                    valeur = self.extraire_texte_multi(
                        self.driver,
                        config[champ],
                        source_key
                    )
                    if valeur:
                        data[champ] = valeur
            
            # Extraire les photos
            if 'photos' in config:
                photos = self.extraire_photos_multi(self.driver, config['photos'])
                if photos:
                    data['photos'] = photos
                    data['nb_photos'] = len(photos)
            
            self.stats[source_key]['success'] += 1
            return data
            
        except Exception as e:
            print(f"    ✗ Erreur: {str(e)[:50]}")
            self.stats[source_key]['errors'] += 1
            return None
    
    def scraper_source(self, source_key, transaction_type='vente', max_annonces=5):
        """Scraper une source complète"""
        if source_key not in self.sources:
            print(f"✗ Source '{source_key}' non disponible")
            return
        
        source_config = self.sources[source_key]
        
        if transaction_type not in source_config['urls']:
            print(f"✗ Type de transaction '{transaction_type}' non disponible pour {source_key}")
            return
        
        url = source_config['urls'][transaction_type]
        
        # 1. Récupérer les URLs des annonces
        urls_annonces = self.scraper_liste_annonces(source_key, url, max_annonces)
        
        if not urls_annonces:
            print(f"  ✗ Aucune annonce trouvée")
            return
        
        print(f"\n  Scraping de {len(urls_annonces)} annonces...")
        self.stats[source_key]['total'] = len(urls_annonces)
        
        # 2. Scraper chaque annonce
        for i, url_annonce in enumerate(urls_annonces, 1):
            print(f"    [{i}/{len(urls_annonces)}] {url_annonce[:60]}...", end=" ")
            
            annonce = self.scraper_annonce(source_key, url_annonce)
            if annonce:
                self.annonces.append(annonce)
                print("✓")
            else:
                print("✗")
            
            time.sleep(SCRAPING_CONFIG['download_delay'])
    
    def scraper_toutes_sources(self, transaction_type='vente', max_annonces_par_source=30):
        """Scraper toutes les sources configurées"""
        print("\n" + "╔" + "="*78 + "╗")
        print("║" + " "*20 + "SCRAPING MULTI-SOURCES" + " "*36 + "║")
        print("╚" + "="*78 + "╝")
        
        print(f"\nType de transaction: {transaction_type}")
        print(f"Sources à scraper: {len(self.sources)}")
        print(f"Max annonces par source: {max_annonces_par_source}")
        
        debut = datetime.now()
        
        for source_key in self.sources.keys():
            try:
                self.scraper_source(source_key, transaction_type, max_annonces_par_source)
            except Exception as e:
                print(f"\n✗ Erreur critique pour {source_key}: {e}")
                continue
        
        fin = datetime.now()
        duree = (fin - debut).total_seconds()
        
        self.afficher_statistiques(duree)
    
    def afficher_statistiques(self, duree):
        """Afficher les statistiques du scraping"""
        print("\n" + "="*70)
        print("STATISTIQUES DU SCRAPING")
        print("="*70)
        
        total_annonces = len(self.annonces)
        print(f"\n✓ Total annonces récupérées: {total_annonces}")
        print(f"✓ Durée: {duree:.1f} secondes")
        print(f"✓ Vitesse: {total_annonces/duree:.2f} annonces/seconde")
        
        print("\n" + "-"*70)
        print(f"{'Source':<20} {'Total':<10} {'Succès':<10} {'Erreurs':<10} {'Taux':<10}")
        print("-"*70)
        
        for source_key, stats in self.stats.items():
            if stats['total'] > 0:
                taux = (stats['success'] / stats['total'] * 100)
                print(f"{SOURCES[source_key]['name']:<20} "
                      f"{stats['total']:<10} "
                      f"{stats['success']:<10} "
                      f"{stats['errors']:<10} "
                      f"{taux:.1f}%")
    
    def sauvegarder_json(self, nom_fichier=None):
        """Sauvegarder les données en JSON"""
        if nom_fichier is None:
            nom_fichier = f"./PIPELINE_IMMO/Data_Immo/Data_Init/multi_source_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Créer le dossier si nécessaire
        os.makedirs(os.path.dirname(nom_fichier), exist_ok=True)
        
        # Ajouter les métadonnées
        data_export = {
            'metadata': {
                'date_scraping': datetime.now().isoformat(),
                'nombre_annonces': len(self.annonces),
                'sources': list(self.sources.keys()),
                'statistiques': self.stats,
            },
            'annonces': self.annonces
        }
        
        with open(nom_fichier, 'w', encoding='utf-8') as f:
            json.dump(data_export, f, ensure_ascii=False, indent=2)
        
        print(f"\n✓ Données sauvegardées: {nom_fichier}")
        print(f"  Taille: {os.path.getsize(nom_fichier)/1024:.2f} KB")
    
    def fermer(self):
        """Fermer le navigateur"""
        self.driver.quit()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper multi-sources immobilier')
    
    parser.add_argument(
        '--sources',
        nargs='+',
        choices=list(SOURCES.keys()),
        help='Sources à scraper (défaut: toutes)'
    )
    
    parser.add_argument(
        '--transaction',
        choices=['vente', 'location'],
        default='vente',
        help='Type de transaction (défaut: vente)'
    )
    
    parser.add_argument(
        '--max-annonces',
        type=int,
        default=30,
        help='Nombre max d\'annonces par source (défaut: 30)'
    )
    
    parser.add_argument(
        '--output',
        help='Nom du fichier de sortie JSON'
    )
    
    args = parser.parse_args()
    
    # Créer le scraper
    scraper = MultiSourceScraper(sources_to_scrape=args.sources)
    
    try:
        # Scraper toutes les sources
        scraper.scraper_toutes_sources(
            transaction_type=args.transaction,
            max_annonces_par_source=args.max_annonces
        )
        
        # Sauvegarder
        scraper.sauvegarder_json(args.output)
        
        print("\n✅ Scraping terminé avec succès!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.fermer()