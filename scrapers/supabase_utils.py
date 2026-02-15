"""
Utilitaires pour connexion Supabase depuis Airflow DAGs  
Solution simple : utiliser directement DATABASE_URL
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_supabase_connection():
    """
    Connexion Supabase simple - laisse psycopg2 gérer la résolution DNS
    """
    # Essayer d'abord DATABASE_URL complète
    database_url = os.getenv('SUPABASE_DATABASE_URL')
    
    if database_url:
        print("Using SUPABASE_DATABASE_URL...")
        conn = psycopg2.connect(
            database_url,
            sslmode='require',
            connect_timeout=15
        )
        print("✅ Connected via DATABASE_URL")
        return conn
    
    # Fallback sur variables séparées  
    host = os.getenv('SUPABASE_HOST')
    port = os.getenv('SUPABASE_PORT', '5432')
    database = os.getenv('SUPABASE_DB', 'postgres')
    user = os.getenv('SUPABASE_USER', 'postgres')
    password = os.getenv('SUPABASE_PASSWORD')
    
    if not all([host, password]):
        raise ValueError("Missing SUPABASE_DATABASE_URL or SUPABASE_HOST/PASSWORD")
    
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        database=database,
        user=user,
        password=password,
        sslmode='require',
        connect_timeout=15
    )
    
    print(f"✅ Connected: {user}@{host}/{database}")
    return conn

def get_supabase_cursor(dict_cursor=False):
    """
    Connexion + curseur
    """
    conn = get_supabase_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor if dict_cursor else None)
    return conn, cursor