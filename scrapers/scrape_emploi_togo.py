"""
Scraper simple pour emploitogo.info
Une seule fonction, gestion d'erreur basique
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime

def scrape_emploi_togo():
    """Scrape emploitogo.info et retourne les offres."""
    
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
                # Extraction basique
                title_elem = container.find('a')
                company_elem = container.find('span', class_='wpjb-company_name') 
                location_elem = container.find('span', class_='wpjb-icon-location')
                
                if not title_elem or not company_elem:
                    continue
                    
                # URL pour déduplication  
                job_url = title_elem.get('href', '')
                if job_url and not job_url.startswith('http'):
                    job_url = 'https://www.emploitogo.info' + job_url
                
                job = {
                    'job_url': job_url,
                    'title': title_elem.text.strip(),
                    'company': company_elem.text.strip(),
                    'location': location_elem.text.strip() if location_elem else '',
                    'description': f"Offre {title_elem.text.strip()} chez {company_elem.text.strip()}",
                    'scraped_at': datetime.now()
                }
                
                jobs.append(job)
                
            except Exception as e:
                print(f"Erreur parsing offre: {e}")
                continue
        
        print(f"Scraped {len(jobs)} jobs from emploitogo.info")
        return jobs
        
    except Exception as e:
        print(f"Erreur scraping: {e}")
        raise