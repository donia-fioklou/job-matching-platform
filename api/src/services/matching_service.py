"""
Service de matching CV / offres d'emploi
Extraction texte PDF + embedding + recherche vectorielle cosine
"""

import pdfplumber
import numpy as np
import logging
from io import BytesIO
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Modèle chargé une seule fois au démarrage (singleton)
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Chargement du modèle d'embedding...")
        _model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased")
        logger.info("Modèle chargé.")
    return _model


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extrait le texte brut d'un fichier PDF.
    Lève ValueError si le PDF est vide ou illisible.
    """
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
            "Impossible d'extraire du texte du PDF. "
            "Le fichier est peut-être scanné (image) sans OCR."
        )
    return full_text


def embed_text(text: str) -> np.ndarray:
    """
    Génère un embedding normalisé 512-dim pour un texte donné.
    """
    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.astype(np.float32)


def find_matching_jobs(
    db: Session,
    cv_embedding: np.ndarray,
    top_k: int = 10,
    min_score: float = 0.0,
) -> List[dict]:
    """
    Recherche les offres les plus proches par cosine similarity.
    Retourne une liste de dicts avec les champs de l'offre + score.
    """
    # Convertit le vecteur numpy en liste pour pgvector
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
            1 - (embedding_description <=> :embedding::vector) AS score
        FROM job_offers
        WHERE embedding_description IS NOT NULL
        ORDER BY embedding_description <=> :embedding::vector
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
                "score": round(score, 4),
            })

    return results
