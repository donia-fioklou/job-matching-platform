#!/usr/bin/env python3
"""
Script de test pour générer les embeddings localement
Utile pour vérifier que tout fonctionne avant déploiement sur Airflow
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire scripts au path
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from embedding_generator import fill_embeddings


def test_embedding_generation():
    """
    Test la génération d'embeddings
    Traite un petit batch pour vérifier
    """
    print("=" * 60)
    print("EMBEDDING GENERATION TEST")
    print("=" * 60)
    
    # Load .env si présent
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        from pathlib import Path
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ Loaded .env variables")
    
    # Check configuration
    host = os.getenv('SUPABASE_HOST')
    if host:
        print(f"✅ Supabase host: {host}")
    else:
        print("❌ SUPABASE_HOST not set")
        return
    
    # Tester avec un petit batch (5 jobs)
    print("\nTesting with 5 jobs (limit)...")
    try:
        stats = fill_embeddings(limit=5, batch_size=5)
        
        print("\n✅ TEST PASSED")
        print(f"Stats: {stats}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_embedding_generation()
