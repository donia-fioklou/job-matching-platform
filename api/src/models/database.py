"""
Configuration base de données PostgreSQL pour l'API
Compatible développement local (Docker) et production (Render + Supabase)
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

def get_database_url():
    """
    Récupère l'URL de base de données selon l'environnement
    - Production (Render): DATABASE_URL directement
    - Développement: Construction depuis variables Supabase
    """
    # Priorité à DATABASE_URL (production Render)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # Fallback développement local (variables Supabase séparées)
    host = os.getenv("SUPABASE_HOST")
    port = os.getenv("SUPABASE_PORT", "5432")
    db = os.getenv("SUPABASE_DB", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD")
    
    if not all([host, password]):
        raise ValueError(
            "Configuration DB manquante. Requis: DATABASE_URL ou SUPABASE_HOST+PASSWORD"
        )
    
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"

def get_engine_config():
    """
    Configuration SQLAlchemy selon l'environnement
    """
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Configuration Render/cloud optimisée
        return {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "echo": False,
            "connect_args": {
                "sslmode": "require",
                "connect_timeout": 10,
                "application_name": "job_matching_api_prod"
            }
        }
    else:
        # Configuration développement local
        return {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_pre_ping": True,
            "echo": False,  # Set True pour debug SQL local
            "connect_args": {
                "sslmode": "require",
                "connect_timeout": 15,
                "application_name": "job_matching_api_dev"
            }
        }

# Configuration base de données
DATABASE_URL = get_database_url()
engine_config = get_engine_config()

engine = create_engine(DATABASE_URL, **engine_config)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dependency FastAPI pour injection DB session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()