from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
from datetime import datetime

def initialiser_driver():
    """Initialise le driver Chrome avec les options appropriées"""
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    # Décommentez la ligne suivante pour mode sans interface
    # options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    return driver

def extraire_annonce(element):
    """Extrait les données d'une annonce"""
    try:
        annonce = {}
        
        # URL
        try:
            lien = element.find_element(By.CSS_SELECTOR, 'a')
            annonce['url'] = lien.get_attribute('href')
        except:
            annonce['url'] = ''
        
        # Titre
        try:
            titre = element.find_element(By.CSS_SELECTOR, 'h3, h2, .title, [class*="titre"]')
            annonce['titre'] = titre.text.strip()
        except:
            annonce['titre'] = ''
        
        # Prix
        try:
            prix = element.find_element(By.CSS_SELECTOR, '[class*="price"], [class*="prix"]')
            annonce['prix'] = prix.text.strip()
        except:
            annonce['prix'] = ''
        
        # Ville
        try:
            ville = element.find_element(By.CSS_SELECTOR, '[class*="city"], [class*="ville"], [class*="location"]')
            annonce['ville'] = ville.text.strip()
        except:
            annonce['ville'] = ''
        
        # GES
        try:
            ges = element.find_element(By.CSS_SELECTOR, '[class*="ges"], [class*="dpe"]')
            annonce['ges'] = ges.text.strip()
        except:
            annonce['ges'] = ''
        
        # Photos
        try:
            photos = element.find_elements(By.CSS_SELECTOR, 'img')
            annonce['photos'] = [img.get_attribute('src') for img in photos if img.get_attribute('src')]
            annonce['nombre_photos'] = len(annonce['photos'])
        except:
            annonce['photos'] = []
            annonce['nombre_photos'] = 0
        
        # Charges/mensualité
        try:
            charges = element.find_element(By.CSS_SELECTOR, '[class*="charge"], [class*="mensualite"]')
            annonce['charges'] = charges.text.strip()
        except:
            annonce['charges'] = ''
        
        annonce['date_extraction'] = datetime.now().isoformat()
        
        return annonce
    except Exception as e:
        print(f"❌ Erreur extraction annonce: {e}")
        return None

def generer_url_page(url_base, numero_page):
    """
    Génère l'URL pour une page spécifique
    Adaptez cette fonction selon le format d'URL de Citya
    """
    # Exemples de formats courants :
    
    # Format 1: ?page=2
    if '?' in url_base:
        return f"{url_base}&page={numero_page}"
    else:
        return f"{url_base}?page={numero_page}"
    
    # Format 2: /page/2
    # return f"{url_base}/page/{numero_page}"
    
    # Format 3: ?p=2
    # if '?' in url_base:
    #     return f"{url_base}&p={numero_page}"
    # else:
    #     return f"{url_base}?p={numero_page}"
    
    # Format 4: ?offset=20 (si 10 résultats par page)
    # offset = (numero_page - 1) * 10
    # if '?' in url_base:
    #     return f"{url_base}&offset={offset}"
    # else:
    #     return f"{url_base}?offset={offset}"

def page_contient_annonces(driver):
    """Vérifie si la page contient des annonces"""
    selecteurs = [
        '[class*="annonce"]',
        '[class*="card"]',
        'article',
        '[class*="listing-item"]',
        '[class*="property"]'
    ]
    
    for selecteur in selecteurs:
        elements = driver.find_elements(By.CSS_SELECTOR, selecteur)
        if elements:
            return True, len(elements)
    
    return False, 0

def scraper_page(driver, url_page):
    """Scrape une page d'annonces"""
    print(f"\n🔍 Scraping de : {url_page}")
    driver.get(url_page)
    
    # Attendre le chargement des annonces
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="annonce"], [class*="card"], article'))
        )
        time.sleep(2)  # Attente supplémentaire pour le JS
    except TimeoutException:
        print("⚠️ Timeout - Les annonces n'ont pas chargé")
        return []
    
    # Vérifier si la page contient des annonces
    contient_annonces, nb_elements = page_contient_annonces(driver)
    if not contient_annonces:
        print("❌ Aucune annonce trouvée sur cette page")
        return []
    
    # Récupérer toutes les annonces
    annonces = []
    
    # Essayer différents sélecteurs
    selecteurs = [
        '[class*="annonce"]',
        '[class*="card"]',
        'article',
        '[class*="listing-item"]',
        '[class*="property"]'
    ]
    
    elements = []
    for selecteur in selecteurs:
        elements = driver.find_elements(By.CSS_SELECTOR, selecteur)
        if elements:
            print(f"✅ {len(elements)} annonces trouvées avec le sélecteur: {selecteur}")
            break
    
    if not elements:
        print("❌ Aucune annonce trouvée")
        return []
    
    for i, element in enumerate(elements, 1):
        print(f"  📄 Extraction annonce {i}/{len(elements)}", end='\r')
        annonce = extraire_annonce(element)
        if annonce and annonce.get('url'):
            annonces.append(annonce)
    
    print(f"\n✅ {len(annonces)} annonces extraites")
    return annonces

def scraper_avec_pagination_auto(url_base, max_pages=50):
    """Scrape toutes les pages en générant automatiquement les URLs"""
    driver = initialiser_driver()
    toutes_annonces = []
    pages_vides_consecutives = 0
    max_pages_vides = 3  # Arrêter après 3 pages vides consécutives
    
    try:
        for page_num in range(1, max_pages + 1):
            print(f"\n{'='*50}")
            print(f"📄 PAGE {page_num}")
            print(f"{'='*50}")
            
            # Générer l'URL de la page
            if page_num == 1:
                url_page = url_base
            else:
                url_page = generer_url_page(url_base, page_num)
            
            # Scraper la page
            annonces = scraper_page(driver, url_page)
            
            # Vérifier si la page est vide
            if not annonces:
                pages_vides_consecutives += 1
                print(f"⚠️ Page vide ({pages_vides_consecutives}/{max_pages_vides})")
                
                if pages_vides_consecutives >= max_pages_vides:
                    print(f"\n🏁 {max_pages_vides} pages vides consécutives, fin du scraping")
                    break
            else:
                pages_vides_consecutives = 0  # Réinitialiser le compteur
                toutes_annonces.extend(annonces)
                print(f"\n📊 Total cumulé : {len(toutes_annonces)} annonces")
            
            # Pause pour éviter d'être bloqué
            time.sleep(2)
        
        if page_num >= max_pages:
            print(f"\n🛑 Limite de {max_pages} pages atteinte")
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()
    
    return toutes_annonces

def sauvegarder_json(annonces, nom_fichier='annonces_scraping.json'):
    """Sauvegarde les annonces dans un fichier JSON"""
    with open(nom_fichier, 'w', encoding='utf-8') as f:
        json.dump(annonces, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Données sauvegardées dans {nom_fichier}")

def main():
    # URL de départ (à adapter selon votre cas)
    URL_BASE = "https://www.citya.com/annonces/vente"
    
    # ⚠️ IMPORTANT : Vérifiez d'abord le format d'URL de pagination sur le site
    # Exemples :
    # - https://www.citya.com/annonces/vente?page=2
    # - https://www.citya.com/annonces/vente/page/2
    # - https://www.citya.com/annonces/vente?p=2
    
    print("🚀 Démarrage du scraping Citya avec pagination automatique\n")
    print(f"📍 URL de base : {URL_BASE}")
    print(f"📄 Nombre maximum de pages : 50")
    print(f"⏸️  Le scraping s'arrêtera après 3 pages vides consécutives\n")
    
    # Scraper avec pagination automatique
    annonces = scraper_avec_pagination_auto(URL_BASE, max_pages=50)
    
    # Sauvegarder les résultats
    if annonces:
        sauvegarder_json(annonces)
        print(f"\n✅ Scraping terminé : {len(annonces)} annonces récupérées")
    else:
        print("\n⚠️ Aucune annonce récupérée")

if __name__ == '__main__':
    main()