# Scripts d'Embeddings

Scripts pour générer et gérer les embeddings (vecteurs sémantiques) des offres d'emploi.

## Fichiers

### `embedding_generator.py`
Script principal de génération d'embeddings.

**Fonctions**
- `fill_embeddings(limit=None, batch_size=50)` : Génère les embeddings pour tous les jobs sans embeddings
- `get_jobs_without_embeddings()` : Récupère les jobs à traiter
- `generate_embeddings_batch()` : Génère les vecteurs pour un batch

**Usage standalone**
```bash
python scripts/embedding_generator.py
```

**Usage dans Airflow**
Voir `airflow/dags/daily_embedding_generation.py`

### `test_embeddings.py`
Script de test pour vérifier la configuration et traiter un petit batch.

**Usage**
```bash
python scripts/test_embeddings.py
```

## Configuration

Requiert les variables Supabase :
```
SUPABASE_DATABASE_URL=postgresql://...
# OU
SUPABASE_HOST=...
SUPABASE_PASSWORD=...
```

## Modèle d'Embeddings

Par défaut : `sentence-transformers/distiluse-base-multilingual-cased`
- Support multilingue (FR, EN)
- Dimension : 768
- Optimisé pour phrases courtes/moyennes

Modèles alternatifs :
- `distiluse-base-multilingual-cased` (768 dims, multilingue, rapide)
- `sentence-transformers/all-mpnet-base-v2` (768 dims, anglais, meilleure qualité)
- `sentence-transformers/all-MiniLM-L6-v2` (384 dims, léger)

## Performance

- Batch size : 50 descriptions
- Temps estimé : ~5 descriptions/seconde (GPU) ou ~1/seconde (CPU)
- Pour 1000 offres : ~15-20 secondes (GPU) ou 15-20 minutes (CPU)

## Airflow DAG

DAG : `daily_embedding_generation`
- Schedule : Quotidien (1 fois/jour)
- Timeout : 2 heures
- Traite tous les jobs sans embeddings en batch

Pour le déployer :
1. Assurer que `scripts/embedding_generator.py` est accessible depuis Airflow
2. Vérifier les variables Supabase dans le conteneur Airflow
3. Déclencher le DAG manuellement ou attendre l'exécution quotidienne

## Troubleshooting

**ERR: "type 'vector' does not exist"**
→ Vérifier que l'extension pgvector est créée : `CREATE EXTENSION IF NOT EXISTS vector;`

**ERR: Slow embedding generation**
→ GPU généralement 10-50x plus rapide que CPU
→ Réduire `batch_size` si problèmes RAM

**ERR: Connection timeout**
→ Vérifier la connectivité Supabase
→ Augmenter `connect_timeout` dans `embedding_generator.py`
