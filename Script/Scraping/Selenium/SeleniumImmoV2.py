from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
import json
import time
from datetime import datetime


class CityaScraper:
    def __init__(self, headless=True):
        # Configuration Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.annonces = []
    
    def extraire_texte(self, element, selecteur):
        """Extraire du texte en gérant les erreurs"""
        try:
            return element.find_element(By.CSS_SELECTOR, selecteur).text.strip()
        except (NoSuchElementException, AttributeError):
            return None
    
    def extraire_attribut(self, element, selecteur, attribut):
        """Extraire un attribut en gérant les erreurs"""
        try:
            return element.find_element(By.CSS_SELECTOR, selecteur).get_attribute(attribut)
        except (NoSuchElementException, AttributeError):
            return None
    
    def generer_url_page(self, url_base, numero_page):
        """Génère l'URL pour une page spécifique"""
        # Format Citya: ?page=2
        if '?' in url_base:
            # Si l'URL a déjà des paramètres, ajouter &page=
            if 'page=' in url_base:
                # Remplacer le numéro de page existant
                import re
                return re.sub(r'page=\d+', f'page={numero_page}', url_base)
            else:
                return f"{url_base}&page={numero_page}"
        else:
            return f"{url_base}?page={numero_page}"
    
    def verifier_page_valide(self):
        """Vérifie si la page contient des annonces"""
        selecteurs_annonces = [
            'a[href*="/annonces/"]',
            '.property-card',
            '.listing-card',
            'article[class*="card"]',
            '[class*="Card"]',
            '[data-testid*="listing"]',
        ]
        
        for selecteur in selecteurs_annonces:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selecteur)
                if len(elements) > 0:
                    return True, len(elements)
            except:
                continue
        
        return False, 0
    
    def scraper_page_liste_auto(self, url_base, max_pages=100):
        """Scraper avec pagination automatique en générant les URLs"""
        print(f"\n{'='*60}")
        print(f"SCRAPING AVEC PAGINATION AUTOMATIQUE")
        print(f"{'='*60}")
        print(f"URL de base: {url_base}")
        print(f"Pages maximum: {max_pages}")
        
        urls_annonces = set()
        pages_vides_consecutives = 0
        max_pages_vides = 3
        
        for page_num in range(1, max_pages + 1):
            # Générer l'URL de la page
            if page_num == 1:
                url_page = url_base
            else:
                url_page = self.generer_url_page(url_base, page_num)
            
            print(f"\n{'─'*60}")
            print(f"📄 PAGE {page_num}")
            print(f"🔗 URL: {url_page}")
            print(f"{'─'*60}")
            
            try:
                self.driver.get(url_page)
                time.sleep(3)  # Attendre le chargement
                
                # Accepter les cookies si présents (seulement page 1)
                if page_num == 1:
                    try:
                        cookie_selectors = [
                            'button[id*="accept"]',
                            'button[class*="accept"]',
                            'button[id*="cookie"]',
                            '#didomi-notice-agree-button',
                            '[class*="cookie"] button',
                        ]
                        for selector in cookie_selectors:
                            try:
                                cookie_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                                if cookie_btn.is_displayed():
                                    cookie_btn.click()
                                    time.sleep(1)
                                    break
                            except:
                                continue
                    except:
                        pass
                
                # Vérifier si la page contient des annonces
                page_valide, nb_elements = self.verifier_page_valide()
                
                if not page_valide:
                    pages_vides_consecutives += 1
                    print(f"⚠️  Page vide ou invalide ({pages_vides_consecutives}/{max_pages_vides})")
                    
                    if pages_vides_consecutives >= max_pages_vides:
                        print(f"\n🏁 {max_pages_vides} pages vides consécutives détectées")
                        print("Fin de la pagination")
                        break
                    continue
                
                # Réinitialiser le compteur si la page contient des annonces
                pages_vides_consecutives = 0
                print(f"✅ {nb_elements} éléments trouvés sur la page")
                
                # Extraire les URLs des annonces
                selecteurs_liens = [
                    'a[href*="/annonces/vente/"]',
                    'a[href*="/annonces/location/"]',
                    'a[href*="/annonce/"]',
                    'a[href*="/bien/"]',
                    '.property-card a',
                    '.listing-card a',
                    'article a',
                    '[class*="Card"] a[href*="/"]'
                ]
                
                nouvelles_annonces = 0
                for selecteur in selecteurs_liens:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selecteur)
                        for elem in elements:
                            href = elem.get_attribute('href')
                            if href and 'citya.com' in href:
                                # Filtrer les URLs valides
                                if any(x in href for x in ['/annonces/', '/annonce/', '/bien/', '/vente/', '/location/']):
                                    if not any(x in href for x in ['#', 'javascript:', 'mailto:', 'tel:', '?page=']):
                                        if href not in urls_annonces:
                                            urls_annonces.add(href)
                                            nouvelles_annonces += 1
                    except:
                        continue
                
                print(f"🆕 {nouvelles_annonces} nouvelles annonces trouvées")
                print(f"📊 Total cumulé: {len(urls_annonces)} annonces")
                
                # Si aucune nouvelle annonce, c'est peut-être la fin
                if nouvelles_annonces == 0 and page_num > 1:
                    pages_vides_consecutives += 1
                    print(f"⚠️  Aucune nouvelle annonce ({pages_vides_consecutives}/{max_pages_vides})")
                
                # Pause pour éviter d'être bloqué
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Erreur sur la page {page_num}: {e}")
                pages_vides_consecutives += 1
                if pages_vides_consecutives >= max_pages_vides:
                    break
                continue
        
        print(f"\n{'='*60}")
        print(f"✅ PAGINATION TERMINÉE")
        print(f"📊 {len(urls_annonces)} annonces uniques trouvées")
        print(f"{'='*60}\n")
        
        return list(urls_annonces)
    
    def scraper_annonce(self, url):
        """Scraper une annonce individuelle"""
        print(f"  📄 Scraping: {url}")
        try:
            self.driver.get(url)
            time.sleep(2)
            
            # Dictionnaire pour stocker les données
            data = {
                'url': url,
                'date_extraction': datetime.now().isoformat(),
            }
            
            # Sélecteurs possibles pour chaque champ
            selecteurs = {
                'titre': ['h1', '.property-title', '[class*="Title"]', 'header h1'],
                'prix': ['.price', '[class*="Price"]', '[class*="prix"]', 'span[class*="amount"]'],
                'type_bien': ['.property-type', '[class*="Type"]', '[class*="category"]'],
                'surface': ['[class*="surface"]', '[class*="area"]', '[class*="size"]'],
                'pieces': ['[class*="room"]', '[class*="piece"]', '[data-testid*="room"]'],
                'chambres': ['[class*="bedroom"]', '[class*="chambre"]'],
                'ville': ['.city', '[class*="City"]', '[class*="ville"]', '.location'],
                'code_postal': ['[class*="postal"]', '[class*="zip"]', '.zipcode'],
                'description': ['.description', '[class*="Description"]', 'article p', '.details'],
                'reference': ['[class*="ref"]', '.reference', '[class*="Reference"]'],
                'dpe': ['[class*="dpe"]', '[class*="energy"]', '.energy-class'],
                'ges': ['[class*="ges"]', '[class*="emission"]', '.emission-class'],
                'etage': ['[class*="floor"]', '[class*="etage"]'],
                'ascenseur': ['[class*="elevator"]', '[class*="ascenseur"]'],
                'balcon': ['[class*="balcon"]', '[class*="balcony"]'],
                'parking': ['[class*="parking"]', '[class*="garage"]'],
                'annee_construction': ['[class*="year"]', '[class*="annee"]', '[class*="construction"]'],
            }
            
            # Extraire chaque champ avec les sélecteurs possibles
            for champ, liste_selecteurs in selecteurs.items():
                for selecteur in liste_selecteurs:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selecteur)
                        if element and element.text.strip():
                            data[champ] = element.text.strip()
                            break
                    except:
                        continue
            
           
            # Extraire les caractéristiques sous forme de liste
            caracteristiques = []
            selecteurs_features = [
                '.features li',
                '.caracteristiques li',
                '[class*="feature"] li',
                'ul[class*="amenities"] li',
                '.details li'
            ]
            
            for selecteur in selecteurs_features:
                try:
                    items = self.driver.find_elements(By.CSS_SELECTOR, selecteur)
                    for item in items:
                        text = item.text.strip()
                        if text and text not in caracteristiques:
                            caracteristiques.append(text)
                except:
                    continue
            
            if caracteristiques:
                data['caracteristiques'] = caracteristiques
            
            # Extraire le prix du loyer si c'est une location
            try:
                loyer = self.driver.find_element(By.CSS_SELECTOR, '[class*="rent"], [class*="loyer"]')
                if loyer:
                    data['loyer'] = loyer.text.strip()
            except:
                pass
            
            # Extraire les charges
            try:
                charges = self.driver.find_element(By.CSS_SELECTOR, '[class*="charges"], [class*="fees"]')
                if charges:
                    data['charges'] = charges.text.strip()
            except:
                pass
            
            # Nettoyer les données vides
            data = {k: v for k, v in data.items() if v}
            
            print(f"    ✅ {len(data)} champs extraits")
            return data
            
        except Exception as e:
            print(f"    ❌ Erreur: {e}")
            return None
    
    def scraper(self, url_base, max_pages=100, max_annonces=None):
        """Fonction principale de scraping"""
        print("\n" + "="*60)
        print("🚀 DÉMARRAGE DU SCRAPING CITYA.COM")
        print("="*60)
        
        # 1. Récupérer les URLs des annonces avec pagination automatique
        urls_annonces = self.scraper_page_liste_auto(url_base, max_pages=max_pages)
        
        if not urls_annonces:
            print("⚠️  Aucune annonce trouvée")
            return
        
        print(f"\n📋 {len(urls_annonces)} annonces à scraper")
        
        # Limiter le nombre d'annonces si spécifié
        if max_annonces:
            urls_annonces = urls_annonces[:max_annonces]
            print(f"🔒 Limitation à {max_annonces} annonces")
        
        # 2. Scraper chaque annonce
        print(f"\n{'='*60}")
        print("📥 EXTRACTION DES DÉTAILS DES ANNONCES")
        print(f"{'='*60}\n")
        
        for i, url in enumerate(urls_annonces, 1):
            print(f"[{i}/{len(urls_annonces)}]", end=" ")
            annonce_data = self.scraper_annonce(url)
            if annonce_data:
                self.annonces.append(annonce_data)
            
            # Pause entre chaque annonce
            if i < len(urls_annonces):
                time.sleep(2)
        
        print(f"\n{'='*60}")
        print(f"✅ {len(self.annonces)} annonces scrapées avec succès")
        print(f"{'='*60}")
    
    def sauvegarder_json(self, nom_fichier=None):
        """Sauvegarder les données en JSON"""
        if nom_fichier is None:
            #nom_fichier = f'citya_annonces_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            nom_fichier = f'citya_annonces.json'
        
        with open(nom_fichier, 'w', encoding='utf-8') as f:
            json.dump(self.annonces, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Données exportées dans '{nom_fichier}'")
        print(f"📊 Statistiques:")
        print(f"   - Nombre d'annonces: {len(self.annonces)}")
        if self.annonces:
            print(f"   - Champs moyens par annonce: {sum(len(a) for a in self.annonces) / len(self.annonces):.1f}")
    
    def fermer(self):
        """Fermer le navigateur"""
        self.driver.quit()


# Script principal
if __name__ == '__main__':
    # Initialiser le scraper (headless=False pour voir le navigateur)
    scraper = CityaScraper(headless=True)
    
    try:
        # Configuration
        urls = [
            {
                'url': 'https://www.citya.com/annonces/vente',
                'nom': 'Ventes',
                'max_pages': 2,  
                'max_annonces': 10  
            },
            {
                'url': 'https://www.citya.com/annonces/location',
                'nom': 'Locations',
                'max_pages': 2,
                'max_annonces': 10
            },
        ]
        
        # Scraper chaque section
        for config in urls:
            print(f"\n\n🎯 SECTION: {config['nom']}")
            scraper.scraper(
                config['url'], 
                max_pages=config['max_pages'],
                max_annonces=config.get('max_annonces')
            )
        
        # Sauvegarder en JSON
        scraper.sauvegarder_json()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
    except Exception as e:
        print(f"\n\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        scraper.fermer()
        print("\n✅ Scraping terminé!\n")