"""
Services métier pour gestion des offres d'emploi
Séparation claire entre routes et logique business
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, text
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.job_offer import JobOffer, JobOfferResponse, JobOfferSummary, JobStats

class JobService:
    """
    Service pour toutes les opérations sur les offres d'emploi
    """
    
    @staticmethod
    def get_jobs(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        company: Optional[str] = None,
        location: Optional[str] = None,
        source: Optional[str] = None,
        has_description: Optional[bool] = None,
        search: Optional[str] = None,
        sort_by: str = "scraped_at",
        sort_order: str = "desc"
    ) -> List[JobOfferSummary]:
        """
        Récupère les offres avec filtres et pagination
        """
        query = db.query(JobOffer)
        
        # Filtres
        if company:
            query = query.filter(JobOffer.company.ilike(f"%{company}%"))
        if location:
            query = query.filter(JobOffer.location.ilike(f"%{location}%"))
        if source:
            query = query.filter(JobOffer.source == source)
        if has_description is not None:
            query = query.filter(JobOffer.has_full_description == has_description)
        if search:
            query = query.filter(
                JobOffer.title.ilike(f"%{search}%") |
                JobOffer.description.ilike(f"%{search}%")
            )
        
        # Tri
        sort_column = getattr(JobOffer, sort_by, JobOffer.scraped_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        # Pagination
        jobs = query.offset(skip).limit(limit).all()
        
        return [JobOfferSummary.model_validate(job) for job in jobs]
    
    @staticmethod
    def get_job_by_id(db: Session, job_id: int) -> Optional[JobOfferResponse]:
        """
        Récupère une offre spécifique par ID
        """
        job = db.query(JobOffer).filter(JobOffer.id == job_id).first()
        if job:
            return JobOfferResponse.model_validate(job)
        return None
    
    @staticmethod
    def get_job_by_url(db: Session, job_url: str) -> Optional[JobOfferResponse]:
        """
        Récupère une offre par URL (utile pour éviter doublons)
        """
        job = db.query(JobOffer).filter(JobOffer.job_url == job_url).first()
        if job:
            return JobOfferResponse.model_validate(job)
        return None
    
    @staticmethod
    def count_jobs(
        db: Session,
        company: Optional[str] = None,
        location: Optional[str] = None,
        source: Optional[str] = None,
        has_description: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Compte le nombre total d'offres avec filtres
        Utile pour pagination
        """
        query = db.query(JobOffer)
        
        # Même filtres que get_jobs
        if company:
            query = query.filter(JobOffer.company.ilike(f"%{company}%"))
        if location:
            query = query.filter(JobOffer.location.ilike(f"%{location}%"))
        if source:
            query = query.filter(JobOffer.source == source)
        if has_description is not None:
            query = query.filter(JobOffer.has_full_description == has_description)
        if search:
            query = query.filter(
                JobOffer.title.ilike(f"%{search}%") |
                JobOffer.description.ilike(f"%{search}%")
            )
        
        return query.count()
    
    @staticmethod
    def get_statistics(db: Session) -> JobStats:
        """
        Génère les statistiques globales de la base
        Utilise la view scraping_stats si disponible
        """
        # Stats de base
        total_jobs = db.query(JobOffer).count()
        jobs_with_desc = db.query(JobOffer).filter(JobOffer.has_full_description == True).count()
        jobs_with_errors = db.query(JobOffer).filter(JobOffer.extraction_error.isnot(None)).count()
        
        # Breakdown par source
        sources_query = db.query(
            JobOffer.source, 
            func.count(JobOffer.id).label('count')
        ).group_by(JobOffer.source).all()
        
        sources_breakdown = {source: count for source, count in sources_query}
        
        # Dernier scraping
        latest_scrape = db.query(func.max(JobOffer.scraped_at)).scalar()
        
        # Pourcentage completion
        completion_pct = (jobs_with_desc / total_jobs * 100) if total_jobs > 0 else 0.0
        
        return JobStats(
            total_jobs=total_jobs,
            jobs_with_full_description=jobs_with_desc,
            jobs_basic_only=total_jobs - jobs_with_desc,
            jobs_with_errors=jobs_with_errors,
            completion_percentage=round(completion_pct, 2),
            sources_breakdown=sources_breakdown,
            latest_scrape=latest_scrape
        )
    
    @staticmethod
    def get_distinct_values(db: Session, field: str) -> List[str]:
        """
        Récupère les valeurs distinctes d'un champ
        Utile pour filtres frontend (companies, locations, sources)
        """
        if field == "company":
            column = JobOffer.company
        elif field == "location":
            column = JobOffer.location  
        elif field == "source":
            column = JobOffer.source
        else:
            raise ValueError(f"Field '{field}' not supported")
        
        results = db.query(column).distinct().filter(column.isnot(None)).all()
        return [result[0] for result in results if result[0]]