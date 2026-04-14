FROM python:3.11-slim

WORKDIR /app

# Install des dépendances système si nécessaire
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements et install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pré-téléchargement du modèle d'embedding au build (évite timeout au 1er appel)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased')"

# Copy source code
COPY src/ ./src/

# Variables d'environnement
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Command par défaut
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]