# Deployment Guide - Render

## Local Development (Current)
```bash
cd api
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
# OR with Docker
docker-compose up api
```

## Production Deployment (Render)

### 1. Push to GitHub
```bash
git add .
git commit -m "feat: add Render deployment config"
git push origin main
```

### 2. Create Render Service
1. Go to [render.com](https://render.com)
2. Connect your GitHub repo
3. **Important**: Set Root Directory to `api`
4. Service will auto-detect `render.yaml` configuration

### 3. Environment Variables (Render Dashboard)
Set these in Render service environment:
```
DATABASE_URL = your_supabase_connection_string
ENVIRONMENT = production
```

### 4. Automatic Deploy
- Render will use `render.yaml` configuration
- Build: `pip install -r requirements.txt`
- Start: `gunicorn src.main:app --config gunicorn.conf.py`

## Testing Production Setup Locally
```bash
cd api
pip install gunicorn
gunicorn src.main:app --config gunicorn.conf.py
```

## Configuration Details

### Environment Detection
- **Development**: Uses SUPABASE_* variables from .env
- **Production**: Uses DATABASE_URL from Render environment

### Server Configuration  
- **Development**: uvicorn with hot reload
- **Production**: gunicorn with optimized workers

### Database Connection
- **Development**: IPv6 compatible through Docker network
- **Production**: Direct Supabase connection through Render cloud

## Troubleshooting

### Local API not starting?
Check that you have gunicorn installed: `pip install gunicorn`

### Database connection errors?
Verify environment variables are set correctly for your environment.

### Render deployment fails?
Check Render logs and ensure `render.yaml` is in the `api` directory.