#!/usr/bin/env python3
"""
Test simple initialisation Supabase 
"""
import sys
sys.path.append('/opt/airflow/scrapers')
from supabase_utils import get_supabase_connection

print("Testing Supabase setup...")

conn = get_supabase_connection()
cursor = conn.cursor()

# Check table exists
cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'job_offers')")
exists = cursor.fetchone()[0]

if not exists:
    print("Creating job_offers table...")
    cursor.execute('''
        CREATE TABLE job_offers (
            id SERIAL PRIMARY KEY,
            job_url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            description TEXT,
            source TEXT DEFAULT 'emploitogo.info',
            scraped_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    conn.commit()
    print("✅ Table created")
else:
    print("✅ Table already exists")

# Test insert  
cursor.execute('''
    INSERT INTO job_offers (job_url, title, company, location, source)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (job_url) DO NOTHING
''', (
    'https://test.com/job1',
    'Test Developer', 
    'Test Company',
    'Lomé, Togo',
    'test_scraper'
))
conn.commit()

cursor.execute('SELECT COUNT(*) FROM job_offers')
count = cursor.fetchone()[0]
print(f"✅ {count} jobs in database")

conn.close()
print("✅ Database ready for scraping!")