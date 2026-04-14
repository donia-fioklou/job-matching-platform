"""
Service de matching CV / offres d'emploi
Extraction texte PDF + embedding via HuggingFace Inference API + recherche vectorielle cosine

HF Inference API : aucun modèle chargé en mémoire localement (~0 MB RAM).
Même modèle que l'embedding_generator.py → vecteurs compatibles.
"""

import os
import pdfplumber
import numpy as np
import httpx
import logging
from io import BytesIO
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)

HF_MODEL = "sentence-transformers/distiluse-base-multilingual-cased"
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL}"


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


def embed_text(cv_text: str) -> np.ndarray:
    """
    Génère un embedding normalisé 512-dim via HuggingFace Inference API.
    Aucun modèle n'est chargé localement — économise ~500 MB de RAM.
    """
    token = os.getenv("HF_API_TOKEN")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    with httpx.Client(timeout=60.0) as client:
        response = client.post(
            HF_API_URL,
            headers=headers,
            json={"inputs": cv_text, "options": {"wait_for_model": True}},
        )

    if response.status_code == 503:
        raise RuntimeError(
            "Le modèle HuggingFace est en cours de chargement, réessaie dans quelques secondes."
        )
    response.raise_for_status()

    data = response.json()

    # L'API retourne [[float...]] pour un input unique — on prend le premier élément
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
        vector = np.array(data[0], dtype=np.float32)
    else:
        vector = np.array(data, dtype=np.float32)

    # Normalisation L2 (équivalent à normalize_embeddings=True de sentence-transformers)
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm

    return vector


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
