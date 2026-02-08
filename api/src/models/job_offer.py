"""
Modèle SQLAlchemy pour job_offers
Correspond exactement au schema PostgreSQL existant
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from sqlalchemy.sql import text
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from .database import Base

class JobOffer(Base):
    """
    Modèle SQLAlchemy pour table job_offers
    """
    __tablename__ = "job_offers"
    
    id = Column(Integer, primary_key=True, index=True)
    job_url = Column(Text, unique=True, nullable=False, index=True)
    title = Column(Text, nullable=False)
    company = Column(Text, nullable=False, index=True)
    location = Column(Text, index=True)
    description = Column(Text)
    source = Column(Text, default='emploitogo.info', index=True)
    scraped_at = Column(DateTime, default=func.now())
    
    # Champs two-phase scraping
    has_full_description = Column(Boolean, default=False, index=True)
    detail_extracted_at = Column(DateTime)
    extraction_error = Column(Text)
    
    # Champs futurs pour matching
    skills_text = Column(Text)
    contract_type = Column(Text)
    salary_range = Column(Text)
    experience_level = Column(Text)
    
    # Embedding fields (futures)
    embedding_description = Column(Text)
    embedding_skills = Column(Text)
    
    # Métadonnées
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# Pydantic models pour API validation et sérialisation
class JobOfferBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    source: str = 'emploitogo.info'
    
class JobOfferCreate(JobOfferBase):
    job_url: str

class JobOfferResponse(JobOfferBase):
    """
    Réponse API pour une offre d'emploi
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    job_url: str
    scraped_at: datetime
    has_full_description: bool = False
    detail_extracted_at: Optional[datetime] = None
    extraction_error: Optional[str] = None
    skills_text: Optional[str] = None
    contract_type: Optional[str] = None
    salary_range: Optional[str] = None
    experience_level: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class JobOfferSummary(BaseModel):
    """
    Réponse API allégée pour listes
    """
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    company: str
    location: Optional[str] = None
    source: str
    scraped_at: datetime
    has_full_description: bool = False

class JobStats(BaseModel):
    """
    Statistiques de la base de données
    """
    total_jobs: int
    jobs_with_full_description: int
    jobs_basic_only: int
    jobs_with_errors: int
    completion_percentage: float
    sources_breakdown: dict
    latest_scrape: Optional[datetime] = None