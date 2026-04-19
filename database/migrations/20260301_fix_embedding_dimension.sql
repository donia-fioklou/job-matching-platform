-- Migration: Fix embedding dimension from 768 to 512
-- Raison: Le modèle distiluse-base-multilingual-cased produit 512 dims, pas 768

-- 1. Supprimer l'index vectoriel existant (lié à la colonne)
DROP INDEX IF EXISTS idx_job_offers_embedding_description;

-- 2. Supprimer la colonne avec mauvaise dimension
ALTER TABLE job_offers DROP COLUMN IF EXISTS embedding_description;

-- 3. Recréer avec la bonne dimension (512)
ALTER TABLE job_offers ADD COLUMN embedding_description VECTOR(512);

-- 4. Recréer l'index vectoriel
CREATE INDEX IF NOT EXISTS idx_job_offers_embedding_description
ON job_offers USING ivfflat (embedding_description vector_cosine_ops)
WITH (lists = 100);
