import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.linkextractors import LinkExtractor
import json
import re
from datetime import datetime


class CityaSpider(scrapy.Spider):
    name = 'immo_scrapy'
    allowed_domains = ['citya.com']
    
    # URLs de départ - vous pouvez en ajouter d'autres
    start_urls = [
        'https://www.citya.com/annonces/vente',
        # 'https://www.citya.com/annonces/location',
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Générer le nom de fichier avec la date
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.custom_settings = {
            'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'ROBOTSTXT_OBEY': True,
            'CONCURRENT_REQUESTS': 4,
            'DOWNLOAD_DELAY': 2,
            'COOKIES_ENABLED': True,
            'HTTPCACHE_ENABLED': True,
            'FEEDS': {
                f'../Pipeline_Immo/Data_Immo/Data_Init/citya_scrapy_data.json': {
                    'format': 'json',
                    'encoding': 'utf8',
                    'indent': 2,
                    'overwrite': True,
                }
            }
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # LinkExtractor pour trouver les annonces
        self.link_extractor = LinkExtractor(
            allow=[r'/annonce/', r'/bien/', r'/vente/', r'/location/'],
            deny=[r'/mentions-legales', r'/contact', r'/nous-contacter']
        )
    
    def parse(self, response):
        """Parser la liste des annonces"""
        self.logger.info(f'Parsing: {response.url}')
        
        # Extraire tous les liens vers les annonces
        selecteurs_cartes = [
            '.property-card a::attr(href)',
            '.listing-card a::attr(href)',
            'article a::attr(href)',
            'a[href*="/annonce/"]::attr(href)',
            'a[href*="/bien/"]::attr(href)',
            '[class*="Card"] a::attr(href)',
            '[data-testid*="listing"] a::attr(href)',
        ]
        
        liens_trouves = set()
        for selecteur in selecteurs_cartes:
            liens = response.css(selecteur).getall()
            liens_trouves.update(liens)
        
        # Utiliser aussi le LinkExtractor
        for link in self.link_extractor.extract_links(response):
            liens_trouves.add(link.url)
        
        # Suivre chaque lien d'annonce
        for lien in liens_trouves:
            yield response.follow(lien, callback=self.parse_annonce)
        
        # Pagination - chercher le lien "suivant"
        selecteurs_next = [
            'a[rel="next"]::attr(href)',
            'a[class*="next"]::attr(href)',
            '.pagination a:last-child::attr(href)',
            'button[aria-label*="suivant"]::attr(href)',
            'a[title*="Suivant"]::attr(href)',
        ]
        
        for selecteur in selecteurs_next:
            next_page = response.css(selecteur).get()
            if next_page:
                self.logger.info(f'Page suivante trouvée: {next_page}')
                yield response.follow(next_page, callback=self.parse)
                break
    
    def parse_annonce(self, response):
        """Parser une annonce individuelle"""
        self.logger.info(f'Scraping annonce: {response.url}')
        
        # Créer le dictionnaire de données
        data = {
            'url': response.url,
            'date_extraction': datetime.now().isoformat(),
        }
        
        # Définir tous les sélecteurs possibles pour chaque champ
        mappings = {
            'titre': [
                'h1::text',
                '.property-title::text',
                '[class*="Title"]::text',
                'header h1::text',
                'h1[class*="heading"]::text',
            ],
            'prix': [
                '.price::text',
                '[class*="Price"]::text',
                '[class*="prix"]::text',
                'span[class*="amount"]::text',
                '[data-testid*="price"]::text',
                'strong[class*="price"]::text',
            ],
            'type_bien': [
                '.property-type::text',
                '[class*="Type"]::text',
                '[class*="category"]::text',
                'span[class*="type"]::text',
            ],
            'surface': [
                '[class*="surface"]::text',
                '[class*="area"]::text',
                '[class*="size"]::text',
                '[class*="Surface"]::text',
            ],
            'pieces': [
                '[class*="room"]::text',
                '[class*="piece"]::text',
                '[data-testid*="room"]::text',
                'span[class*="rooms"]::text',
            ],
            'chambres': [
                '[class*="bedroom"]::text',
                '[class*="chambre"]::text',
                '[class*="Bedroom"]::text',
            ],
            'ville': [
                '.city::text',
                '[class*="City"]::text',
                '[class*="ville"]::text',
                '.location::text',
                '[class*="locality"]::text',
            ],
            'code_postal': [
                '[class*="postal"]::text',
                '[class*="zip"]::text',
                '.zipcode::text',
                '[class*="postcode"]::text',
            ],
            'description': [
                '.description::text',
                '[class*="Description"]::text',
                'article p::text',
                '.details::text',
                'div[class*="description"] p::text',
            ],
            'reference': [
                '[class*="ref"]::text',
                '.reference::text',
                '[class*="Reference"]::text',
                'span[class*="ref"]::text',
            ],
            'dpe': [
                '[class*="dpe"]::text',
                '[class*="energy"]::text',
                '.energy-class::text',
                '[data-testid*="dpe"]::text',
            ],
            'ges': [
                '[class*="ges"]::text',
                '[class*="emission"]::text',
                '.emission-class::text',
                '[data-testid*="ges"]::text',
            ],
            'etage': [
                '[class*="floor"]::text',
                '[class*="etage"]::text',
                '[class*="Floor"]::text',
            ],
            'loyer': [
                '[class*="rent"]::text',
                '[class*="loyer"]::text',
                '[class*="Rent"]::text',
            ],
            'charges': [
                '[class*="charges"]::text',
                '[class*="fees"]::text',
                '[class*="Charges"]::text',
            ],
            'annee_construction': [
                '[class*="year"]::text',
                '[class*="annee"]::text',
                '[class*="construction"]::text',
            ],
        }
        
        # Extraire chaque champ
        for champ, selecteurs in mappings.items():
            for selecteur in selecteurs:
                valeur = response.css(selecteur).get()
                if valeur:
                    data[champ] = valeur.strip()
                    break
        
        # Extraire la description (peut être sur plusieurs balises)
        if 'description' not in data:
            desc_parts = response.css('.description::text, [class*="Description"]::text').getall()
            if desc_parts:
                data['description'] = ' '.join([p.strip() for p in desc_parts if p.strip()])
        
        # Extraire toutes les photos
        selecteurs_images = [
            'img[class*="property"]::attr(src)',
            '.gallery img::attr(src)',
            '[class*="Gallery"] img::attr(src)',
            'img[class*="slider"]::attr(src)',
            'picture img::attr(src)',
            '[class*="Image"] img::attr(src)',
            'img[class*="photo"]::attr(src)',
        ]
        
        photos = set()
        for selecteur in selecteurs_images:
            images = response.css(selecteur).getall()
            for img in images:
                # Filtrer les vraies photos (pas les icônes)
                if img and 'http' in img and not any(x in img.lower() for x in ['logo', 'icon', 'avatar']):
                    photos.add(img)
        
        if photos:
            data['photos'] = list(photos)
            data['nombre_photos'] = len(photos)
        
        # Extraire les caractéristiques/équipements
        selecteurs_features = [
            '.features li::text',
            '.caracteristiques li::text',
            '[class*="feature"] li::text',
            'ul[class*="amenities"] li::text',
            '.details li::text',
            '[class*="equipment"] li::text',
        ]
        
        caracteristiques = []
        for selecteur in selecteurs_features:
            items = response.css(selecteur).getall()
            caracteristiques.extend([item.strip() for item in items if item.strip()])
        
        if caracteristiques:
            data['caracteristiques'] = list(set(caracteristiques))
        
        # Extraire les informations supplémentaires depuis le texte
        texte_complet = ' '.join(response.css('body::text').getall())
        
        # Chercher des patterns spécifiques
        patterns = {
            'balcon': r'balcon',
            'terrasse': r'terrasse',
            'jardin': r'jardin',
            'parking': r'parking|garage',
            'ascenseur': r'ascenseur',
            'cave': r'cave',
            'piscine': r'piscine',
        }
        
        for key, pattern in patterns.items():
            if re.search(pattern, texte_complet, re.IGNORECASE):
                if key not in data:
                    data[key] = 'Oui'
        
        # Nettoyer les données vides
        data = {k: v for k, v in data.items() if v}
        
        yield data


def run_spider():
    """Lancer le spider Scrapy"""
    process = CrawlerProcess()
    process.crawl(CityaSpider)
    process.start()


if __name__ == '__main__':
    print("=" * 60)
    print("SCRAPING CITYA.COM - VERSION SCRAPY")
    print("=" * 60)
    print("\nDémarrage du spider...")
    print("Les données seront exportées dans 'citya_scrapy_data.json'\n")
    
    try:
        run_spider()
    except KeyboardInterrupt:
        print("\n\nInterruption par l'utilisateur")
    except Exception as e:
        print(f"\n\nErreur: {e}")
    
    print("\nScraping terminé!")