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
    def __init__(self):
        # Configuration Chrome headless
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.annonces = []
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        #self.pathsave = 'Pipeline_Immo/Data_Immo/Data_Init/citya_scrapy_data_{date_str}.json'
    
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
    
    def scraper_page_liste(self, url, max_pages=100000): 
        """Scraper la liste des annonces et récupérer leurs URLs"""
        print(f"Accès à {url}...")
        self.driver.get(url)
        time.sleep(1)  # Attendre le chargement
        
        urls_annonces = set()
        page_actuelle = 1
        
        while page_actuelle <= max_pages:
            print(f"Scraping page {page_actuelle}...")
            
            # Accepter les cookies si présents
            try:
                cookie_btn = self.driver.find_element(By.CSS_SELECTOR, 
                    'button[class*="accept"], button[class*="cookie"], #didomi-notice-agree-button')
                cookie_btn.click()
                time.sleep(1)
            except:
                pass
            
            # Chercher tous les liens vers les annonces
            selecteurs_liens = [
                'a[href*="/annonce/"]',
                'a[href*="/bien/"]',
                'a[data-testid*="listing"]',
                '.property-card a',
                '.listing-card a',
                'article a',
                '[class*="Card"] a[href*="/"]'
            ]
            
            for selecteur in selecteurs_liens:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selecteur)
                    for elem in elements:
                        href = elem.get_attribute('href')
                        if href and 'citya.com' in href and href not in urls_annonces:
                            # Filtrer les URLs qui semblent être des annonces
                            if any(x in href for x in ['/annonce/', '/bien/', '/vente/', '/location/']):
                                if not any(x in href for x in ['#', 'javascript:', 'mailto:', 'tel:']):
                                    urls_annonces.add(href)
                except:
                    continue
            
            print(f"  -> {len(urls_annonces)} annonces trouvées jusqu'à présent")
            
            # Chercher le bouton "page suivante"
            try:
                selecteurs_next = [
                    'a[rel="next"]',
                    'button[aria-label*="suivant"]',
                    'a[class*="size-5"]',
                    '.pagination a:last-child',
                    'a[title*="suivant"]',
                ]
                
                next_button = None
                for selecteur in selecteurs_next:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, selecteur)
                        if next_button:
                            break
                    except:
                        continue
                
                if next_button and next_button.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                    time.sleep(1)
                    next_button.click()
                    time.sleep(3)
                    page_actuelle += 1
                else:
                    print("Pas de page suivante trouvée")
                    break
            except Exception as e:
                print(f"Fin de pagination: {e}")
                break
        
        return list(urls_annonces)
    
    def scraper_annonce(self, url):
        """Scraper une annonce individuelle"""
        print(f"  Scraping: {url}")
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
            
            # Extraire les photos
            photos = []
            selecteurs_images = [
                'img[class*="property"]',
                '.gallery img',
                '[class*="Gallery"] img',
                'img[class*="slider"]',
                'picture img',
                '[class*="Image"] img'
            ]
            
            for selecteur in selecteurs_images:
                try:
                    images = self.driver.find_elements(By.CSS_SELECTOR, selecteur)
                    for img in images:
                        src = img.get_attribute('src')
                        if src and 'http' in src and src not in photos:
                            photos.append(src)
                except:
                    continue
            
            if photos:
                data['photos'] = photos
                data['nombre_photos'] = len(photos)
            
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
            
            return data
            
        except Exception as e:
            print(f"    Erreur lors du scraping de {url}: {e}")
            return None
    
    def scraper(self, url_base, max_annonces=50):
        """Fonction principale de scraping"""
        print("=" * 60)
        print("DÉMARRAGE DU SCRAPING CITYA.COM")
        print("=" * 60)
        
        # 1. Récupérer les URLs des annonces
        urls_annonces = self.scraper_page_liste(url_base, max_pages=1000)
        print(f"\n{len(urls_annonces)} annonces trouvées au total")
        
        # Limiter le nombre d'annonces
        urls_annonces = list(urls_annonces)[:max_annonces]
        print(f"Scraping de {len(urls_annonces)} annonces...\n")
        
        # 2. Scraper chaque annonce
        for i, url in enumerate(urls_annonces, 1):
            print(f"[{i}/{len(urls_annonces)}]", end=" ")
            annonce_data = self.scraper_annonce(url)
            if annonce_data:
                self.annonces.append(annonce_data)
            time.sleep(5)  # Pause entre chaque requête
        
        print(f"\n{len(self.annonces)} annonces scrapées avec succès")
    
    #def sauvegarder_json(self, nom_fichier=f'citya_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json'):
    def sauvegarder_json(self, nom_fichier=f'citya_.json'):
        """Sauvegarder les données en JSON"""
        with open(nom_fichier, 'w', encoding='utf-8') as f:
            json.dump(self.annonces, f, ensure_ascii=False, indent=2)
        print(f"\nDonnées exportées dans '{nom_fichier}'")
        print(f"Nombre total d'annonces: {len(self.annonces)}")
    
    def fermer(self):
        """Fermer le navigateur"""
        self.driver.quit()


# Script principal
if __name__ == '__main__':
    scraper = CityaScraper()
    
    try:
        # URLs à scraper (vous pouvez modifier selon vos besoins)
        urls = [
            'https://www.citya.com/annonces/vente',  # Ventes
             'https://www.citya.com/annonces/location',  # Locations
        ]
        
        # Scraper chaque section
        for url in urls:
            scraper.scraper(url, max_annonces=5)
        
        # Sauvegarder en JSON
        scraper.sauvegarder_json()
        
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur")
    except Exception as e:
        print(f"\n\nErreur: {e}")
    finally:
        scraper.fermer()
        print("\nScraping terminé!")