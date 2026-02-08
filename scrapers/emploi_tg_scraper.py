"""
Scraper simple pour emploi.tg
Style simple comme scrape_emploi_togo.py
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def scrape_emploi_tg():
    """
    Scrape emploi.tg - Simple function style
    """
    
    url = "https://www.emploi.tg/recherche-jobs-togo"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver le container principal des offres
        main_container = soup.find('div', class_='page-search-jobs-content')
        if not main_container:
            print("Container page-search-jobs-content not found")
            return []
        
        # Containers des offres d'emploi dans le container principal
        job_containers = main_container.find_all('div', class_='card card-job')
        
        jobs = []
        
        for container in job_containers:
            try:
                # Titre du poste
                title_elem = container.find('h3').find('a') if container.find('h3') else None
                # Entreprise
                company_elem = container.find('a', class_='card-job-company')
                
                if not title_elem or not company_elem:
                    continue
                    
                # URL de l'offre depuis data-href
                job_url = container.get('data-href', '')
                if not job_url and title_elem:
                    # Fallback vers le href du titre si pas de data-href
                    job_url = title_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = 'https://www.emploi.tg' + job_url
                
                # Description du poste
                description_elem = container.find('div', class_='card-job-description')
                if description_elem and description_elem.find('p'):
                    description = description_elem.find('p').text.strip()
                else:
                    description = f"Offre {title_elem.text.strip()} chez {company_elem.text.strip()}"
                
                # Extraire les détails depuis la liste ul li
                details = container.find('ul')
                location = ""
                contract_type = ""
                skills = ""
                
                if details:
                    for li in details.find_all('li'):
                        li_text = li.text
                        if "Région de" in li_text:
                            strong = li.find('strong')
                            location = strong.text.strip() if strong else ""
                        elif "Contrat proposé" in li_text:
                            strong = li.find('strong')
                            contract_type = strong.text.strip() if strong else ""
                        elif "Compétences clés" in li_text:
                            strong = li.find('strong')
                            skills = strong.text.strip() if strong else ""
                
                job = {
                    'job_url': job_url,
                    'title': title_elem.text.strip(),
                    'company': company_elem.text.strip(),
                    'location': location,
                    'description': description,
                    'skills': skills,
                    'contract_type': contract_type,
                    'scraped_at': datetime.now()
                }
                
                jobs.append(job)
                
            except Exception as e:
                print(f"Erreur parsing offre emploi.tg: {e}")
                continue
        
        print(f"Scraped {len(jobs)} jobs from emploi.tg")
        return jobs
        
    except Exception as e:
        print(f"Erreur scraping emploi.tg: {e}")
        raise

