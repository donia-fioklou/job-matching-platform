# Job Matching Platform API

API REST FastAPI pour exposer les données d'offres d'emploi collectées au Togo.

## Architecture

```
Sites d'emploi → Airflow (scraping) → PostgreSQL → FastAPI API → Applications Frontend
```

## Endpoints principaux

### 📋 Offres d'emploi
- `GET /jobs` - Liste des offres avec filtres et pagination
- `GET /jobs/{id}` - Détail d'une offre spécifique
- `GET /jobs/stats` - Statistiques globales
- `GET /jobs/count` - Comptage avec filtres
- `GET /jobs/distinct/{field}` - Valeurs distinctes (company, location, source)

### 🔍 Filtres disponibles
- `company` : Recherche partielle entreprise
- `location` : Localisation exacte  
- `source` : Source de données (emploi.tg, goafricaonline, etc.)
- `has_description` : Descriptions complètes disponibles
- `search` : Recherche texte libre titre/description
- `sort_by` / `sort_order` : Tri personnalisé

### 🏥 Health checks
- `GET /health` - Check basique
- `GET /health/database` - Vérification PostgreSQL
- `GET /health/full` - Check complet avec stats

## Démarrage rapide

```bash
# 1. Build et démarrage complet
docker-compose up -d

# 2. API disponible sur
http://localhost:8000

# 3. Documentation interactive
http://localhost:8000/docs

# 4. Airflow (si besoin de vérifier les données)
http://localhost:8080  (admin/admin)
```

## Exemples d'utilisation

### Lister les 10 dernières offres
```bash
curl "http://localhost:8000/jobs?limit=10&sort_by=scraped_at&sort_order=desc"
```

### Rechercher par entreprise
```bash
curl "http://localhost:8000/jobs?company=Orange&limit=5"
```

### Statistiques de la base
```bash
curl "http://localhost:8000/jobs/stats"
```

### Recherche texte libre
```bash
curl "http://localhost:8000/jobs?search=développeur&limit=20"
```

## Structure du projet

```
api/
├── src/
│   ├── models/          # SQLAlchemy & Pydantic models
│   ├── routes/          # FastAPI endpoints (jobs, health)
│   ├── services/        # Business logic layer
│   └── utils/           # Helpers
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── README.md           # Cette documentation
```

## Intégration avec le pipeline existant

L'API se connecte à la **même base PostgreSQL** que les scrapers Airflow:
- Table: `job_offers` 
- Connection: `postgresql://jobuser:jobpass@postgres:5432/jobmatching`
- **Aucune modification** du pipeline scraping nécessaire

## Monitoring et observabilité

### Health checks
```bash
# Check basique
curl http://localhost:8000/health

# Check base de données  
curl http://localhost:8000/health/database
```

### Métriques disponibles
- Nombre total d'offres par source
- Pourcentage de descriptions complètes
- Dernière date de scraping
- Offres avec erreurs d'extraction

## Évolutions futures prévues

1. **Authentication** : JWT tokens pour sécurisation
2. **Rate limiting** : Protection contre abus
3. **Cache Redis** : Performance requêtes fréquentes  
4. **Endpoints ML** : Embeddings, matching, recommandations
5. **WebSockets** : Notifications temps-réel nouvelles offres
6. **Export** : Formats CSV, JSON pour analyses

## Développement

### Test local (sans Docker)
```bash
cd api
pip install -r requirements.txt

# Variables d'environnement
export DATABASE_URL="postgresql://jobuser:jobpass@localhost:5433/jobmatching"
export PYTHONPATH="."

# Démarrage
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Tests API
```bash
# Health check
curl http://localhost:8000/health

# Premier test avec données
curl "http://localhost:8000/jobs?limit=5" | jq .
```