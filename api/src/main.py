"""
Application FastAPI principale
Point d'entrée de l'API Job Matching Platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from .routes import jobs_router, health_router
from .models.database import engine, Base

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application
    """
    # Startup: Créer les tables si nécessaire (normalement déjà créées par init.sql)
    logger.info("Starting Job Matching API...")
    try:
        # Vérifie que les tables existent (sans les recréer)
        Base.metadata.reflect(bind=engine)
        logger.info("Database connection verified")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        
    yield
    
    # Shutdown
    logger.info("Shutting down Job Matching API...")

# Application FastAPI
app = FastAPI(
    title="Job Matching Platform API",
    description="""
    **API REST pour la plateforme de matching d'emploi au Togo**
    
    Cette API expose les données collectées par les scrapers Airflow depuis:
    - emploi.tg
    - goafricaonline.com  
    - emploi_info sites
    
    ## Fonctionnalités principales:
    
    * **🔍 Recherche et filtrage** des offres d'emploi
    * **📊 Statistiques** de scraping et monitoring
    * **🏢 Filtres** par entreprise, localisation, source
    * **📱 Pagination** optimisée pour applications frontend
    * **🔗 Accès par URL** pour déduplication
    
    ## Prochaines évolutions:
    * Matching IA candidat/offre
    * Analyse sémantique des descriptions
    * Recommandations personnalisées
    """,
    version="1.0.0",
    lifespan=lifespan,
    # Docs URL personnalisée
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware CORS pour frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routes
app.include_router(health_router)
app.include_router(jobs_router)

@app.get("/", tags=["Root"])
async def root():
    """
    Page d'accueil de l'API
    """
    return {
        "message": "Job Matching Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "jobs": "/jobs",
            "stats": "/jobs/stats",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    # Port configuration for both local and Render
    port = int(os.getenv("PORT", "8000"))  # Render provides PORT env var
    host = "0.0.0.0"  # Works both locally and on Render
    
    uvicorn.run(
        "main:app", 
        host=host, 
        port=port, 
        reload=True if os.getenv("ENVIRONMENT") != "production" else False,
        log_level="info"
    )