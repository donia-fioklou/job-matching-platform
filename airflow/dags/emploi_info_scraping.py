"""
DAG Airflow architecture two-phase : 
Phase 1: Extract URLs + métadonnées de base
Phase 2: Extract descriptions détaillées  
Phase 3: Merge et Load en base
"""

from datetime import datetime, timedelta
import sys
sys.path.append('/opt/airflow/scrapers')

import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator
from scrape_emploi_togo import scrape_emploi_togo, extract_job_details as scraper_extract_details

# Configuration du DAG
default_args = {
    'owner': 'job-team',
    'start_date': datetime(2024, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'hourly_emploi_info_scraping',
    default_args=default_args,
    description='Scraping hourly des offres emploitogo.info',
    schedule='0 * * * *',  # Hourly (nouvelle syntaxe)
    catchup=False,
    tags=['scraping', 'emploi-info', 'jobs']
)

def extract_job_urls(**context):
    """Phase 1: Extraction URLs emploitogo.info"""
    
    print("Phase 1: Starting job URLs extraction...")
    base_jobs = scrape_emploi_togo()
    
    if not base_jobs:
        print("No jobs found in phase 1")
        return {"jobs_count": 0, "detail_urls": [], "status": "no_data"}
    
    # Extraction des URLs pour phase 2
    detail_urls = [job['detail_url'] for job in base_jobs if job.get('detail_url')]
    
    print(f"Phase 1: Extracted {len(base_jobs)} jobs, {len(detail_urls)} detail URLs")
    
    # Push vers XCom pour les phases suivantes
    context['task_instance'].xcom_push(key='base_jobs', value=base_jobs)
    context['task_instance'].xcom_push(key='detail_urls', value=detail_urls)
    
    return {
        "jobs_count": len(base_jobs),
        "detail_urls_count": len(detail_urls),
        "status": "success"
    }

def extract_job_details(**context):
    """Phase 2: Extraction descriptions détaillées emploitogo.info"""
    
    # Récupération URLs depuis Phase 1
    detail_urls = context['task_instance'].xcom_pull(
        key='detail_urls', 
        task_ids='extract_job_urls'
    )
    
    if not detail_urls:
        print("No detail URLs to process")
        return {"details_count": 0, "status": "no_data"}
    
    print(f"Phase 2: Extracting details for {len(detail_urls)} URLs...")
    
    # Extraction des détails
    job_details = scraper_extract_details(detail_urls)
    
    print(f"Phase 2: Extracted details for {len(job_details)} jobs")
    
    # Push vers XCom pour Phase 3
    context['task_instance'].xcom_push(key='job_details', value=job_details)
    
    return {
        "details_count": len(job_details),
        "successful_extractions": len([j for j in job_details if j.get('has_full_description')]),
        "failed_extractions": len([j for j in job_details if not j.get('has_full_description')]),
        "status": "success"
    }

def merge_and_load(**context):
    """Phase 3: Merge données et Load en base PostgreSQL"""
    
    # Récupération données des phases précédentes
    base_jobs = context['task_instance'].xcom_pull(
        key='base_jobs', 
        task_ids='extract_job_urls'
    )
    
    job_details = context['task_instance'].xcom_pull(
        key='job_details', 
        task_ids='extract_job_details'
    )
    
    if not base_jobs:
        print("No base jobs to load")
        return {"loaded_count": 0, "status": "no_data"}
    
    # Merge des données : base + détails
    print(f"Phase 3: Merging {len(base_jobs)} base jobs with {len(job_details or [])} details...")
    
    # Création d'un index des détails par URL
    details_by_url = {}
    if job_details:
        for detail in job_details:
            details_by_url[detail['job_url']] = detail
    
    # Merge des données
    merged_jobs = []
    for base_job in base_jobs:
        merged_job = base_job.copy()
        
        # Si on a des détails pour cette URL, on merge
        detail = details_by_url.get(base_job['job_url'])
        if detail:
            merged_job.update({
                'description': detail['full_description'],
                'has_full_description': detail['has_full_description'],
                'detail_extracted_at': detail['detail_extracted_at']
            })
            if 'extraction_error' in detail:
                merged_job['extraction_error'] = detail['extraction_error']
        
        merged_jobs.append(merged_job)
    
    print(f"Phase 3: Merged {len(merged_jobs)} complete job records")
    
    # Load en base PostgreSQL
    conn = psycopg2.connect(
        host='postgres',
        port=5432,
        database='jobmatching',
        user='jobuser',
        password='jobpass'
    )
    
    cursor = conn.cursor()
    inserted = 0
    updated = 0
    
    for job in merged_jobs:
        try:
            # UPSERT avec le schéma correct
            cursor.execute("""
                INSERT INTO job_offers (
                    job_url, title, company, location, description, source
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_url) DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    description = EXCLUDED.description,
                    scraped_at = CURRENT_TIMESTAMP
                RETURNING (xmax = 0) AS is_insert
            """, (
                job['job_url'],
                job['title'],
                job['company'], 
                job['location'],
                job['description'],
                'emploitogo.info'  # Source originale
            ))
            
            result = cursor.fetchone()
            if result and result[0]:
                inserted += 1
            else:
                updated += 1
                
        except Exception as e:
            print(f"Error inserting job {job.get('job_url', 'unknown')}: {e}")
            continue
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Phase 3 completed: {inserted} inserted, {updated} updated")
    
    return {
        "loaded_count": len(merged_jobs),
        "inserted": inserted,
        "updated": updated,
        "merge_success_rate": len([j for j in merged_jobs if j.get('has_full_description')]) / len(merged_jobs) if merged_jobs else 0,
        "status": "success"
    }

# Définition des tâches
extract_urls_task = PythonOperator(
    task_id='extract_job_urls',
    python_callable=extract_job_urls,
    dag=dag,
)

extract_details_task = PythonOperator(
    task_id='extract_job_details',
    python_callable=extract_job_details,
    dag=dag,
    # Plus de timeout pour cette phase
    execution_timeout=timedelta(minutes=15),
)

merge_load_task = PythonOperator(
    task_id='merge_and_load',
    python_callable=merge_and_load,
    dag=dag,
)

# Pipeline Three-Phase : URLs >> Details >> Merge&Load
extract_urls_task >> extract_details_task >> merge_load_task