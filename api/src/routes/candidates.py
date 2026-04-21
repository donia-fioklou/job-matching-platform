"""
Routes candidats — matching CV (PDF) / offres d'emploi + inscription
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

from ..models.database import get_db
from ..models.candidate import Candidate, CandidateProfile
from ..services.matching_service import extract_text_from_pdf, embed_text, find_matching_jobs

router = APIRouter(prefix="/candidates", tags=["Candidates"])

MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class MatchedJob(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    source: str
    job_url: str
    scraped_at: datetime
    has_full_description: bool
    contract_type: Optional[str]
    experience_level: Optional[str]
    salary_range: Optional[str]
    score: float


class MatchResponse(BaseModel):
    cv_text_preview: str
    total_matched: int
    jobs: List[MatchedJob]


@router.post("/match", response_model=MatchResponse, summary="Matcher un CV (PDF) avec les offres d'emploi")
async def match_cv(
    file: UploadFile = File(..., description="CV au format PDF (max 5 Mo)"),
    top_k: int = Query(10, ge=1, le=50, description="Nombre d'offres à retourner"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="Score minimum de similarité (0 à 1)"),
    db: Session = Depends(get_db),
):
    """
    Upload un CV au format PDF et retourne les offres d'emploi les plus compatibles,
    classées par score de similarité cosine (0 = aucune similarité, 1 = identique).

    **Étapes du matching :**
    1. Extraction du texte brut du PDF
    2. Génération d'un embedding 512-dim (modèle multilingue FR/EN)
    3. Recherche des offres les plus proches par cosine similarity (pgvector)
    """
    # Validation type MIME
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")

    # Lecture et validation taille
    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide.")
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Le fichier dépasse la limite de 5 Mo.")

    # Extraction texte
    try:
        cv_text = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Génération embedding
    try:
        cv_embedding = embed_text(cv_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de l'embedding : {e}")

    # Recherche vectorielle
    try:
        matched_jobs = find_matching_jobs(db, cv_embedding, top_k=top_k, min_score=min_score)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche : {e}")

    return MatchResponse(
        cv_text_preview=cv_text[:500] + ("..." if len(cv_text) > 500 else ""),
        total_matched=len(matched_jobs),
        jobs=matched_jobs,
    )


# ── Inscription candidat ──────────────────────────────────────────────────────

class RegisterResponse(BaseModel):
    id: int
    message: str


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="Inscrire un candidat (profil + CV) dans Supabase",
)
async def register_candidate(
    name:      str       = Form(...),
    job_title: str       = Form(""),
    city:      str       = Form(""),
    email:     str       = Form(""),
    phone:     str       = Form(""),
    file:      UploadFile = File(..., description="CV au format PDF (max 5 Mo)"),
    db:        Session   = Depends(get_db),
):
    """
    Enregistre un candidat dans la base Supabase :
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
        cv_embedding = embed_text(cv_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur embedding : {e}")

    vector_list = cv_embedding.tolist()

    # Upsert : mise à jour si l'email existe déjà
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
