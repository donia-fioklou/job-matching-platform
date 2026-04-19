"""
DAG simple pour récupération JSearch API avec pattern ETL classique
Extract -> Transform -> Load
"""

from datetime import datetime, timedelta
import sys
import os

# Correction des chemins pour les imports
sys.path.append('/opt/airflow/scrapers')
sys.path.append('/opt/airflow/getJobApi')
sys.path.append('/opt/airflow')

from airflow import DAG
from airflow.operators.python import PythonOperator

# Configuration du DAG
default_args = {
    'owner': 'job-team',
    'start_date': datetime(2024, 1, 1),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'jsearch_etl_jobs',
    default_args=default_args,
    description='ETL simple pour JSearch API',
    schedule='0 */1 * * *',  # Toutes les heures
    catchup=False,
    tags=['etl', 'jsearch', 'jobs']
)

def extract_jobs(**context):
    """
    Extract: Récupère les données brutes depuis l'API
    
    Responsabilité: Appeler l'API et passer les données à Transform
    """
    # Import au runtime pour éviter les erreurs d'initialisation du DAG
    from linkedin_api import fetch_jobs
    
    print("Extract: Récupération des données JSearch API...")
    
    # Appel de l'API via la fonction du module linkedin_api
    api_response = fetch_jobs(
        query="developer jobs in in new york via linkedin",
        country="us", 
        language="en",
        date_posted="all"
    )
    
    # Vérifier que l'API a répondu correctement
    if api_response.get('status') != 'OK':
        raise Exception(f"Erreur API: {api_response.get('status')}")
    
    raw_jobs = api_response.get('data', [])
    print(f"Extract: {len(raw_jobs)} offres récupérées")
    
    return raw_jobs

def transform_jobs(**context):
    """
    Transform: Mappe les champs API vers le schéma de la base de données
    
    Responsabilité: Transformation pure des données (API -> BD schema)
    """
    print("Transform: Mapping des données...")
    
    # Récupération des données de l'étape Extract
    raw_jobs = context['task_instance'].xcom_pull(task_ids='extract_jobs')
    
    if not raw_jobs:
        print("Transform: Aucune donnée à transformer")
        return []
    
    transformed_jobs = []
    
    for job in raw_jobs:
        # Mapping direct API JSearch -> Schema BD
        transformed_job = {
            'job_url': job.get('job_apply_link', ''),
            'title': job.get('job_title', ''),
            'company': job.get('employer_name', ''),
            'location': job.get('job_location', ''),
            'description': job.get('job_description', ''),
            'source': 'jsearch-api'
        }
        
        # Ne garder que les offres avec URL (clé unique)
        if transformed_job['job_url']:
            transformed_jobs.append(transformed_job)
    
    print(f"Transform: {len(transformed_jobs)} offres transformées")
    return transformed_jobs

def load_jobs(**context):
    """
    Load: Insert les données transformées en base de données
    
    Responsabilité: Persistence en BD avec gestion des doublons
    """
    # Imports au runtime pour éviter les erreurs d'initialisation du DAG
    from supabase_utils import get_supabase_connection
    import psycopg2
    
    print("Load: Insertion en base de données...")
    
    # Récupération des données transformées
    transformed_jobs = context['task_instance'].xcom_pull(task_ids='transform_jobs')
    
    if not transformed_jobs:
        print("Load: Aucune donnée à charger")
        return {"inserted": 0, "updated": 0}
    
    # Connexion DB via utilitaire existant
    conn = get_supabase_connection()
    cursor = conn.cursor()
    
    inserted = 0
    updated = 0
    
    for job in transformed_jobs:
        try:
            # UPSERT simple via ON CONFLICT
            cursor.execute("""
                INSERT INTO job_offers (job_url, title, company, location, description, source)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_url) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    company = EXCLUDED.company,
                    location = EXCLUDED.location,
                    description = EXCLUDED.description,
                    updated_at = NOW()
                RETURNING (xmax = 0) as inserted;
            """, (
                job['job_url'],
                job['title'], 
                job['company'],
                job['location'],
                job['description'],
                job['source']
            ))
            
            result = cursor.fetchone()
            if result and result[0]:  # xmax = 0 signifie nouvelle insertion
                inserted += 1
            else:
                updated += 1
                
        except psycopg2.Error as e:
            print(f"Erreur DB: {e}")
            continue
    
    conn.commit()
    cursor.close() 
    conn.close()
    
    print(f"Load: {inserted} nouvelles offres, {updated} mises à jour")
    return {"inserted": inserted, "updated": updated}

# Définition des tâches Airflow
extract_task = PythonOperator(
    task_id='extract_jobs',
    python_callable=extract_jobs,
    dag=dag
)

transform_task = PythonOperator(
    task_id='transform_jobs', 
    python_callable=transform_jobs,
    dag=dag
)

load_task = PythonOperator(
    task_id='load_jobs',
    python_callable=load_jobs,
    dag=dag
)

# Pipeline ETL : Extract -> Transform -> Load
extract_task >> transform_task >> load_task