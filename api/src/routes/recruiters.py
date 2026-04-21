"""
Routes recruteurs — matching description de poste → candidats
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional

from ..models.database import get_db
from ..models.candidate import CandidateProfile
from ..services.matching_service import embed_text

router = APIRouter(prefix="/recruiters", tags=["Recruiters"])


class RecruiterMatchRequest(BaseModel):
    job_description: str
    top_k: int = 10
    min_score: float = 0.0


class RecruiterMatchResponse(BaseModel):
    total_matched: int
    candidates: List[CandidateProfile]


@router.post(
    "/match",
    response_model=RecruiterMatchResponse,
    summary="Matcher une description de poste avec les candidats inscrits",
)
async def match_candidates(
    body: RecruiterMatchRequest,
    db: Session = Depends(get_db),
):
    """
    Prend une description de poste en texte libre et retourne les candidats
    dont le CV correspond le mieux, classés par score de similarité cosine.

    **Étapes :**
    1. Génération de l'embedding de la description de poste
    2. Recherche vectorielle cosine dans la table `candidates`
    3. Retour des profils triés par score décroissant
    """
    if not body.job_description.strip():
        raise HTTPException(status_code=400, detail="La description de poste est vide.")

    try:
        job_embedding = embed_text(body.job_description)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur embedding : {e}")

    vector_str = "[" + ",".join(str(float(x)) for x in job_embedding) + "]"

    sql = text("""
        SELECT
            id,
            name,
            job_title,
            city,
            email,
            phone,
            1 - (cv_embedding <=> CAST(:embedding AS vector)) AS score
        FROM candidates
        WHERE cv_embedding IS NOT NULL
        ORDER BY cv_embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    rows = db.execute(
        sql, {"embedding": vector_str, "top_k": body.top_k}
    ).mappings().all()

    results = []
    for row in rows:
        score = round(float(row["score"]), 4)
        if score >= body.min_score:
            results.append(
                CandidateProfile(
                    id=row["id"],
                    name=row["name"],
                    job_title=row["job_title"],
                    city=row["city"],
                    email=row["email"],
                    phone=row["phone"],
                    score=score,
                )
            )

    return RecruiterMatchResponse(total_matched=len(results), candidates=results)
