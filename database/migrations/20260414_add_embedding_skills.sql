-- Migration: Ajout colonne embedding_skills (VECTOR 512)
-- Aligne la DB avec le modèle SQLAlchemy JobOffer
-- Modèle: distiluse-base-multilingual-cased (512 dimensions)

ALTER TABLE job_offers
    ADD COLUMN IF NOT EXISTS embedding_skills VECTOR(512);

-- Index vectoriel cosine pour recherche par compétences
CREATE INDEX IF NOT EXISTS idx_job_offers_embedding_skills
ON job_offers USING ivfflat (embedding_skills vector_cosine_ops)
WITH (lists = 100);
