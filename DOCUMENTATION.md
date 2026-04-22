# Job Matching Platform — Documentation Générale

Plateforme complète de matching emploi pour le marché togolais, combinant scraping automatisé, matching IA par embeddings et interfaces mobile + web.

---

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Composants](#composants)
   - [API FastAPI](#api-fastapi)
   - [Airflow (Scrapers)](#airflow-scrapers)
   - [Application Mobile Flutter](#application-mobile-flutter)
   - [Application Web Recruteurs (Next.js)](#application-web-recruteurs-nextjs)
   - [Base de données](#base-de-données)
4. [Endpoints API](#endpoints-api)
5. [Modèle IA](#modèle-ia)
6. [Déploiement](#déploiement)
7. [Variables d'environnement](#variables-denvironnement)
8. [Migrations](#migrations)

---

## Vue d'ensemble

```
Scrapers Airflow ──► PostgreSQL/Supabase ◄── API FastAPI ◄── App Mobile Flutter
                          (pgvector)               │
                                                   └──── App Web Recruteurs Next.js
```

**Flux candidat :**
1. Le candidat uploade son CV (PDF) dans l'app mobile
2. L'API extrait le texte, génère un embedding (512 dimensions) et retourne les offres les plus compatibles
3. Le profil et l'embedding du candidat sont enregistrés dans Supabase

**Flux recruteur :**
1. Le recruteur colle la description du poste dans l'app web
2. L'API embed la description et recherche les candidats les plus proches par similarité cosine

---

## Architecture

```
job-matching-platform/
├── api/                        # Backend FastAPI (Python)
├── airflow/                    # Orchestration des scrapers
├── mobile/                     # App Flutter (iOS/Android)
├── recruiter-web/              # App web recruteurs (Next.js)
├── database/                   # Schémas SQL et migrations
├── scrapers/                   # Scripts de scraping Python
├── scripts/                    # Génération d'embeddings
└── docker-compose.yml          # Orchestration locale
```

---

## Composants

### API FastAPI

**Répertoire :** `api/`  
**Port :** `8000`  
**URL production :** `http://95.111.244.63:8000`  
**Documentation interactive :** `http://95.111.244.63:8000/docs`

**Technologies :**
- FastAPI 0.104 + Uvicorn / Gunicorn
- SQLAlchemy 2.0 + psycopg2
- pdfplumber (extraction texte PDF)
- sentence-transformers (`distiluse-base-multilingual-cased`, 512 dim)
- pgvector (recherche vectorielle)

**Structure :**
```
api/src/
├── main.py                     # Point d'entrée, CORS, lifespan
├── models/
│   ├── database.py             # Connexion SQLAlchemy
│   ├── job_offer.py            # Modèle offres d'emploi
│   └── candidate.py            # Modèle candidats
├── routes/
│   ├── jobs.py                 # CRUD offres d'emploi
│   ├── candidates.py           # Match CV + inscription
│   ├── recruiters.py           # Match description → candidats
│   └── health.py               # Healthcheck
└── services/
    ├── matching_service.py     # Extraction PDF + embeddings
    └── job_service.py          # Logique métier offres
```

---

### Airflow (Scrapers)

**Répertoire :** `airflow/`  
**UI :** `http://95.111.244.63:8080`  
**Scheduler :** quotidien

**DAGs disponibles :**

| DAG | Source | Description |
|-----|--------|-------------|
| `emploi_tg_scraping` | emploi.tg | Offres d'emploi Togo |
| `goafricaonline_scraping` | goafricaonline.com | Offres Afrique de l'Ouest |
| `emploi_info_scraping` | emploi-info.tg | Offres locales |
| `lucreatif_scraping` | lucreatif.com | Offres créatives |
| `jsearch_etl_dag` | JSearch API | Offres internationales |
| `daily_embedding_generation` | — | Génère les embeddings des nouvelles offres |

---

### Application Mobile Flutter

**Répertoire :** `mobile/Job-Match-mobile-app-flutter/`  
**Plateformes :** Android, iOS  
**State management :** GetX  
**HTTP :** Dio  

**Fonctionnalités :**
- Onboarding : upload CV PDF → matching automatique
- Page Discover : recommandations d'offres personnalisées
- Page Favoris : sauvegarde locale (SharedPreferences)
- Page Profil : gestion CV + données personnelles
- Détail offre : description complète + bouton "Postuler" (ouvre le navigateur)

**Persistance :**
- CV copié dans `getApplicationDocumentsDirectory()` au moment du choix
- Favoris sérialisés en JSON dans SharedPreferences (`favoris_list`)
- Profil stocké dans `StorageService` (SharedPreferences)

**Inscription candidat :**  
Après chaque upload de CV réussi, l'app envoie silencieusement le profil + PDF à `POST /candidates/register` pour alimenter la base de matching recruteur.

---

### Application Web Recruteurs (Next.js)

**Répertoire :** `recruiter-web/`  
**Framework :** Next.js 16 + TypeScript + Tailwind CSS  
**Port local :** `3000`

**Fonctionnalités :**
- Formulaire de description de poste (texte libre)
- Sélection du nombre de profils (5 / 10 / 20 / 30 / 50)
- Curseur de score minimum (0–80%)
- Affichage des candidats classés par score de similarité
- Badge de score coloré (vert ≥70%, orange ≥45%, gris sinon)
- Lien mailto direct sur l'email du candidat

**Proxy API :**  
`app/api/match/route.ts` fait office de proxy server-side vers `http://95.111.244.63:8000/recruiters/match` pour éviter les problèmes CORS.

---

### Base de données

**Hébergement :** Supabase (PostgreSQL + extension pgvector)

**Tables principales :**

#### `job_offers`
| Colonne | Type | Description |
|---------|------|-------------|
| `id` | SERIAL | Clé primaire |
| `job_url` | TEXT UNIQUE | URL source (déduplication) |
| `title` | TEXT | Intitulé du poste |
| `company` | TEXT | Nom de l'entreprise |
| `location` | TEXT | Localisation |
| `description` | TEXT | Description complète |
| `source` | TEXT | Source du scraping |
| `embedding_description` | VECTOR(512) | Embedding pour matching |
| `contract_type` | TEXT | CDI / CDD / Stage… |
| `experience_level` | TEXT | Junior / Senior… |

#### `candidates`
| Colonne | Type | Description |
|---------|------|-------------|
| `id` | SERIAL | Clé primaire |
| `name` | TEXT | Nom complet |
| `job_title` | TEXT | Métier / poste recherché |
| `city` | TEXT | Ville |
| `email` | TEXT UNIQUE | Email (clé de déduplication) |
| `phone` | TEXT | Téléphone |
| `cv_text` | TEXT | Texte extrait du CV |
| `cv_embedding` | VECTOR(512) | Embedding pour matching recruteur |
| `created_at` | TIMESTAMP | Date d'inscription |

**Index vectoriels :**
```sql
-- Offres d'emploi
CREATE INDEX ON job_offers USING hnsw (embedding_description vector_cosine_ops);

-- Candidats
CREATE INDEX ON candidates USING hnsw (cv_embedding vector_cosine_ops);
```

---

## Endpoints API

### Offres d'emploi

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/jobs` | Liste paginée des offres |
| `GET` | `/jobs/{id}` | Détail d'une offre |
| `GET` | `/jobs/search` | Recherche par mot-clé |

### Candidats

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/candidates/match` | Upload PDF → retourne les offres compatibles |
| `POST` | `/candidates/register` | Inscription candidat (profil + CV) |

**`POST /candidates/match`** — multipart/form-data :
```
file      : PDF (max 5 Mo)
top_k     : int (défaut: 10)
min_score : float 0.0–1.0 (défaut: 0.0)
```

**`POST /candidates/register`** — multipart/form-data :
```
name      : string (requis)
job_title : string
city      : string
email     : string (clé upsert)
phone     : string
file      : PDF (requis)
```

### Recruteurs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/recruiters/match` | Description de poste → candidats compatibles |

**`POST /recruiters/match`** — JSON :
```json
{
  "job_description": "string",
  "top_k": 10,
  "min_score": 0.0
}
```

### Santé

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/health` | Statut de l'API et de la DB |

---

## Modèle IA

**Modèle :** `sentence-transformers/distiluse-base-multilingual-cased`  
**Dimensions :** 512  
**Langues :** multilingue (français, anglais, et 48 autres)  
**Chargement :** singleton, chargé une seule fois au démarrage de l'API  

**Pipeline de matching :**
1. Extraction du texte brut (pdfplumber pour CV, texte direct pour descriptions)
2. Génération de l'embedding 512-dim
3. Recherche des N plus proches voisins par **similarité cosine** via pgvector
4. Filtrage par score minimum
5. Tri décroissant par score

---

## Déploiement

### VPS Contabo (`95.111.244.63`)

```bash
# Connexion
ssh root@95.111.244.63
cd /root/job-matching-platform

# Mettre à jour et redéployer
git pull origin main
./deploy.sh pull

# Ou manuellement :
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

**Services Docker :**
- `api` — FastAPI sur le port 8000
- `airflow-webserver` — UI Airflow sur le port 8080
- `airflow-scheduler` — Planificateur des DAGs
- `postgres` — PostgreSQL pour les métadonnées Airflow

### Recruiter Web (local / à déployer)

```bash
cd recruiter-web
npm install
npm run dev       # Développement → http://localhost:3000
npm run build     # Build production
npm start         # Serveur production
```

---

## Variables d'environnement

Fichier `.env` à la racine du projet :

```env
# Supabase (base de données principale)
SUPABASE_DATABASE_URL=postgresql://...
SUPABASE_HOST=...
SUPABASE_PORT=5432
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=...

# Next.js Recruiter Web (optionnel, défaut: http://95.111.244.63:8000)
API_URL=http://95.111.244.63:8000
```

---

## Migrations

Les migrations SQL sont dans `database/migrations/`, à exécuter via le **Supabase SQL Editor** ou `psql` :

```bash
psql "$SUPABASE_DATABASE_URL" -f database/migrations/<fichier>.sql
```

| Fichier | Description |
|---------|-------------|
| `database/init.sql` | Schéma initial (table `job_offers`, extension vector) |
| `20260228_add_pgvector.sql` | Activation pgvector |
| `20260301_fix_embedding_dimension.sql` | Correction dimension 512 |
| `20260414_add_embedding_skills.sql` | Colonne `embedding_skills` |
| `20260421_add_candidates_table.sql` | Table `candidates` + index hnsw |
