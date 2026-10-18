# Plateforme de Matching d’Offres d’Emploi

**Auteur :** donia-fioklou

## Problématique

Les offres d’emploi sont collectées depuis plusieurs sites, puis exposées via une API et un frontend.  
Comment centraliser, nettoyer, historiser et rendre consultables ces données de manière robuste, tout en préparant une future brique de matching entre candidats et offres ?

## Solution : une architecture moderne de collecte et d’exposition des données

```mermaid
flowchart LR
    S1[Sites d'emploi] --> A[Airflow<br/>scraping]
    A --> P[(Supabase PostgreSQL)]
    P --> F[FastAPI<br/>API REST]
    F --> W[Applications / Frontend]
```

### Extract : collecter les offres d’emploi

- **Problème :** les données sont dispersées sur plusieurs sites et doivent être récupérées automatiquement.
- **Solution :** des scrapers orchestrés par Airflow collectent les offres depuis plusieurs sources, notamment :
  - `emploi.tg`
  - `goafricaonline`
  - `emploi_info`
- Les données récupérées incluent les champs essentiels pour l’analyse et l’affichage :
  - titre
  - entreprise
  - localisation
  - description
  - source
  - date de scraping

### Transform : normaliser et préparer les données

La transformation prépare les offres pour un stockage exploitable et une utilisation future dans des fonctionnalités de matching.

| Problème constaté | Technique utilisée |
|---|---|
| Données issues de sources différentes | Normalisation des champs communs |
| Données dupliquées | Déduplication au niveau de la base Supabase |
| Données incomplètes | Conservation des champs utiles et suivi des valeurs manquantes |
| Préparation au matching futur | Prévoir des champs comme `skills_text` et `embedding_description` |

### Load : stocker et exposer les données

- **Problème :** les offres doivent être accessibles facilement par d’autres applications.
- **Solution :** insertion dans une base PostgreSQL gérée par Supabase, puis exposition via une API FastAPI.
- La plateforme permet :
  - de consulter les offres
  - de filtrer par entreprise, lieu ou source
  - d’accéder aux statistiques globales
  - de vérifier l’état de santé de l’API et de la base

## Architecture technique

- **Airflow** : orchestration des scrapers
- **Supabase PostgreSQL** : stockage managé des offres d’emploi
- **FastAPI** : API REST pour exposer les données
- **Docker Compose** : déploiement local de l’infrastructure
- **Next.js** : frontend applicatif dans `recruiter-web`

## Structure du projet

```text
job-matching-platform/
├── scrapers/               # Scripts de collecte
├── airflow/dags/           # Orchestration Airflow (3 DAGs)
├── api/                    # FastAPI REST endpoints
├── recruiter-web/          # Frontend Next.js
├── database/init.sql       # Schéma PostgreSQL
├── docker-compose.yml      # Infrastructure complète
├── init_supabase.py        # Initialisation de la base
└── .env                    # Configuration locale
```

## Exécution rapide

1. Configurer Supabase et renseigner les variables d’environnement dans `.env`.
2. Initialiser le schéma de base de données :
```bash
python init_supabase.py
```
3. Démarrer l’environnement :
```bash
docker-compose up -d
```
4. Accéder aux interfaces :
   - Airflow : `http://localhost:8080`
   - API : `http://localhost:8000/docs`
   - Health check : `http://localhost:8000/health`

## Vérification des données

### Via l’API REST

```bash
curl http://localhost:8000/jobs/stats
curl http://localhost:8000/jobs?limit=10&sort_order=desc
curl "http://localhost:8000/jobs?company=Orange&limit=5"
```

### Via Supabase

Accéder au dashboard Supabase puis ouvrir la table `job_offers` dans le Table Editor.

## Endpoints API

| Endpoint | Description |
|---|---|
| `GET /jobs` | Liste des offres avec filtres et pagination |
| `GET /jobs/{id}` | Détail d’une offre |
| `GET /jobs/stats` | Statistiques globales |
| `GET /jobs/count` | Comptage avec filtres |
| `GET /jobs/distinct/{field}` | Valeurs distinctes d’un champ |
| `GET /health` | Health check basique |
| `GET /health/database` | Vérification de la base PostgreSQL |
| `GET /health/full` | Health check complet avec métriques |

## Requêtes utiles

### Lister les dernières offres

```bash
curl "http://localhost:8000/jobs?limit=10&sort_by=scraped_at&sort_order=desc"
```

### Rechercher par entreprise

```bash
curl "http://localhost:8000/jobs?company=Orange&limit=5"
```

### Rechercher par texte libre

```bash
curl "http://localhost:8000/jobs?search=développeur&limit=20"
```

## Vérification de la qualité

Quelques points à contrôler après exécution :

- les scrapers récupèrent bien les offres depuis les sources ciblées
- la table `job_offers` est alimentée correctement
- les doublons sont gérés avant exposition
- l’API répond sur les endpoints principaux
- le health check de la base retourne un statut valide
- les données sont prêtes pour une future couche de matching sémantique

## Configuration

### Lancer l’API localement sans Docker

```bash
cd api
pip install -r requirements.txt
export DATABASE_URL="postgresql://jobuser:jobpass@localhost:5433/jobmatching"
export PYTHONPATH="."
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Démarrer le frontend Next.js

```bash
cd recruiter-web
npm install
npm run dev
```

## Évolutions futures

- ajout de nouvelles sources d’offres
- enrichissement des champs extraits
- authentification de l’API
- rate limiting
- cache Redis
- endpoints de matching par embeddings
- notifications temps réel

## Crédit

Projet réalisé à partir d’une architecture moderne combinant Airflow, Supabase, FastAPI et Next.js, avec une préparation orientée vers le matching candidat/offre.
