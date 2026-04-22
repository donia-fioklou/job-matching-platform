"""
Script pour régénérer les embeddings des candidats existants avec pondération du job_title.
Usage :
    python scripts/regenerate_candidate_embeddings.py
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import logging
from sqlalchemy import create_engine, select, update
from sqlalchemy.orm import sessionmaker
from src.models.candidate import Candidate
from src.services.matching_service import embed_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Récupérer l'URL de la base depuis l'env
DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("Variable d'environnement SUPABASE_DATABASE_URL ou DATABASE_URL manquante.")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

candidates = session.query(Candidate).all()
logger.info(f"{len(candidates)} candidats à traiter...")

for c in candidates:
    try:
        if not c.cv_text:
            logger.warning(f"Candidat {c.id} sans cv_text, ignoré.")
            continue
        new_emb = embed_text(c.cv_text, job_title=c.job_title)
        c.cv_embedding = new_emb.tolist()
        logger.info(f"Candidat {c.id} ({c.name}) : embedding régénéré.")
    except Exception as e:
        logger.error(f"Erreur pour candidat {c.id} : {e}")

session.commit()
logger.info("Tous les embeddings candidats ont été régénérés.")
session.close()
