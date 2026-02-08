"""
Configuration base de données PostgreSQL pour l'API
Se connecte à la même DB que les scrapers Airflow
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Configuration DB - utilise les mêmes paramètres que docker-compose.yml
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://jobuser:jobpass@postgres:5432/jobmatching"
)

# Engine avec configuration optimisée pour API
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Vérifie la connexion avant utilisation
    echo=False  # Set to True pour debug SQL
)

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