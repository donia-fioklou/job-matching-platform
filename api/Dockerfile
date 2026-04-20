FROM python:3.11-slim

WORKDIR /app

# Install des dépendances système si nécessaire
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements et install Python dependencies
COPY requirements.txt .
# Torch CPU-only d'abord (~200MB vs ~2GB pour GPU)
RUN pip install --no-cache-dir --timeout=180 --retries=5 \
    torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --timeout=180 --retries=5 -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY gunicorn.conf.py .

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Command par défaut
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]