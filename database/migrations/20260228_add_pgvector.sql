-- Add pgvector support and vector columns
-- NOTE: Update dimensions if you use a different embedding model.

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE job_offers
    ADD COLUMN IF NOT EXISTS embedding_description VECTOR(512);

-- Index for similarity search (cosine)
CREATE INDEX IF NOT EXISTS idx_job_offers_embedding_description
ON job_offers USING ivfflat (embedding_description vector_cosine_ops)
WITH (lists = 100);
