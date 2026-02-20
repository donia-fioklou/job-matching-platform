# Package scrapers - Web scrapers pour différents sites d'emploi

from .lucreatif_scraper import scrape_lucreatif, extract_job_details
from .emploi_tg_scraper import scrape_emploi_tg
from .goafricaonline_scraper import scrape_goafricaonline

__all__ = [
    'scrape_lucreatif', 
    'extract_job_details',
    'scrape_emploi_tg', 
    'scrape_goafricaonline'
]