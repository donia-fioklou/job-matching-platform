"""
Service de matching CV / offres d'emploi
Extraction texte PDF + embedding local (sentence-transformers) + recherche vectorielle cosine
"""

import pdfplumber
import numpy as np
import logging
from io import BytesIO
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/distiluse-base-multilingual-cased"

# Singleton : charg� une seule fois au 1er appel
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Chargement du modele {MODEL_NAME}...")
        _model = SentenceTransformer(MODEL_NAME)
        logger.info("Modele charge.")
    return _model


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        if len(pdf.pages) == 0:
            raise ValueError("Le PDF ne contient aucune page.")
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text.strip())

    full_text = "\n".join(text_parts).strip()
    if not full_text:
        raise ValueError(
            "Impossible d extraire du texte du PDF. "
            "Le fichier est peut-etre scanne (image) sans OCR."
        )
    return full_text


def embed_text(cv_text: str, job_title: str = None) -> np.ndarray:
    model = _get_model()
    if job_title and job_title.strip():
        # On donne plus de poids au titre (x3)
        text = (job_title.strip() + ". ") * 10 + cv_text
    else:
        text = cv_text
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.astype(np.float32)


def find_matching_jobs(
    db: Session,
    cv_embedding: np.ndarray,
    top_k: int = 10,
    min_score: float = 0.0,
) -> List[dict]:
    vector_str = "[" + ",".join(str(float(x)) for x in cv_embedding) + "]"

    sql = text("""
        SELECT
            id,
            title,
            company,
            location,
            source,
            job_url,
            scraped_at,
            has_full_description,
            contract_type,
            experience_level,
            salary_range,
            LEFT(description, 500) AS description,
            1 - (embedding_description <=> CAST(:embedding AS vector)) AS score
        FROM job_offers
        WHERE embedding_description IS NOT NULL
        ORDER BY embedding_description <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    rows = db.execute(sql, {"embedding": vector_str, "top_k": top_k}).mappings().all()

    results = []
    for row in rows:
        score = float(row["score"])
        if score >= min_score:
            results.append({
                "id": row["id"],
                "title": row["title"],
                "company": row["company"],
                "location": row["location"],
                "source": row["source"],
                "job_url": row["job_url"],
                "scraped_at": row["scraped_at"],
                "has_full_description": row["has_full_description"],
                "contract_type": row["contract_type"],
                "experience_level": row["experience_level"],
                "salary_range": row["salary_range"],
                "description": row["description"],
                "score": round(score, 4),
                "ai_match_reason": None,
                "source_type": "database",
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
