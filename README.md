# Plateforme de Matching d’Offres d’Emploi

**Auteur :** donia-fioklou

## Problématique

Les offres d’emploi sont dispersées sur de nombreux sites, et les candidats peinent à trouver celles qui correspondent réellement à leur profil.  
Comment centraliser, nettoyer, historiser et rendre consultables ces données de manière robuste, puis mettre en relation automatiquement les candidats et les offres grâce à un matching sémantique ?

## Solution : une architecture moderne de collecte, d’exposition et de matching

```mermaid
flowchart LR
    S1[Sites d'emploi] --> A[Airflow<br/>scraping]
    A --> P[(Supabase PostgreSQL<br/>+ pgvector)]
    P --> F[FastAPI<br/>API REST + matching]
    F --> W[Frontend recruteur<br/>Next.js]
    F --> M[Application mobile<br/>candidats]
    M -. CV / texte .-> F
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

La transformation prépare les offres pour un stockage exploitable et pour le matching sémantique.

| Problème constaté | Technique utilisée |
|---|---|
| Données issues de sources différentes | Normalisation des champs communs |
| Données dupliquées | Déduplication au niveau de la base Supabase |
| Données incomplètes | Conservation des champs utiles et suivi des valeurs manquantes |
| Matching candidat/offre | Champs `skills_text` et `embedding_description` (vecteur 512 dimensions) |

### Load : stocker et exposer les données

- **Problème :** les offres doivent être accessibles facilement par d’autres applications.
- **Solution :** insertion dans une base PostgreSQL gérée par Supabase, puis exposition via une API FastAPI.
- La plateforme permet :
  - de consulter les offres
  - de filtrer par entreprise, lieu ou source
  - d’accéder aux statistiques globales
  - de vérifier l’état de santé de l’API et de la base
  - de recommander des offres à un candidat grâce au matching sémantique

## Matching sémantique candidat / offre

Le matching repose sur des embeddings : le profil d’un candidat (CV ou texte libre) et chaque offre sont transformés en vecteurs, puis comparés par similarité.

### Modèle d’embedding

| Caractéristique | Valeur |
|---|---|
| Modèle | `sentence-transformers/distiluse-base-multilingual-cased` |
| Dimensions | 512 |
| Langues | Multilingue (français, anglais et 48 autres) |
| Chargement | Singleton, chargé une seule fois au démarrage de l’API |

Le chargement en singleton évite de recharger le modèle à chaque requête, ce qui garde des temps de réponse faibles.

### Pipeline de matching

```mermaid
flowchart LR
    I[CV PDF ou texte] --> E1[1. Extraction du texte brut]
    E1 --> E2[2. Embedding 512-dim]
    E2 --> E3[3. N plus proches voisins<br/>cosine via pgvector]
    E3 --> E4[4. Filtrage par score minimum]
    E4 --> E5[5. Tri décroissant par score]
    E5 --> R[Offres recommandées]
```

1. **Extraction du texte brut** : `pdfplumber` pour les CV, texte direct pour les descriptions d’offres.
2. **Génération de l’embedding** de dimension 512.
3. **Recherche des N plus proches voisins** par similarité cosine via `pgvector`.
4. **Filtrage** par score minimum.
5. **Tri décroissant** par score.

## Application mobile pour les candidats

Une application mobile est dédiée aux candidats. Elle s’appuie sur l’API FastAPI pour :

- consulter et filtrer les offres collectées
- soumettre un CV ou un texte de profil
- recevoir les offres les plus proches de leur profil, classées par score de similarité

Côté recruteurs, l’interface web `recruiter-web` (Next.js) reste le point d’accès.

## Architecture technique

- **Airflow** : orchestration des scrapers
- **Supabase PostgreSQL + pgvector** : stockage managé des offres et recherche vectorielle
- **FastAPI** : API REST pour exposer les données et le matching
- **sentence-transformers** : génération des embeddings multilingues
- **pdfplumber** : extraction du texte des CV
- **Docker Compose** : déploiement local de l’infrastructure
- **Next.js** : frontend recruteur dans `recruiter-web`
- **Application mobile** : interface dédiée aux candidats

## Structure du projet

```text
job-matching-platform/
├── scrapers/               # Scripts de collecte
├── airflow/dags/           # Orchestration Airflow (3 DAGs)
├── api/                    # FastAPI REST endpoints + matching
├── recruiter-web/          # Frontend Next.js (recruteurs)
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

> Au démarrage, l’API charge le modèle d’embedding une seule fois. Le premier lancement peut donc être plus long (téléchargement du modèle).

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

Les endpoints de matching suivent le pipeline décrit plus haut (CV ou texte en entrée, offres classées par score en sortie) ; voir `http://localhost:8000/docs` pour leur documentation à jour.

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
- les embeddings des offres sont bien générés (dimension 512) et indexés via pgvector
- le matching retourne des offres triées par score décroissant, au-dessus du score minimum

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
- amélioration du matching (pondération des compétences, réajustement du score minimum)
- notifications temps réel (nouvelles offres correspondant au profil du candidat)

## Crédit

Projet réalisé à partir d’une architecture moderne combinant Airflow, Supabase (pgvector), FastAPI et Next.js, avec un matching sémantique candidat/offre et une application mobile dédiée aux candidats.
