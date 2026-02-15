# Job Matching Platform - Architecture Moderne

## 🏗 **Architecture Supabase + API**

```
Sites d'emploi → Airflow (scraping) → Supabase PostgreSQL → FastAPI → Applications
```

**Pipeline moderne** :
1. **Scrapers Airflow** : emploi.tg, goafricaonline, emploi_info
2. **Base Supabase** : PostgreSQL managé avec déduplication  
3. **API FastAPI** : Endpoints REST pour exposition des données

## ⚙️ **Configuration initiale**

### **1. Setup Supabase**
```bash
# 1. Créer projet sur supabase.com
# 2. Configurer .env avec vos credentials (voir .env.example)
# 3. Initialiser le schema
python init_supabase.py
```

### **2. Démarrage des services**
```bash
# 1. Démarrer l'infrastructure
docker-compose up -d

# 2. Interfaces disponibles
# Airflow: http://localhost:8080 (admin/admin)
# API: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

## 📊 **Vérifier les données**

### **Via API REST**
```bash
# Statistiques globales
curl http://localhost:8000/jobs/stats

# 10 dernières offres
curl http://localhost:8000/jobs?limit=10&sort_order=desc

# Recherche par entreprise
curl "http://localhost:8000/jobs?company=Orange&limit=5"
```

### **Via Supabase Dashboard**
Accédez à votre projet Supabase → Table Editor → `job_offers`
## 🗂 **Structure du projet**

```
job-matching-platform/
├── scrapers/               # Scripts de collecte
├── airflow/dags/          # Orchestration (3 DAGs)
├── api/                   # FastAPI REST endpoints
├── database/init.sql      # Schema PostgreSQL
├── docker-compose.yml     # Infrastructure Supabase + API
├── init_supabase.py      # Script d'initialisation DB
└── .env                  # Configuration (à remplir)
```

## 🔗 **API Endpoints**

| Endpoint | Description | Example |
|----------|-------------|---------|
| `GET /jobs` | Liste avec filtres/pagination | `/jobs?company=Orange&limit=10` |
| `GET /jobs/{id}` | Détail d'une offre | `/jobs/123` |
| `GET /jobs/stats` | Statistiques globales | Nb total, sources, etc. |
| `GET /health` | Health checks | Status API + DB |

**Documentation interactive** : http://localhost:8000/docs

## 🚀 **Avantages de cette architecture**

- ✅ **Scalable** : Supabase gère la montée en charge
- ✅ **API REST** : Intégration facile apps/frontend  
- ✅ **Monitoring** : Health checks et statistiques
- ✅ **Moderne** : FastAPI async + PostgreSQL managé
- ✅ **Sécurisé** : SSL par défaut, credentials isolés

## 📋 **Migration & Support**

- 📖 **Guide détaillé** : [MIGRATION_SUPABASE.md](MIGRATION_SUPABASE.md)
- 🔧 **API Documentation** : [api/README.md](api/README.md)  
- ⚠️ **Troubleshooting** : Voir section dédiée dans guides

---
**🎯 Platform prête pour développement d'IA matching candidat/offre !**
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
