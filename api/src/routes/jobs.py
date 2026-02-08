"""
Routes pour les offres d'emploi
Endpoints REST standards pour CRUD et recherche
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..models.database import get_db
from ..models.job_offer import JobOfferResponse, JobOfferSummary, JobStats
from ..services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("/", response_model=List[JobOfferSummary])
async def get_jobs(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer (pagination)"),
    limit: int = Query(100, ge=1, le=500, description="Nombre maximum d'éléments à retourner"),
    company: Optional[str] = Query(None, description="Filtrer par entreprise (recherche partielle)"),
    location: Optional[str] = Query(None, description="Filtrer par localisation"),
    source: Optional[str] = Query(None, description="Filtrer par source (emploi.tg, goafricaonline, etc.)"),
    has_description: Optional[bool] = Query(None, description="Filtrer par description complète disponible"),
    search: Optional[str] = Query(None, description="Recherche texte libre dans titre/description"),
    sort_by: str = Query("scraped_at", description="Champ de tri (scraped_at, title, company)"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Ordre de tri"),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des offres d'emploi avec filtres et pagination
    
    **Filtres disponibles:**
    - `company`: Recherche partielle dans le nom de l'entreprise
    - `location`: Filtrage exact par localisation
    - `source`: Filtrage par source de données
    - `has_description`: True/False pour descriptions complètes
    - `search`: Recherche texte libre dans titre et description
    
    **Tri:**
    - `sort_by`: scraped_at (défaut), title, company, created_at
    - `sort_order`: desc (défaut) ou asc
    
    **Pagination:**
    - `skip`: Position de départ (0 par défaut)
    - `limit`: Nombre max d'éléments (100 par défaut, 500 max)
    """
    try:
        jobs = JobService.get_jobs(
            db=db,
            skip=skip,
            limit=limit,
            company=company,
            location=location,
            source=source,
            has_description=has_description,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@router.get("/count")
async def count_jobs(
    company: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    has_description: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Compte le nombre total d'offres correspondant aux filtres
    Utile pour pagination frontend
    """
    try:
        count = JobService.count_jobs(
            db=db,
            company=company,
            location=location,
            source=source,
            has_description=has_description,
            search=search
        )
        return {"total": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error counting jobs: {str(e)}")

@router.get("/stats", response_model=JobStats)
async def get_statistics(db: Session = Depends(get_db)):
    """
    Statistiques globales de la base de données
    
    **Retourne:**
    - Nombre total d'offres
    - Nombre avec descriptions complètes
    - Pourcentage de completion
    - Breakdown par source
    - Date du dernier scraping
    """
    try:
        stats = JobService.get_statistics(db)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching statistics: {str(e)}")

@router.get("/distinct/{field}")
async def get_distinct_values(
    field: str,
    db: Session = Depends(get_db)
):
    """
    Récupère les valeurs distinctes d'un champ
    
    **Champs supportés:**
    - `company`: Liste des entreprises uniques
    - `location`: Liste des localisations uniques
    - `source`: Liste des sources de données
    
    Utile pour construire des filtres frontend
    """
    try:
        if field not in ["company", "location", "source"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Field '{field}' not supported. Use: company, location, source"
            )
        
        values = JobService.get_distinct_values(db, field)
        return {
            "field": field,
            "values": sorted(values),  # Tri alphabétique
            "count": len(values)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching distinct values: {str(e)}")

@router.get("/{job_id}", response_model=JobOfferResponse)
async def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Récupère une offre d'emploi spécifique par son ID
    
    **Retourne toutes les informations** disponibles pour cette offre,
    y compris la description complète si disponible.
    """
    try:
        job = JobService.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")

@router.get("/url/{job_url:path}")
async def get_job_by_url(job_url: str, db: Session = Depends(get_db)):
    """
    Récupère une offre d'emploi par son URL source
    
    **Utile pour:**
    - Éviter les doublons lors du scraping
    - Vérifier si une URL est déjà dans la base
    """
    try:
        job = JobService.get_job_by_url(db, job_url)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job with URL '{job_url}' not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job by URL: {str(e)}")