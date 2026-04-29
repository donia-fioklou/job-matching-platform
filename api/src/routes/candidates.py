"""
Routes candidats — matching CV (PDF) / offres d'emploi + inscription
Pipeline : extraction PDF → profil Gemini → vector search DB ‖ JSearch live → re-ranking Gemini
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..models.candidate import Candidate
from ..models.database import get_db
from ..services.jsearch_service import search_fresh_jobs
from ..services.llm_service import extract_cv_profile, rerank_jobs
from ..services.matching_service import embed_text, extract_text_from_pdf, find_matching_jobs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/candidates", tags=["Candidates"])

MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


# ── Schémas de réponse ────────────────────────────────────────────────────────

class MatchedJob(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    source: str
    job_url: str
    scraped_at: Optional[datetime]
    has_full_description: bool
    contract_type: Optional[str]
    experience_level: Optional[str]
    salary_range: Optional[str]
    score: float
    ai_match_reason: Optional[str] = None   # Explication Gemini
    source_type: str = "database"           # "database" | "live_search"


class MatchResponse(BaseModel):
    cv_text_preview: str
    total_matched: int
    jobs: List[MatchedJob]
    cv_profile: Optional[dict] = None       # Profil structuré extrait par Gemini


# ── Endpoint /match ───────────────────────────────────────────────────────────

@router.post(
    "/match",
    response_model=MatchResponse,
    summary="Matcher un CV (PDF) avec les offres d'emploi",
)
async def match_cv(
    file: UploadFile = File(..., description="CV au format PDF (max 5 Mo)"),
    top_k: int = Query(10, ge=1, le=50, description="Nombre d'offres à retourner"),
    min_score: float = Query(0.2, ge=0.0, le=1.0, description="Score minimum de similarité"),
    db: Session = Depends(get_db),
):
    """
    Upload un CV PDF et retourne les offres les plus compatibles.

    **Pipeline en 3 étapes :**
    1. Gemini extrait un profil structuré (titre, compétences, localisation)
    2. En parallèle : recherche vectorielle en DB  +  JSearch live (offres fraîches)
    3. Gemini re-classe l'ensemble et ajoute une explication par offre

    Si Gemini ou JSearch ne sont pas configurés, l'étape est ignorée gracieusement.
    """
    # ── Validation fichier ────────────────────────────────────────────────────
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Le fichier dépasse la limite de 5 Mo.")

    # ── Étape 1 : Extraction texte ────────────────────────────────────────────
    try:
        cv_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # ── Étape 2 : Profil structuré via Gemini (non bloquant) ─────────────────
    try:
        profile = await asyncio.to_thread(extract_cv_profile, cv_text)
    except Exception as e:
        logger.warning(f"CV profile extraction skipped: {e}")
        profile = {}

    # ── Étape 3 : Embedding avec job_title enrichi ────────────────────────────
    job_title = profile.get("job_title", "")
    try:
        cv_embedding = embed_text(cv_text, job_title=job_title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur embedding : {e}")

    # ── Étape 4 : Recherche parallèle DB + JSearch ───────────────────────────
    # On demande top_k*2 en DB pour donner plus de choix au re-ranker
    location = profile.get("location", "")

    try:
        db_jobs, live_jobs = await asyncio.gather(
            asyncio.to_thread(
                find_matching_jobs, db, cv_embedding,
                top_k=min(top_k * 2, 40), min_score=min_score
            ),
            search_fresh_jobs(job_title, location, top_k=10),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche : {e}")

    all_jobs = db_jobs + live_jobs
    if not all_jobs:
        return MatchResponse(
            cv_text_preview=cv_text[:500] + ("..." if len(cv_text) > 500 else ""),
            total_matched=0,
            jobs=[],
            cv_profile=profile or None,
        )

    # ── Étape 5 : Re-ranking Gemini ───────────────────────────────────────────
    try:
        ranked = await asyncio.to_thread(rerank_jobs, cv_text, profile, all_jobs, top_k)
    except Exception as e:
        logger.warning(f"Reranking skipped: {e}")
        ranked = sorted(all_jobs, key=lambda x: x.get("score", 0), reverse=True)[:top_k]

    return MatchResponse(
        cv_text_preview=cv_text[:500] + ("..." if len(cv_text) > 500 else ""),
        total_matched=len(ranked),
        jobs=ranked,
        cv_profile=profile or None,
    )


# ── Endpoint /register ────────────────────────────────────────────────────────

class RegisterResponse(BaseModel):
    id: int
    message: str


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Inscrire un candidat (profil + CV) dans Supabase",
)
async def register_candidate(
    name:      str        = Form(...),
    job_title: str        = Form(""),
    city:      str        = Form(""),
    email:     str        = Form(""),
    phone:     str        = Form(""),
    file:      UploadFile = File(..., description="CV au format PDF (max 5 Mo)"),
    db:        Session    = Depends(get_db),
):
    """
    Enregistre un candidat dans Supabase :
    - Sauvegarde le profil (nom, métier, ville, email, téléphone)
    - Extrait le texte du CV et génère son embedding
    - Upsert sur l'email (met à jour si déjà inscrit)
    """
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Le fichier dépasse la limite de 5 Mo.")

    try:
        cv_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    try:
        cv_embedding = embed_text(cv_text, job_title=job_title)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur embedding : {e}")

    vector_list = cv_embedding.tolist()

    existing = db.query(Candidate).filter(Candidate.email == email).first() if email else None

    if existing:
        existing.name         = name
        existing.job_title    = job_title
        existing.city         = city
        existing.phone        = phone
        existing.cv_text      = cv_text
        existing.cv_embedding = vector_list
        db.commit()
        db.refresh(existing)
        return RegisterResponse(id=existing.id, message="Profil mis à jour.")
    else:
        candidate = Candidate(
            name=name,
            job_title=job_title,
            city=city,
            email=email or None,
            phone=phone or None,
            cv_text=cv_text,
            cv_embedding=vector_list,
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)
        return RegisterResponse(id=candidate.id, message="Candidat enregistré.")
