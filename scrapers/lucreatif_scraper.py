"""
Scraper pour lucreatif avec architecture two-phase
Phase 1: Extraction URLs et métadonnées de base depuis la liste  
Phase 2: Extraction descriptions détaillées depuis chaque page
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def scrape_single_page(page_url):
    """Scrape une seule page et retourne URLs + métadonnées de base."""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(page_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Container principal : articles avec class job_listing
        job_containers = soup.find_all('article', class_='job_listing')
        
        jobs = []
        
        for container in job_containers:
            try:
                # Extraction titre et URL depuis <h2 class="entry-title job-title"><a href="...">
                title_elem = container.find('h2', class_='entry-title job-title')
                if not title_elem:
                    continue
                
                title_link = title_elem.find('a')
                if not title_link:
                    continue
                
                detail_url = title_link.get('href', '')
                title = title_link.text.strip()
                
                # URL pour déduplication et phase 2
                if not detail_url:
                    continue
                
                # Métadonnées de base pour déduplication immédiate
                job = {
                    'job_url': detail_url,  # URL unique pour déduplication
                    'detail_url': detail_url,  # URL pour phase 2
                    'title': title,
                    'company': 'Lucreatif',  # Default company (pas disponible en liste)
                    'location': 'Non spécifié',  # Pas disponible en liste
                    'description': f"[SNIPPET] {title}",  # Description temporaire
                    'scraped_at': datetime.now(),
                    'has_full_description': False  # Flag pour tracking phase 2
                }
                
                jobs.append(job)
                
            except Exception as e:
                print(f"Erreur parsing offre: {e}")
                continue
        
        return jobs
        
    except Exception as e:
        print(f"Erreur scraping page {page_url}: {e}")
        return []


def scrape_lucreatif():
    """Phase 1: Scrape toutes les pages et retourne URLs + métadonnées de base."""
    
    base_url = "https://lucreatif.com/job-list/"
    all_jobs = []
    page = 1
    
    print("=== DEBUT PAGINATION LUCREATIF ===")
    
    while True:
        # Construction URL page
        if page == 1:
            page_url = base_url
        else:
            page_url = f"{base_url}page/{page}/"
        
        print(f"Scraping page {page}: {page_url}")
        
        # Scraping de la page
        page_jobs = scrape_single_page(page_url)
        
        # Si aucune offre trouvée, on a atteint la fin
        if not page_jobs or len(page_jobs) == 0:
            print(f"Page {page}: Aucune offre trouvée - fin de pagination")
            break
        
        # Ajouter les offres de cette page
        all_jobs.extend(page_jobs)
        print(f"Page {page}: {len(page_jobs)} offres trouvées")
        
        # Délai entre pages pour éviter surcharge serveur
        time.sleep(1)
        
        page += 1
        
        # Sécurité: limite à 20 pages max pour éviter boucle infinie
        if page > 20:
            print("Limite de 20 pages atteinte - arrêt")
            break
    
    print(f"=== FIN PAGINATION: {len(all_jobs)} offres sur {page-1} pages ===")
    return all_jobs


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
    <div class="job-detail-description">
        <h3>Job Description</h3>
        <div class="inner">
            [description complète ici]
        </div>
    </div>
    
    Args:
        soup: BeautifulSoup object de la page détail
        
    Returns:
        str: Description complète ou message d'erreur
    """
    # Sélecteur principal identifié
    desc_element = soup.select_one('div.job-detail-description div.inner')
    
    if desc_element:
        full_description = desc_element.get_text(separator=' ', strip=True)
        # Nettoyage du contenu 
        full_description = ' '.join(full_description.split())  # Normalise les espaces
        
        if len(full_description) > 50:  # Validation minimum de contenu
            print(f"✓ Description extraite: {len(full_description)} caractères")
            return full_description
    
    print("✗ Aucune description trouvée avec le sélecteur div.job-detail-description div.inner")
    return "[NO DESCRIPTION FOUND]"





