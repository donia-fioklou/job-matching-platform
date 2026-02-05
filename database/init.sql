-- Base de données simple pour job matching
-- Une seule table job_offers avec l'essentiel

CREATE TABLE IF NOT EXISTS job_offers (
    id SERIAL PRIMARY KEY,
    job_url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    scraped_at TIMESTAMP DEFAULT NOW(),
    
    -- Préparation future pour matching (vides pour l'instant)
    skills_text TEXT,
    embedding_description TEXT  -- Stockage JSON temporaire pour les embeddings futurs
);

-- Index basique pour déduplication et recherche
CREATE INDEX IF NOT EXISTS idx_job_offers_url ON job_offers(job_url);
CREATE INDEX IF NOT EXISTS idx_job_offers_company ON job_offers(company);
CREATE INDEX IF NOT EXISTS idx_job_offers_scraped_at ON job_offers(scraped_at);