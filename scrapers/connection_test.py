#!/usr/bin/env python3
"""
Script de diagnostic de connexion Supabase
Utilize pour identifier et résoudre les problèmes réseau IPv4/IPv6
"""

import os
import socket
import psycopg2
from pathlib import Path
import time

def load_env_vars():
    """Charge les variables depuis .env"""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value

def resolve_hostname_ipv4(hostname):
    """
    Résout un hostname vers IPv4 uniquement
    Critical pour éviter les problèmes IPv6 dans Docker
    """
    try:
        print(f"Résolution DNS pour {hostname}...")
        # Force IPv4 avec AF_INET
        addr_info = socket.getaddrinfo(
            hostname, 
            None, 
            socket.AF_INET,  # IPv4 seulement
            socket.SOCK_STREAM
        )
        ipv4_address = addr_info[0][4][0]
        print(f"✅ IPv4 résolu: {hostname} → {ipv4_address}")
        return ipv4_address
    except socket.gaierror as e:
        print(f"❌ Erreur résolution DNS: {e}")
        return None

def test_supabase_connection():
    """
    Test complet de connexion à Supabase avec diagnostic détaillé
    """
    print("=" * 60)
    print("DIAGNOSTIC CONNEXION SUPABASE")
    print("=" * 60)
    
    # Charger les variables
    load_env_vars()
    
    # Récupérer la config
    host = os.getenv('SUPABASE_HOST')
    password = os.getenv('SUPABASE_PASSWORD')
    port = int(os.getenv('SUPABASE_PORT', '5432'))
    db = os.getenv('SUPABASE_DB', 'postgres')
    user = os.getenv('SUPABASE_USER', 'postgres')
    
    if not all([host, password]):
        print("❌ Variables d'environnement manquantes")
        print(f"SUPABASE_HOST: {'✅' if host else '❌'}")
        print(f"SUPABASE_PASSWORD: {'✅' if password else '❌'}")
        return False
    
    print(f"Configuration détectée:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Database: {db}")
    print(f"  User: {user}")
    print()
    
    # Test 1: Résolution DNS IPv4
    print("TEST 1: Résolution DNS IPv4")
    ipv4_address = resolve_hostname_ipv4(host)
    if not ipv4_address:
        return False
    print()
    
    # Test 2: Connexion réseau basique
    print("TEST 2: Test connectivité réseau")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((ipv4_address, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} accessible sur {ipv4_address}")
        else:
            print(f"❌ Port {port} inaccessible (code: {result})")
            return False
    except Exception as e:
        print(f"❌ Erreur test réseau: {e}")
        return False
    print()
    
    # Test 3: Connexion PostgreSQL avec IPv4 forcé
    print("TEST 3: Connexion PostgreSQL avec IPv4")
    try:
        start_time = time.time()
        conn = psycopg2.connect(
            host=ipv4_address,  # Utiliser IPv4 directement
            port=port,
            database=db,
            user=user,
            password=password,
            sslmode='require',
            connect_timeout=15
        )
        
        # Test requête simple
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        pg_version = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'job_offers'")
        table_exists = cursor.fetchone()[0] > 0
        
        connection_time = time.time() - start_time
        
        print(f"✅ Connexion PostgreSQL réussie ({connection_time:.2f}s)")
        print(f"✅ Version: {pg_version[:50]}...")
        print(f"✅ Table job_offers: {'EXISTS' if table_exists else 'MISSING'}")
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM job_offers")
            job_count = cursor.fetchone()[0]
            print(f"✅ Nombre d'offres: {job_count}")
        
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def connection_benchmark():
    """
    Benchmark de connexion pour optimiser les timeouts
    """
    print("\n" + "=" * 60)
    print("BENCHMARK PERFORMANCE CONNEXION")
    print("=" * 60)
    
    load_env_vars()
    host = os.getenv('SUPABASE_HOST')
    password = os.getenv('SUPABASE_PASSWORD')
    
    if not all([host, password]):
        print("❌ Configuration manquante pour benchmark")
        return
    
    ipv4_address = resolve_hostname_ipv4(host)
    if not ipv4_address:
        return
    
    # Test avec différents timeouts
    timeouts = [5, 10, 15, 20]
    successful_connections = []
    
    for timeout in timeouts:
        print(f"\nTest timeout {timeout}s...")
        try:
            start_time = time.time()
            conn = psycopg2.connect(
                host=ipv4_address,
                port=5432,
                database='postgres',
                user='postgres',
                password=password,
                sslmode='require',
                connect_timeout=timeout
            )
            connection_time = time.time() - start_time
            conn.close()
            
            successful_connections.append((timeout, connection_time))
            print(f"✅ Succès en {connection_time:.2f}s")
            
        except Exception as e:
            print(f"❌ Échec: {str(e)[:100]}")
    
    if successful_connections:
        print(f"\n✅ Timeout optimal recommandé: {min(successful_connections, key=lambda x: x[1])[0]}s")
    else:
        print("\n❌ Aucune connexion réussie")

if __name__ == "__main__":
    success = test_supabase_connection()
    
    if success:
        connection_benchmark()
        print(f"\n🎯 DIAGNOSTIC: CONNEXION FONCTIONNELLE")
        print("Votre pipeline de données peut maintenant fonctionner")
    else:
        print(f"\n❌ DIAGNOSTIC: CONNEXION ÉCHOUÉE") 
        print("Vérifiez la configuration et la connectivité réseau")