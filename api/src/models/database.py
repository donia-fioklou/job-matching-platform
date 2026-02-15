"""
Configuration base de données PostgreSQL pour l'API
Connectée à Supabase PostgreSQL via variables d'environnement
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

"""
Configuration base de données PostgreSQL pour l'API
Connectée à Supabase PostgreSQL avec résolution IPv4 robuste
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import socket
import logging

logger = logging.getLogger(__name__)

def resolve_supabase_ipv4(hostname):
    """
    Résout hostname Supabase vers IPv4 pour éviter problèmes Docker IPv6
    
    Args:
        hostname (str): Hostname Supabase
        
    Returns:
        str: Adresse IPv4 ou hostname original si échec
    """
    try:
        addr_info = socket.getaddrinfo(
            hostname, 
            None, 
            socket.AF_INET,  # Force IPv4
            socket.SOCK_STREAM
        )
        ipv4_addr = addr_info[0][4][0]
        logger.info(f"Supabase IPv4 résolu: {hostname} → {ipv4_addr}")
        return ipv4_addr
    except Exception as e:
        logger.warning(f"IPv4 resolution failed for {hostname}: {e}")
        return hostname  # Fallback sur hostname original

def build_supabase_url():
    """
    Construit l'URL de connexion Supabase avec IPv4 forcé
    Fallback sur variables individuelles si DATABASE_URL n'est pas définie
    """
    # Priorité à la DATABASE_URL complète
    database_url = os.getenv("DATABASE_URL")
    if database_url and "supabase.co" in database_url:
        # Parser l'URL pour remplacer hostname par IPv4
        import re
        
        # Extract hostname from URL
        hostname_match = re.search(r'@([^:/]+)', database_url)
        if hostname_match:
            original_hostname = hostname_match.group(1)
            ipv4_hostname = resolve_supabase_ipv4(original_hostname)
            
            # Replace hostname in URL with IPv4
            if ipv4_hostname != original_hostname:
                database_url = database_url.replace(original_hostname, ipv4_hostname)
                logger.info(f"URL modifiée avec IPv4: {original_hostname} → {ipv4_hostname}")
        
        return database_url
    
    # Sinon, construire depuis variables individuelles avec IPv4
    host = os.getenv("SUPABASE_HOST")
    port = os.getenv("SUPABASE_PORT", "5432")
    db = os.getenv("SUPABASE_DB", "postgres")
    user = os.getenv("SUPABASE_USER", "postgres")
    password = os.getenv("SUPABASE_PASSWORD")
    
    if not all([host, password]):
        raise ValueError(
            "Configuration Supabase incomplète. Variables requises : "
            "DATABASE_URL ou (SUPABASE_HOST + SUPABASE_PASSWORD)"
        )
    
    # Résoudre host vers IPv4
    ipv4_host = resolve_supabase_ipv4(host)
    
    return f"postgresql://{user}:{password}@{ipv4_host}:{port}/{db}"

# Configuration DB Supabase avec IPv4
DATABASE_URL = build_supabase_url()

# Engine avec configuration optimisée pour Supabase production
engine = create_engine(
    DATABASE_URL,
    pool_size=3,         # Réduit pour Supabase (limites connexion)
    max_overflow=7,      # Plus conservateur pour hosted DB
    pool_pre_ping=True,  # Critical pour connexions distantes
    pool_recycle=1800,   # Recycler connexions après 30min
    echo=False,          # Set to True pour debug SQL
    # Options critiques pour Supabase IPv4 + SSL
    connect_args={
        "sslmode": "require",              # Supabase require SSL
        "connect_timeout": 15,             # Timeout robuste
        "application_name": "job_matching_api",  # Pour monitoring
        "keepalives_idle": 600,            # Keep-alive pour stabilité
        "keepalives_interval": 30,
        "keepalives_count": 3
    }
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