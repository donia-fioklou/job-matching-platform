"""
DAG Airflow ultra-simple : une seule tâche qui fait tout
Scrape + Save toutes les heures
"""

from datetime import datetime, timedelta
import sys
sys.path.append('/opt/airflow/scrapers')

import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator
from scrape_emploi_togo import scrape_emploi_togo

# Configuration du DAG
default_args = {
    'owner': 'job-team',
    'start_date': datetime(2024, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'hourly_job_scraping',
    default_args=default_args,
    description='Scrape jobs every hour',
    schedule_interval='0 * * * *',  # Hourly
    catchup=False,
    tags=['jobs', 'hourly']
)

def extract_jobs(**context):
    """Tâche Extract : scraping des offres emploi"""
    
    print("Starting job scraping...")
    jobs = scrape_emploi_togo()
    
    if not jobs:
        print("No jobs found")
        return {"jobs_count": 0, "jobs": []}
    
    print(f"Scraped {len(jobs)} jobs")
    
    # Push vers XCom pour la tâche Load
    context['task_instance'].xcom_push(key='jobs_data', value=jobs)
    
    return {"jobs_count": len(jobs), "status": "success"}

def load_jobs(**context):
    """Tâche Load : sauvegarde en base PostgreSQL"""
    
    # Récupération données depuis Extract
    jobs = context['task_instance'].xcom_pull(key='jobs_data', task_ids='extract_jobs')
    
    if not jobs:
        print("No jobs to load")
        return {"loaded_count": 0, "status": "no_data"}
    
    print(f"Loading {len(jobs)} jobs to database...")
    
    # Connection DB
    conn = psycopg2.connect(
        host='postgres',
        database='jobmatching',
        user='jobuser',
        password='jobpass'
    )
    
    # Insert avec déduplication
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    
    for job in jobs:
        try:
            # UPSERT simple
            cursor.execute("""
                INSERT INTO job_offers (job_url, title, company, location, description, scraped_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_url) DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    description = EXCLUDED.description,
                    scraped_at = EXCLUDED.scraped_at
                RETURNING (xmax = 0) AS is_insert
            """, (
                job['job_url'],
                job['title'], 
                job['company'],
                job['location'],
                job['description'],
                job['scraped_at']
            ))
            
            result = cursor.fetchone()
            if result and result[0]:  # is_insert = True
                inserted += 1
            else:
                updated += 1
                
        except Exception as e:
            print(f"Error inserting job: {e}")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Load completed: {inserted} inserted, {updated} updated")
    
    return {
        "loaded_count": len(jobs),
        "inserted": inserted, 
        "updated": updated,
        "status": "success"
    }

# Définition des tâches
extract_task = PythonOperator(
    task_id='extract_jobs',
    python_callable=extract_jobs,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_jobs',
    python_callable=load_jobs,
    dag=dag,
)

# Pipeline : Extract >> Load
extract_task >> load_task