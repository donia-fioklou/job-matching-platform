"""
Routes recruteurs — matching description de poste → candidats
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List

from ..models.database import get_db
from ..models.candidate import CandidateProfile
from ..services.matching_service import embed_text

logger = logging.getLogger(__name__)

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

    try:
        rows = db.execute(
            sql, {"embedding": vector_str, "top_k": body.top_k}
        ).mappings().all()
    except Exception as e:
        logger.error(f"Erreur SQL match_candidates: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur base de données : {e}")

    logger.info(f"match_candidates: {len(rows)} lignes retournées, min_score={body.min_score}")

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
