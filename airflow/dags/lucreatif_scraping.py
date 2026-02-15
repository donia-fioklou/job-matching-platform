"""
DAG Airflow pour scraper lucreatif.com

Sépare les tâches Extract et Load pour lucreatif.com
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup

import sys
import os

# Ajouter le dossier scrapers au sys.path
sys.path.append('/opt/airflow/scrapers')

# Import du scraper lucreatif
from lucreatif_scraper import scrape_lucreatif, extract_job_details

# Import des utilitaires Supabase
from supabase_utils import get_supabase_connection

# Import de la librairie pour PostgreSQL
import psycopg2
from psycopg2.extras import RealDictCursor


def extract_jobs(**context):
    """
    Tâche Extract: scraping de lucreatif.com avec deux phases
    Phase 1: Extraction URLs et métadonnées de base
    Phase 2: Extraction descriptions détaillées
    """
    print("Starting lucreatif.com job extraction (Phase 1 + 2)...")
    
    # Phase 1: Extraction URLs et métadonnées de base
    print("Phase 1: Extracting job URLs and basic metadata...")
    jobs_basic = scrape_lucreatif()
    
    if not jobs_basic or len(jobs_basic) == 0:
        print("No jobs found in Phase 1")
        return []
    
    print(f"Phase 1 completed: {len(jobs_basic)} jobs found")
    
    # Phase 2: Extraction descriptions détaillées
    print("Phase 2: Extracting detailed descriptions...")
    job_urls = [job['job_url'] for job in jobs_basic]
    detailed_jobs = extract_job_details(job_urls)
    
    # Fusionner les données des deux phases
    print("Merging Phase 1 and Phase 2 data...")
    final_jobs = []
    
    for i, basic_job in enumerate(jobs_basic):
        # Prendre les métadonnées de base de Phase 1
        final_job = {
            'job_url': basic_job['job_url'],
            'title': basic_job['title'],
            'company': basic_job['company'],
            'location': basic_job['location'],
            'scraped_at': basic_job['scraped_at']
        }
        
        # Ajouter la description détaillée de Phase 2 si disponible
        if i < len(detailed_jobs):
            detailed_job = detailed_jobs[i]
            final_job['description'] = detailed_job.get('full_description', basic_job['description'])
            final_job['has_full_description'] = detailed_job.get('has_full_description', False)
        else:
            # Fallback si Phase 2 échoue pour cette offre
            final_job['description'] = basic_job['description']
            final_job['has_full_description'] = False
        
        final_jobs.append(final_job)
    
    print(f"Extract completed: {len(final_jobs)} jobs with detailed descriptions")
    
    # Envoyer les données à la tâche Load via XCom
    return final_jobs


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
    
    # Connexion à Supabase PostgreSQL
    conn = get_supabase_connection()
    
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
                'lucreatif.com'
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
    'hourly_lucreatif_scraping',
    default_args=default_args,
    description='Scraping hourly des offres lucreatif.com',
    schedule=timedelta(hours=1),  # Chaque heure
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['scraping', 'lucreatif', 'jobs']
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