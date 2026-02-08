"""
Scraper pour goafricaonline.com/tg/emploi
Style simple comme scrape_emploi_togo.py - Sélecteurs CSS réels basés sur l'HTML de la page
"""

import requests
from bs4 import BeautifulSoup
import time

def scrape_goafricaonline():
    """
    Scrape goafricaonline.com/tg/emploi - Simple function style
    """
    
    # URL goafricaonline Togo
    url = "https://www.goafricaonline.com/tg/emploi"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Conteneur principal avec toute la liste des jobs
        main_container = soup.find('div', class_='grow flex flex-col gap-[16px] pt-[24px] safe-area-[20px]')
        if not main_container:
            print("Conteneur principal des jobs non trouvé")
            return []
        
        # Containers individuels des offres d'emploi
        job_containers = main_container.find_all('div', class_='relative flex flex-col gap-[24px] bg-white shadow-leo p-[24px] rounded-[8px] border border-solid border-gray-300 hover:border-brand-blue svelte-4dndt0')
        
        jobs = []
        
        for container in job_containers:
            try:
                # Titre et URL - lien principal
                title_elem = container.find('a', class_='font-bold text-20/[26.02px] text-gray-800 stretched-link hover:no-underline hover:text-link cursor-pointer [grid-area:title]')
                
                # Nom de l'entreprise 
                company_elem = container.find('div', class_='font-bold text-16/[20.82px] text-gray-800')
                
                # Localisation - div après l'icône du drapeau
                location_elem = container.find('div', class_='font-bold text-12/[18px] text-gray-800')
                
                if not title_elem or not company_elem:
                    continue
                    
                # URL de l'offre
                job_url = title_elem.get('href', '') if title_elem else ""
                if job_url and not job_url.startswith('http'):
                    job_url = 'https://www.goafricaonline.com' + job_url
                
                # Description
                description_elem = container.find('p', class_='text-14/[20px] text-gray-650 font-normal line-clamp-[9] t:line-clamp-4 overflow-wrap-anywhere')
                description = description_elem.get_text(strip=True) if description_elem else f"Offre {title_elem.get_text(strip=True)} chez {company_elem.get_text(strip=True)}"
                
                # Tags/badges pour contrat, salaire, etc.
                tag_elements = container.find_all('div', class_='ls:whitespace-nowrap flex items-center gap-[8px] text-gray-800 font-medium text-12/[18px] py-[4px] px-[12px] rounded-full bg-gray-100')
                
                skills_list = []
                contract_type = ""
                
                for tag in tag_elements:
                    tag_text = tag.get_text(strip=True)
                    # Check for contract types
                    if any(keyword in tag_text.upper() for keyword in ['CDD', 'CDI', 'FREELANCE', 'STAGE', 'TEMPS COMPLET', 'TEMPS PARTIEL']):
                        if not contract_type:  # Take first contract type found
                            contract_type = tag_text
                    # Check for experience level
                    elif 'expérience' in tag_text.lower() or 'ans' in tag_text.lower():
                        skills_list.append(tag_text)
                    # Check for salary info
                    elif any(keyword in tag_text.upper() for keyword in ['FCFA', 'F CFA', 'SALAIRE', '€', '$']):
                        skills_list.append(tag_text)
                    # Check for remote work
                    elif 'télétravail' in tag_text.lower() or 'remote' in tag_text.lower():
                        skills_list.append(tag_text)
                
                skills = ', '.join(skills_list)
                
                job = {
                    'job_url': job_url,
                    'title': title_elem.get_text(strip=True),
                    'company': company_elem.get_text(strip=True),
                    'location': location_elem.get_text(strip=True) if location_elem else 'Lomé',
                    'description': description,
                    'source': 'goafricaonline.com',
                    'skills_text': ', '.join(skills_list) if skills_list else '',
                    'contract_type': contract_type
                }
                
                jobs.append(job)
                
            except Exception as e:
                print(f"Erreur parsing offre goafricaonline: {e}")
                continue
        
        print(f"Scraped {len(jobs)} jobs from goafricaonline.com/tg/emploi")
        return jobs
        
    except Exception as e:
        print(f"Erreur scraping goafricaonline.com: {e}")
        raise

