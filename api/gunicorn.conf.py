# Gunicorn configuration for production deployment
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"  # Render provides PORT env var
backlog = 2048

# Worker processes
# VPS production: (2 * CPU cores) + 1. Ajuster selon votre VPS Contabo.
import multiprocessing
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"  # Use uvicorn worker for FastAPI
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeouts
timeout = 30
keepalive = 2

# Logging
loglevel = "info"
accesslog = "-"  # Log to stdout for Render to capture
errorlog = "-"   # Log to stderr for Render to capture
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "job-matching-api"

# Server mechanics
preload_app = True  # Load application code before forking workers
daemon = False      # Don't daemonize (Render needs foreground process)

# SSL (Render handles this, but good to disable for clarity)
forwarded_allow_ips = "*"
proxy_allow_from = "*"