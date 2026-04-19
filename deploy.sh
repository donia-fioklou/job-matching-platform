#!/bin/bash
# deploy.sh - Script de déploiement sur VPS Contabo
# Usage: ./deploy.sh [pull|restart|logs|stop]

set -e

COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

case "$1" in
  pull)
    echo ">>> Pulling latest code..."
    git pull origin main
    echo ">>> Rebuilding images..."
    $COMPOSE build --no-cache
    echo ">>> Restarting services..."
    $COMPOSE up -d
    echo ">>> Done. Check logs: ./deploy.sh logs"
    ;;

  restart)
    echo ">>> Restarting all services..."
    $COMPOSE restart
    ;;

  logs)
    SERVICE=${2:-""}
    $COMPOSE logs -f --tail=100 $SERVICE
    ;;

  stop)
    echo ">>> Stopping all services..."
    $COMPOSE down
    ;;

  status)
    $COMPOSE ps
    ;;

  *)
    echo ">>> First deploy / Full start..."
    echo ">>> Step 1: Build images"
    $COMPOSE build

    echo ">>> Step 2: Start database and init Airflow"
    $COMPOSE up -d postgres
    sleep 10
    $COMPOSE up airflow-init

    echo ">>> Step 3: Start all services"
    $COMPOSE up -d

    echo ""
    echo "=== Services started ==="
    $COMPOSE ps
    echo ""
    echo "API:     http://$(curl -s ifconfig.me):8000"
    echo "Airflow: http://$(curl -s ifconfig.me):8081"
    echo ""
    echo "Pour configurer Nginx + SSL, suivre le README de déploiement."
    ;;
esac
