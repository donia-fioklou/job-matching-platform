"""
DAG Airflow pour scraper goafricaonline.com/tg/emploi

Sépare les tâches Extract et Load pour goafricaonline
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

import sys
import os

# Ajouter le dossier scrapers au sys.path
sys.path.append('/opt/airflow/scrapers')

# Import du scraper goafricaonline
from goafricaonline_scraper import scrape_goafricaonline

# Import de la librairie pour PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor


def extract_jobs(**context):
    """
    Tâche Extract: scraping de goafricaonline.com/tg/emploi
    """
    print("Starting goafricaonline.com/tg/emploi job extraction...")
    
    # Appel du scraper
    jobs_data = scrape_goafricaonline()  # Simple function call
    
    print(f"Extracted {len(jobs_data)} jobs from goafricaonline.com/tg/emploi")
    
    # Envoyer les données à la tâche Load via XCom
    return jobs_data


def load_jobs(**context):
    """
    Tâche Load: insertion en base PostgreSQL
    """
    # Récupération des données depuis la tâche Extract
    ti = context['ti']
    jobs_data = ti.xcom_pull(task_ids='extract_jobs')
    
    if not jobs_data or len(jobs_data) == 0:
        print("No jobs received from extract task")
        return
    
    print(f"Received {len(jobs_data)} jobs to load")
    
    # Connexion à PostgreSQL
    conn = psycopg2.connect(
        host='postgres',
        port=5432,
        database='jobmatching',
        user='jobuser',
        password='jobpass'
    )
    
    cursor = conn.cursor()
    
    loaded_count = 0
    skipped_count = 0
    
    for job in jobs_data:
        try:
            # UPSERT: insertion ou mise à jour si l'URL existe déjà
            cursor.execute("""
                INSERT INTO job_offers (job_url, title, company, location, description, skills_text, contract_type, source)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_url) 
                DO UPDATE SET 
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    description = EXCLUDED.description,
                    skills_text = EXCLUDED.skills_text,
                    contract_type = EXCLUDED.contract_type,
                    scraped_at = CURRENT_TIMESTAMP
            """, (
                job.get('job_url', ''),
                job.get('title', ''),
                job.get('company', ''),
                job.get('location', ''),
                job.get('description', ''),
                job.get('skills', ''),
                job.get('contract_type', ''),
                'goafricaonline.com'
            ))
            
            
            loaded_count += 1
            
        except Exception as e:
            print(f"Error loading job {job.get('title', 'Unknown')}: {e}")
            skipped_count += 1
            continue
    
    # Validation et fermeture
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Load completed: {loaded_count} loaded, {skipped_count} skipped")


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

# Définition du DAG
dag = DAG(
    'hourly_goafricaonline_scraping',
    default_args=default_args,
    description='Scraping hourly des offres goafricaonline.com/tg/emploi',
    schedule=timedelta(hours=1),  # Chaque heure
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['scraping', 'goafricaonline', 'jobs']
)

# Définition des tâches
extract_task = PythonOperator(
    task_id='extract_jobs',
    python_callable=extract_jobs,
    dag=dag,
    provide_context=True
)

load_task = PythonOperator(
    task_id='load_jobs',
    python_callable=load_jobs,
    dag=dag,
    provide_context=True
)

# Définition des dépendances
extract_task >> load_task