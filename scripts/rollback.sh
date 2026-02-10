#!/bin/bash

# ==============================================================================
# Script de Rollback - Transport Quote
# ==============================================================================
# Usage: ./scripts/rollback.sh <target_version> [restore_db]
# Exemple: ./scripts/rollback.sh v1.0.0
# Exemple avec BDD: ./scripts/rollback.sh v1.0.0 true
# ==============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

VERSION=$1
RESTORE_DB=$2

log() { echo -e "${GREEN}[ROLLBACK] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}"; }

if [ -z "$VERSION" ]; then
    error "Version cible manquante."
    echo "Usage: $0 <target_version> [restore_db (true/false)]"
    exit 1
fi

log "🔙 Démarrage du rollback vers : $VERSION"

# 1. Revenir au code précédent
log "1. Git Checkout..."
git checkout "$VERSION"

# 2. Redémarrer l'application
log "2. Redémarrage des conteneurs..."
docker-compose up -d --build

# 3. Restauration BDD (Optionnel et Risqué)
if [ "$RESTORE_DB" == "true" ]; then
    log "⚠️  Restauration de la base de données demandée."
    
    # Trouver le dernier backup correspondant (ou demander fichier)
    # Ici, on liste les backups et on demande confirmation
    echo "Fichiers de backup disponibles :"
    ls -lh backups/*.sql
    
    read -p "Entrez le chemin complet du fichier SQL à restaurer : " BACKUP_FILE
    
    if [ -f "$BACKUP_FILE" ]; then
        log "Restoration depuis $BACKUP_FILE..."
        # Attention : ceci écrase la BDD actuelle
        cat "$BACKUP_FILE" | docker-compose exec -T postgres psql -U postgres transport_quote
        log "✅ Base de données restaurée."
    else
        error "Fichier introuvable. Restauration annulée."
    fi
else
    log "ℹ️  Aucune restauration BDD effectuée (code uniquement)."
fi

log "✅ Rollback terminé. Vérifiez les logs : docker-compose logs -f"
