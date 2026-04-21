"""
Modèle SQLAlchemy + schémas Pydantic pour la table candidates
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from pgvector.sqlalchemy import Vector
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

from .database import Base


class Candidate(Base):
    """Modèle SQLAlchemy — table candidates"""

    __tablename__ = "candidates"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(Text, nullable=False)
    job_title    = Column(Text)
    city         = Column(Text)
    email        = Column(Text, unique=True, index=True)
    phone        = Column(Text)
    cv_text      = Column(Text)
    cv_embedding = Column(Vector(512))
    created_at   = Column(DateTime, default=func.now())
    updated_at   = Column(DateTime, default=func.now(), onupdate=func.now())


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class CandidateProfile(BaseModel):
    """Profil candidat renvoyé aux recruteurs (sans données sensibles inutiles)"""

    model_config = ConfigDict(from_attributes=True)

    id:        int
    name:      str
    job_title: Optional[str]
    city:      Optional[str]
    email:     Optional[str]
    phone:     Optional[str]
    score:     float
