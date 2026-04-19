"""
DAG Airflow pour générer les embeddings des offres d'emploi
Exécute le script de vectorisation avec sentence-transformers
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Ajouter les chemins pour les imports
sys.path.append('/opt/airflow')
sys.path.insert(0, '/opt/airflow/scripts')

# Configuration du DAG
default_args = {
    'owner': 'job-platform',
    'depends_on_past': False,
    'email': ['admin@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=10)
}

dag = DAG(
    'daily_embedding_generation',
    default_args=default_args,
    description='Générer les embeddings pour les descriptions d\'offres d\'emploi',
    schedule=timedelta(days=1),  # Une fois par jour
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['embedding', 'ml', 'jobs']
)


def generate_embeddings_task(**context):
    """
    Tâche Airflow pour générer les embeddings
    Traite tous les jobs sans embedding par batch de 50
    """
    logger_info = []
    
    try:
        from embedding_generator import fill_embeddings

        logger_info.append("Starting embedding generation...")
        
        # Exécuter la génération d'embeddings
        stats = fill_embeddings(batch_size=50)
        
        logger_info.append(f"✅ Embedding generation completed")
        logger_info.append(f"Processed: {stats['processed']}")
        logger_info.append(f"Saved: {stats['saved']}")
        logger_info.append(f"Errors: {stats['errors']}")
        
        # Push stats vers XCom pour monitoring
        context['task_instance'].xcom_push(
            key='embedding_stats',
            value=stats
        )
        
        # Log
        for log_line in logger_info:
            print(log_line)
        
        # Retourner les stats
        return stats
    
    except Exception as e:
        logger_info.append(f"❌ Error: {str(e)}")
        for log_line in logger_info:
            print(log_line)
        raise


# Définition des tâches
embedding_task = PythonOperator(
    task_id='generate_job_embeddings',
    python_callable=generate_embeddings_task,
    dag=dag,
    provide_context=True,
    # Augmenter le timeout car le traitement peut être long
    execution_timeout=timedelta(hours=2)
)

# Pour l'instant, une seule tâche
# À l'avenir, on peut ajouter d'autres étapes (eg: validation, retraining, etc.)
