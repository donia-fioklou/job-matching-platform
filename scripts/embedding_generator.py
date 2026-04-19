"""
Script de génération d'embeddings pour les descriptions d'offres d'emploi
Utilise sentence-transformers pour créer des vecteurs sémantiques
"""

import os
import logging
from typing import List, Tuple, Any
import psycopg2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BATCH_SIZE = 50  # Nombre de descriptions à traiter par batch
MODEL_NAME = "sentence-transformers/distiluse-base-multilingual-cased"  # Multilingue FR/EN
EMBEDDING_DIMENSION = 512


def get_supabase_connection():
    """Connexion à Supabase PostgreSQL"""
    database_url = os.getenv('SUPABASE_DATABASE_URL')
    
    if database_url:
        conn = psycopg2.connect(
            database_url,
            sslmode='require',
            connect_timeout=15
        )
        logger.info("✅ Connected via DATABASE_URL")
        return conn
    
    # Fallback sur variables séparées
    host = os.getenv('SUPABASE_HOST')
    port = os.getenv('SUPABASE_PORT', '5432')
    database = os.getenv('SUPABASE_DB', 'postgres')
    user = os.getenv('SUPABASE_USER', 'postgres')
    password = os.getenv('SUPABASE_PASSWORD')
    
    if not all([host, password]):
        raise ValueError("Missing SUPABASE_DATABASE_URL or SUPABASE_HOST/PASSWORD")
    
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password,
        sslmode='require',
        connect_timeout=15
    )
    
    logger.info(f"✅ Connected: {user}@{host}/{database}")
    return conn


def get_jobs_without_embeddings(
    conn: psycopg2.extensions.connection,
    limit: int = None
) -> List[Tuple[int, str]]:
    """
    Récupère les offres d'emploi sans embeddings
    Retourne: [(job_id, description), ...]
    """
    cursor = conn.cursor()
    
    query = """
        SELECT id, description
        FROM job_offers
        WHERE description IS NOT NULL
          AND LENGTH(description) > 10
          AND embedding_description IS NULL
        ORDER BY scraped_at DESC
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    
    logger.info(f"Found {len(rows)} jobs without embeddings")
    return rows


def generate_embeddings_batch(
    model: Any,
    texts: List[str]
) -> List:
    """
    Génère les embeddings pour un batch de textes
    Normalise les vecteurs pour meilleure cosine similarity
    """
    logger.info(f"Generating embeddings for {len(texts)} texts...")
    
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,  # Important pour cosine similarity
        show_progress_bar=False,
        batch_size=32
    )
    
    logger.info(f"✅ Generated {len(embeddings)} embeddings")
    return embeddings


def save_embeddings(
    conn: psycopg2.extensions.connection,
    job_embeddings: List[Tuple[int, List[float]]]
) -> int:
    """
    Sauvegarde les embeddings en base de données
    """
    cursor = conn.cursor()
    
    # Conversion en format PostgreSQL vector
    # Format: (embedding_list, job_id) pour le UPDATE
    data = [
        (str(embedding.tolist()), job_id)
        for job_id, embedding in job_embeddings
    ]
    
    query = """
        UPDATE job_offers
        SET embedding_description = %s::vector
        WHERE id = %s
    """
    
    try:
        # executemany pour UPDATE (pas execute_values qui est pour INSERT)
        cursor.executemany(query, data)
        conn.commit()
        
        count = cursor.rowcount
        logger.info(f"✅ Saved {count} embeddings to database")
        
        return count
        
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"❌ Database error: {e}")
        raise
    finally:
        cursor.close()


def fill_embeddings(limit: int = None, batch_size: int = BATCH_SIZE) -> dict:
    """
    Remplit tous les embeddings manquants
    
    Args:
        limit: Nombre max de jobs à traiter (None = tous)
        batch_size: Nombre de descriptions par batch
    
    Returns:
        dict avec statistiques (processed, saved, errors)
    """
    logger.info(f"Starting embedding generation (batch_size={batch_size})")
    logger.info(f"Model: {MODEL_NAME}")
    
    from sentence_transformers import SentenceTransformer

    # Charger le modèle
    logger.info("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    
    # Connexion DB
    conn = get_supabase_connection()
    
    # Récupérer les jobs sans embeddings
    jobs = get_jobs_without_embeddings(conn, limit=limit)
    
    if not jobs:
        logger.info("No jobs to process")
        conn.close()
        return {"processed": 0, "saved": 0, "errors": 0}
    
    stats = {"processed": 0, "saved": 0, "errors": 0}
    
    # Traiter par batch
    for i in range(0, len(jobs), batch_size):
        batch = jobs[i : i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(jobs) + batch_size - 1) // batch_size
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} jobs)...")
        
        try:
            # Extraire descriptions et IDs
            job_ids = [job[0] for job in batch]
            descriptions = [job[1] for job in batch]
            
            # Générer embeddings
            embeddings = generate_embeddings_batch(model, descriptions)
            
            # Préparer pour sauvegarde
            job_embeddings = list(zip(job_ids, embeddings))
            
            # Sauvegarder
            saved = save_embeddings(conn, job_embeddings)
            
            stats["processed"] += len(batch)
            stats["saved"] += saved
            
        except Exception as e:
            logger.error(f"❌ Error processing batch {batch_num}: {e}")
            stats["errors"] += len(batch)
            continue
    
    conn.close()
    
    logger.info("=" * 60)
    logger.info("EMBEDDING GENERATION COMPLETE")
    logger.info(f"Processed: {stats['processed']}")
    logger.info(f"Saved: {stats['saved']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("=" * 60)
    
    return stats


if __name__ == "__main__":
    # Mode standalone
    fill_embeddings()
