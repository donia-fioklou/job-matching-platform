FROM apache/airflow:2.8.1

USER root

# Installation de dépendances système si nécessaires pour sentence-transformers
# (torch peut avoir besoin de certaines bibliothèques)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copier et installer les dépendances Python supplémentaires
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# L'image de base contient déjà tout le nécessaire pour Airflow
# On ajoute juste nos dépendances custom
