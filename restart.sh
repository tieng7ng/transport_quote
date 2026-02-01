#!/bin/bash

# Script de redémarrage complet - Transport Quote
# Usage: ./restart.sh [frontend|backend|all]

set -e

PROJECT_DIR="/Users/tiengd/Documents/tuto/transport_quote"
cd "$PROJECT_DIR"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction pour redémarrer le frontend
restart_frontend() {
    log_info "=== Redémarrage Frontend ==="

    cd "$PROJECT_DIR"

    log_info "Arrêt du container frontend..."
    docker-compose stop frontend 2>/dev/null || true
    docker-compose rm -f frontend 2>/dev/null || true

    log_info "Reconstruction de l'image frontend..."
    docker-compose build frontend

    log_info "Démarrage du container frontend..."
    docker-compose up -d frontend

    log_info "Frontend redémarré avec succès!"
    echo -e "${GREEN}URL: http://localhost:8080${NC}"
}

# Fonction pour redémarrer le backend
restart_backend() {
    log_info "=== Redémarrage Backend ==="

    cd "$PROJECT_DIR"

    log_info "Arrêt du container backend..."
    docker-compose stop backend 2>/dev/null || true
    docker-compose rm -f backend 2>/dev/null || true

    log_info "Reconstruction de l'image backend..."
    docker-compose build backend

    log_info "Démarrage du container backend..."
    docker-compose up -d backend

    log_info "Backend redémarré avec succès!"
    echo -e "${GREEN}URL: http://localhost:3000${NC}"
}

# Fonction pour redémarrer tout
restart_all() {
    log_info "=== Redémarrage Complet ==="

    cd "$PROJECT_DIR"

    log_info "Arrêt de tous les containers..."
    docker-compose down

    log_info "Reconstruction des images (build incremental)..."
    docker-compose build

    log_info "Démarrage de tous les services..."
    docker-compose up -d

    log_info "Tous les services redémarrés avec succès!"
    echo ""
    echo -e "${GREEN}URLs:${NC}"
    echo -e "  Frontend: http://localhost:8080"
    echo -e "  Backend:  http://localhost:3000"
    echo -e "  API Docs: http://localhost:3000/docs"
}

# Fonction pour afficher le statut
show_status() {
    log_info "=== Statut des services ==="
    docker-compose ps
}

# Menu principal
case "${1:-all}" in
    frontend|f)
        restart_frontend
        ;;
    backend|b)
        restart_backend
        ;;
    all|a)
        restart_all
        ;;
    status|s)
        show_status
        ;;
    *)
        echo "Usage: $0 [frontend|backend|all|status]"
        echo ""
        echo "Options:"
        echo "  frontend (f)  - Redémarre uniquement le frontend"
        echo "  backend (b)   - Redémarre uniquement le backend"
        echo "  all (a)       - Redémarre tout (défaut)"
        echo "  status (s)    - Affiche le statut des containers"
        exit 1
        ;;
esac

echo ""
show_status
