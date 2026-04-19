-- Schema PostgreSQL pour Job Matching Platform
-- Architecture Two-Phase : Base Jobs + Detailed Descriptions

-- Extensions requises
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS job_offers (
    id SERIAL PRIMARY KEY,
    job_url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    source TEXT DEFAULT 'emploitogo.info',  -- Source du scraping
    scraped_at TIMESTAMP DEFAULT NOW(),
    
    -- Nouveaux champs pour architecture two-phase
    has_full_description BOOLEAN DEFAULT FALSE,
    detail_extracted_at TIMESTAMP,
    extraction_error TEXT,
    
    -- Futurs champs pour matching et analyse
    skills_text TEXT,
    contract_type TEXT,
    salary_range TEXT,
    experience_level TEXT,
    
    -- Champs pour embedding et matching
    embedding_description VECTOR(512),
    
    -- Métadonnées
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index pour performance et monitoring two-phase
CREATE INDEX IF NOT EXISTS idx_job_offers_url ON job_offers(job_url);
CREATE INDEX IF NOT EXISTS idx_job_offers_company ON job_offers(company);
CREATE INDEX IF NOT EXISTS idx_job_offers_scraped_at ON job_offers(scraped_at);
CREATE INDEX IF NOT EXISTS idx_job_offers_has_full_description ON job_offers(has_full_description);
CREATE INDEX IF NOT EXISTS idx_job_offers_location ON job_offers(location);
CREATE INDEX IF NOT EXISTS idx_job_offers_source ON job_offers(source);

-- Index vectoriel pour recherche sémantique (cosine)
CREATE INDEX IF NOT EXISTS idx_job_offers_embedding_description
ON job_offers USING ivfflat (embedding_description vector_cosine_ops)
WITH (lists = 100);

-- Vue pour monitoring des phases de scraping
CREATE OR REPLACE VIEW scraping_stats AS 
SELECT 
    COUNT(*) as total_jobs,
    COUNT(CASE WHEN has_full_description = true THEN 1 END) as jobs_with_full_description,
    COUNT(CASE WHEN has_full_description = false OR has_full_description IS NULL THEN 1 END) as jobs_basic_only,
    COUNT(CASE WHEN extraction_error IS NOT NULL THEN 1 END) as jobs_with_errors,
    ROUND(
        COUNT(CASE WHEN has_full_description = true THEN 1 END) * 100.0 / COUNT(*), 2
    ) as full_description_rate,
    MAX(scraped_at) as last_scraping,
    MAX(detail_extracted_at) as last_detail_extraction
FROM job_offers;