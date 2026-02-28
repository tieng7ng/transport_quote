#!/bin/bash

# ============================================================
# Usage :
#   ./start.sh local   → HTTP sur http://localhost:8080
#   ./start.sh prod    → HTTPS sur https://transportquote.duckdns.org
# ============================================================

ENV=${1:-local}

case "$ENV" in
  local)
    echo "Démarrage en mode LOCAL (http://localhost:8080)..."
    docker-compose \
      -f docker-compose.yml \
      -f docker-compose.local.yml \
      --env-file .env.local \
      up -d --build
    echo ""
    echo "Application disponible sur : http://localhost:8080"
    ;;
  prod)
    echo "Démarrage en mode PRODUCTION (https://transportquote.duckdns.org)..."
    docker-compose \
      -f docker-compose.yml \
      --env-file .env \
      up -d --build
    echo ""
    echo "Application disponible sur : https://transportquote.duckdns.org"
    ;;
  *)
    echo "Usage: $0 [local|prod]"
    echo "  local  → HTTP sur http://localhost:8080 (défaut)"
    echo "  prod   → HTTPS sur https://transportquote.duckdns.org"
    exit 1
    ;;
esac
