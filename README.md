# Job Matching Platform - Version Simple

## Architecture Ultra-Simple

```
Emploitogo.info → Airflow (1 task) → PostgreSQL
```

**Une seule tâche Airflow** qui fait tout :
1. Scrape emploitogo.info
2. Insert/Update PostgreSQL  
3. Déduplication par job_url

## Démarrage

```bash
# 1. Démarrer
docker-compose up -d

# 2. Airflow UI
http://localhost:8080 
Login: admin / admin

# 3. Activer le DAG "hourly_job_scraping"
```

## Vérifier les données

```bash
# Connexion DB
docker-compose exec postgres psql -U jobuser -d jobmatching

# Voir les jobs
SELECT title, company, scraped_at FROM job_offers ORDER BY scraped_at DESC LIMIT 10;
```

## Structure

```
job-matching-platform/
├── docker-compose.yml          # PostgreSQL + Airflow standalone
├── database/init.sql            # Une seule table job_offers
├── scrapers/scraper.py          # Script scraping simple
└── airflow/dags/simple_job_scraping.py  # DAG avec 1 tâche
```

## Base de Données

**Table unique** : `job_offers`
- `job_url` (UNIQUE) → déduplication
- `title, company, location, description` → données de base
- `scraped_at` → timestamp

**Préparation future** :
- `skills_text` → pour extraction compétences
- `embedding_description` → pour matching sémantique

## Next Steps

1. **Vérifier** que ça fonctionne
2. **Améliorer** le scraper (plus de champs)
3. **Ajouter** d'autres sources
4. **Préparer** le matching avec embeddings
