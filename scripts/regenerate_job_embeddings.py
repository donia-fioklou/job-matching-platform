"""
Script pour régénérer les embeddings des offres d'emploi existantes
avec pondération forte sur la description (description x3 + title).
Usage :
    python scripts/regenerate_job_embeddings.py
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.job_offer import JobOffer
from src.services.matching_service import _get_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("Variable d'environnement SUPABASE_DATABASE_URL ou DATABASE_URL manquante.")
    sys.exit(1)


import time

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
model = _get_model()

def regenerate_job_embedding(job_id, retries=3, delay=2):
    for attempt in range(retries):
        session = Session()
        try:
            job = session.query(JobOffer).get(job_id)
            if not job or not job.description:
                logger.warning(f"Offre {job_id} sans description, ignorée.")
                session.close()
                return
            text = job.description.strip()
            if job.title and job.title.strip():
                text += job.title.strip()*10
            emb = model.encode(text, normalize_embeddings=True)
            job.embedding_description = emb.astype(float).tolist()
            session.commit()
            logger.info(f"Offre {job.id} ({job.title}) : embedding régénéré.")
            session.close()
            return
        except Exception as e:
            session.rollback()
            session.close()
            logger.error(f"Erreur pour offre {job_id} (tentative {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logger.error(f"Échec définitif pour offre {job_id} après {retries} tentatives.")

session = Session()
jobs = session.query(JobOffer.id).all()
session.close()
logger.info(f"{len(jobs)} offres à traiter...")

for (job_id,) in jobs:
    regenerate_job_embedding(job_id)

logger.info("Tous les embeddings offres ont été régénérés.")
