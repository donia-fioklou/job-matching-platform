"""
Scraper simple pour emploitogo.info avec architecture two-phase
Phase 1: Extraction URLs et métadonnées de base
Phase 2: Extraction descriptions détaillées
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def scrape_emploi_togo():
    """Phase 1: Scrape la liste et retourne URLs + métadonnées de base."""
    
    url = "https://www.emploitogo.info/offres-emploi/?show_results=1&query=&location=togo"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        job_containers = soup.find_all('div', class_='wpjb-grid-row')
        
        jobs = []
        
        for container in job_containers:
            try:
                # Extraction basique + URL détail
                title_elem = container.find('a')
                company_elem = container.find('span', class_='wpjb-company_name') 
                location_elem = container.find('span', class_='wpjb-icon-location')
                
                if not title_elem or not company_elem:
                    continue
                    
                # URL pour phase 2 (description détaillée)
                detail_url = title_elem.get('href', '')
                if detail_url and not detail_url.startswith('http'):
                    detail_url = 'https://www.emploitogo.info' + detail_url
                
                # Métadonnées de base pour déduplication immediate
                job = {
                    'job_url': detail_url,  # URL unique pour déduplication
                    'detail_url': detail_url,  # URL pour phase 2
                    'title': title_elem.text.strip(),
                    'company': company_elem.text.strip(),
                    'location': location_elem.text.strip() if location_elem else '',
                    'description': f"[SNIPPET] {title_elem.text.strip()} chez {company_elem.text.strip()}",  # Temporaire
                    'scraped_at': datetime.now(),
                    'has_full_description': False  # Flag pour tracking
                }
                
                jobs.append(job)
                
            except Exception as e:
                print(f"Erreur parsing offre: {e}")
                continue
        
        print(f"Phase 1: Scraped {len(jobs)} job URLs from emploitogo.info")
        return jobs
        
    except Exception as e:
        print(f"Erreur scraping: {e}")
        raise

def extract_job_details(job_urls):
    """Phase 2: Extraction descriptions détaillées depuis les URLs."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    detailed_jobs = []
    
    for i, url in enumerate(job_urls):
        try:
            print(f"Extracting details {i+1}/{len(job_urls)}: {url[:60]}...")
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # PLACEHOLDER - En attente des tags HTML que vous fournirez
            # TODO: Remplacer avec les vrais sélecteurs
            full_description = extract_description_from_detail_page(soup)
            
            detailed_jobs.append({
                'job_url': url,
                'full_description': full_description,
                'has_full_description': True,
                'detail_extracted_at': datetime.now()
            })
            
            # Délai poli entre requêtes pour éviter rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"Erreur extraction détail {url}: {e}")
            # En cas d'échec, on garde une version dégradée
            detailed_jobs.append({
                'job_url': url,
                'full_description': "[ERROR] Could not extract full description",
                'has_full_description': False,
                'detail_extracted_at': datetime.now(),
                'extraction_error': str(e)
            })
            continue
    
    print(f"Phase 2: Extracted details for {len(detailed_jobs)} jobs")
    return detailed_jobs

def extract_description_from_detail_page(soup):
    """
    Extraction description depuis page détail avec sélecteur HTML spécifique.
    
    Structure HTML confirmée: 
    <div class="wpjb-text-box">
        <h3>Description</h3>
        <div class="wpjb-text">
            [description complète ici]
        </div>
    </div>
    
    Args:
        soup: BeautifulSoup object de la page détail
        
    Returns:
        str: Description complète ou message d'erreur
    """
    # Sélecteur principal identifié
    desc_element = soup.select_one('div.wpjb-text')
    
    if desc_element:
        full_description = desc_element.get_text(separator=' ', strip=True)
        # Nettoyage du contenu 
        full_description = ' '.join(full_description.split())  # Normalise les espaces
        
        if len(full_description) > 50:  # Validation minimum de contenu
            print(f"✓ Description extraite: {len(full_description)} caractères")
            return full_description
    
    print("✗ Aucune description trouvée avec le sélecteur div.wpjb-text")
    return "[NO DESCRIPTION FOUND]"