
# CONFIGURATION DES SOURCES

SOURCES = {
    'citya': {
        'name': 'Citya Immobilier',
        'enabled': True,
        'urls': {
            'vente': 'https://www.citya.com/annonces/vente',
            'location': 'https://www.citya.com/annonces/location',
        },
        'selectors': {
            # Sélecteurs pour la liste d'annonces
            'liste': {
                'cartes': [
                    '.property-card a',
                    '.listing-card a',
                    'article a',
                    'a[href*="/annonce/"]',
                ],
                'pagination': [
                    'a[rel="next"]',
                    'a[class*="next"]',
                    '.pagination a:last-child',
                ]
            },
            # Sélecteurs pour une annonce individuelle
            'annonce': {
                'titre': ['h1', '.property-title', '[class*="Title"]'],
                'prix': ['.price', '[class*="Price"]', '[class*="prix"]'],
                'type_bien': ['.property-type', '[class*="Type"]'],
                'surface': ['[class*="surface"]', '[class*="area"]'],
                'pieces': ['[class*="room"]', '[class*="piece"]'],
                'chambres': ['[class*="bedroom"]', '[class*="chambre"]'],
                'ville': ['.city', '[class*="ville"]', '.location'],
                'code_postal': ['[class*="postal"]', '[class*="zip"]'],
                'description': ['.description', '[class*="Description"]'],
                'reference': ['[class*="ref"]', '.reference'],
                'dpe': ['[class*="dpe"]', '[class*="energy"]'],
                'ges': ['[class*="ges"]', '[class*="emission"]'],
                'photos': [
                    'img[class*="property"]',
                    '.gallery img',
                    '[class*="Gallery"] img',
                ]
            }
        }
    },
    
    'seloger': {
        'name': 'SeLoger',
        'enabled': True,
        'urls': {
            'vente': 'https://www.seloger.com/list.htm?types=1,2&natures=1,2,4',
            'location': 'https://www.seloger.com/list.htm?types=1,2&natures=1',
        },
        'selectors': {
            'liste': {
                'cartes': [
                    'article.c-pa-card a',
                    '.c-pa-link',
                    'a[data-test="sl.card"]',
                ],
                'pagination': [
                    'a[data-test="pagination-next"]',
                    '.pagination-next',
                ]
            },
            'annonce': {
                'titre': ['h1.c-pa-h1', 'h1[data-test="ad-title"]'],
                'prix': ['.c-pa-price', '[data-test="price"]'],
                'type_bien': ['.c-pa-info--label', '[data-test="property-type"]'],
                'surface': ['[data-test="surface"]', '.c-pa-criterion:has-text("m²")'],
                'pieces': ['[data-test="rooms"]', '.c-pa-criterion:has-text("pièce")'],
                'chambres': ['[data-test="bedrooms"]', '.c-pa-criterion:has-text("chambre")'],
                'ville': ['.c-pa-city', '[data-test="city"]'],
                'code_postal': ['.c-pa-zipcode', '[data-test="zipcode"]'],
                'description': ['[data-test="description"]', '.c-pa-description'],
                'reference': ['[data-test="reference"]', '.c-pa-reference'],
                'dpe': ['[data-test="dpe"]', '.c-dpe-energy'],
                'ges': ['[data-test="ges"]', '.c-dpe-emission'],
                'photos': [
                    '.c-pa-carousel img',
                    '[data-test="slider-image"]',
                ]
            }
        }
    },
    
    'leboncoin': {
        'name': 'LeBonCoin',
        'enabled': True,
        'urls': {
            'vente': 'https://www.leboncoin.fr/recherche?category=9&real_estate_type=1',
            'location': 'https://www.leboncoin.fr/recherche?category=10',
        },
        'selectors': {
            'liste': {
                'cartes': [
                    'a[data-test-id="ad"]',
                    'a.styles_advertLink__ZKVgV',
                ],
                'pagination': [
                    'button[data-test-id="next-page"]',
                    'a[title="Page suivante"]',
                ]
            },
            'annonce': {
                'titre': ['h1[data-test-id="ad-title"]', 'h1.styles_adTitle__e_p1_'],
                'prix': ['span[data-test-id="price"]', '.styles_adPrice__e_p1_'],
                'type_bien': ['[data-test-id="category"]', '.styles_category__e_p1_'],
                'surface': ['[data-test-id="surface"]', '.styles_surface__e_p1_'],
                'pieces': ['[data-test-id="rooms"]', '.styles_rooms__e_p1_'],
                'ville': ['[data-test-id="location"]', '.styles_location__e_p1_'],
                'code_postal': ['[data-test-id="zipcode"]'],
                'description': ['[data-test-id="description"]', '.styles_description__e_p1_'],
                'reference': ['[data-test-id="reference"]'],
                'photos': [
                    'img[data-test-id="image"]',
                    '.styles_image__e_p1_',
                ]
            }
        }
    },
    
    'pap': {
        'name': 'PAP (De Particulier à Particulier)',
        'enabled': True,
        'urls': {
            'vente': 'https://www.pap.fr/annonce/vente-immobiliere-g37738',
            'location': 'https://www.pap.fr/annonce/locations-g37823',
        },
        'selectors': {
            'liste': {
                'cartes': [
                    '.search-list-item a',
                    'a.item-title',
                ],
                'pagination': [
                    'a.pagination-next',
                    '.pagination .next',
                ]
            },
            'annonce': {
                'titre': ['h1.item-title', 'h1.title'],
                'prix': ['.item-price', '.price'],
                'type_bien': ['.item-type', '.property-type'],
                'surface': ['.item-surface', '.surface'],
                'pieces': ['.item-pieces', '.pieces'],
                'chambres': ['.item-chambres', '.bedrooms'],
                'ville': ['.item-ville', '.city'],
                'code_postal': ['.item-cp', '.zipcode'],
                'description': ['.item-description', '.description'],
                'reference': ['.item-reference', '.reference'],
                'photos': [
                    '.slider-container img',
                    '.gallery img',
                ]
            }
        }
    },
    
    'bienici': {
        'name': 'Bien\'ici',
        'enabled': True,
        'urls': {
            'vente': 'https://www.bienici.com/recherche/achat',
            'location': 'https://www.bienici.com/recherche/location',
        },
        'selectors': {
            'liste': {
                'cartes': [
                    'a.adCardLink',
                    '.adCard a',
                ],
                'pagination': [
                    'button[aria-label="Page suivante"]',
                    '.pagination-next',
                ]
            },
            'annonce': {
                'titre': ['h1.titleLabel', 'h1[data-test="ad-title"]'],
                'prix': ['.adPrice', '[data-test="price"]'],
                'type_bien': ['.adType', '[data-test="property-type"]'],
                'surface': ['.adSurface', '[data-test="surface"]'],
                'pieces': ['.adRooms', '[data-test="rooms"]'],
                'chambres': ['.adBedrooms', '[data-test="bedrooms"]'],
                'ville': ['.adCity', '[data-test="city"]'],
                'code_postal': ['.adZipcode', '[data-test="zipcode"]'],
                'description': ['.adDescription', '[data-test="description"]'],
                'reference': ['.adReference', '[data-test="reference"]'],
                'dpe': ['.dpeValue', '[data-test="dpe"]'],
                'ges': ['.gesValue', '[data-test="ges"]'],
                'photos': [
                    '.adPhotoSlider img',
                    '[data-test="photo"]',
                ]
            }
        }
    },
}


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_enabled_sources():
    """Retourner la liste des sources activées"""
    return {key: val for key, val in SOURCES.items() if val['enabled']}


def get_source_config(source_name):
    """Obtenir la configuration d'une source spécifique"""
    return SOURCES.get(source_name)


def get_all_urls(transaction_type='vente'):
    """Obtenir toutes les URLs pour un type de transaction"""
    urls = {}
    for source_key, source_data in get_enabled_sources().items():
        if transaction_type in source_data['urls']:
            urls[source_key] = source_data['urls'][transaction_type]
    return urls


def list_sources():
    """Afficher toutes les sources disponibles"""
    print("\n" + "=" * 70)
    print("SOURCES DE DONNÉES DISPONIBLES")
    print("=" * 70)
    
    for key, source in SOURCES.items():
        status = "✓ ACTIVÉE" if source['enabled'] else "✗ DÉSACTIVÉE"
        print(f"\n{status} - {source['name']} ({key})")
        print(f"  URLs:")
        for trans_type, url in source['urls'].items():
            print(f"    • {trans_type}: {url}")


# ============================================================================
# CONFIGURATION GÉNÉRALE
# ============================================================================

SCRAPING_CONFIG = {
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'download_delay': 2,
    'concurrent_requests': 4,
    'max_annonces_par_source': 30,
    'timeout': 10,
    'headless': True,  # Pour Selenium
    'retry_times': 3,
}


if __name__ == '__main__':
    list_sources()
    
    print("\n" + "=" * 70)
    print("URLs DE VENTE")
    print("=" * 70)
    for source, url in get_all_urls('vente').items():
        print(f"{source}: {url}")