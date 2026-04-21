-- Migration : Table des candidats inscrits via l'app mobile
-- Objectif : stocker profil + embedding CV pour matching côté recruteurs

CREATE TABLE IF NOT EXISTS candidates (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    job_title       TEXT,
    city            TEXT,
    email           TEXT UNIQUE,
    phone           TEXT,

    -- Texte extrait du CV (pour affichage côté recruteur)
    cv_text         TEXT,

    -- Embedding du CV pour la recherche vectorielle (même dimension que job_offers)
    cv_embedding    VECTOR(512),

    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Index email pour déduplication rapide
CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates(email);

-- Index vectoriel cosine pour matching recruteur → candidat
CREATE INDEX IF NOT EXISTS idx_candidates_cv_embedding
    ON candidates USING ivfflat (cv_embedding vector_cosine_ops)
    WITH (lists = 50);
