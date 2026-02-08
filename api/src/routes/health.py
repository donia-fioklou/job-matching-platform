"""
Health check endpoints pour monitoring
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from ..models.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
async def health_check():
    """
    Health check basique
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "job-matching-api"
    }

@router.get("/database")
async def database_health(db: Session = Depends(get_db)):
    """
    Vérifie la connexion à PostgreSQL
    """
    try:
        # Test simple query
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            return {
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=503, detail="Database query failed")
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Database connection failed: {str(e)}"
        )

@router.get("/full")
async def full_health_check(db: Session = Depends(get_db)):
    """
    Health check complet avec infos système
    """
    try:
        # Test DB connection
        db.execute(text("SELECT 1")).scalar()
        
        # Check quelques stats rapides
        job_count = db.execute(text("SELECT COUNT(*) FROM job_offers")).scalar()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "job-matching-api",
            "database": "connected", 
            "total_jobs": job_count,
            "checks": {
                "database": "pass",
                "basic_query": "pass"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "job-matching-api",
            "error": str(e),
            "checks": {
                "database": "fail"
            }
        }