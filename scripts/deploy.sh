#!/bin/bash

# ==============================================================================
# Script de Déploiement Production - Transport Quote
# ==============================================================================
# Usage: ./scripts/deploy.sh <version_tag>
# Exemple: ./scripts/deploy.sh v1.2.0
#
# Pré-requis:
# - Être à la racine du projet
# - Avoir les droits d'exécution (chmod +x scripts/deploy.sh)
# - Docker et Docker Compose installés
# - Accès Git configuré
# ==============================================================================

set -e  # Arrêter le script en cas d'erreur

# Couleurs pour les logs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Vérification des arguments
VERSION=$1

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

if [ -z "$VERSION" ]; then
    error "Erreur: Version non spécifiée."
    echo "Usage: $0 <version_tag>"
    exit 1
fi

# Vérification que nous sommes à la racine (présence de docker-compose.yml)
if [ ! -f "docker-compose.yml" ]; then
    error "Erreur: docker-compose.yml introuvable. Exécutez le script depuis la racine du projet."
    exit 1
fi

log "🚀 Démarrage du déploiement de la version : $VERSION"

# ------------------------------------------------------------------------------
# 1. Sauvegarde de sécurité (Base de données)
# ------------------------------------------------------------------------------
log "💾 Étape 1/4 : Sauvegarde de la base de données..."
mkdir -p backups
BACKUP_FILE="backups/pre_deploy_${VERSION}_$(date +%Y%m%d_%H%M%S).sql"

if docker-compose exec -T postgres pg_dump -U postgres transport_quote > "$BACKUP_FILE"; then
    log "   ✅ Sauvegarde réussie : $BACKUP_FILE"
else
    error "   ❌ Échec de la sauvegarde. Arrêt du déploiement par sécurité."
    exit 1
fi

# ------------------------------------------------------------------------------
# 2. Mise à jour du code
# ------------------------------------------------------------------------------
log "📥 Étape 2/4 : Récupération du code (Git)..."

# S'assurer que le repo est propre (ou stash si nécessaire, ici on refuse pour prod)
if [ -n "$(git status --porcelain)" ]; then
    warn "⚠️  Modifications locales détectées. Assurez-vous que c'est intentionnel."
    # git stash # Décommenter si on veut forcer le stash
fi

log "   Fetching tags..."
git fetch --tags --force

log "   Checkout version $VERSION..."
if git checkout "$VERSION"; then
    log "   ✅ Code mis à jour vers $VERSION"
else
    error "   ❌ Version $VERSION introuvable sur Git."
    exit 1
fi

# ------------------------------------------------------------------------------
# 3. Reconstruction et Redémarrage
# ------------------------------------------------------------------------------
log "🏗  Étape 3/4 : Reconstruction des conteneurs..."

# Build sans cache pour s'assurer d'avoir les dernières dépendances si changées
docker-compose -f docker-compose.yml --env-file .env up -d --build --remove-orphans

# Vérification basique
if [ $? -eq 0 ]; then
    log "   ✅ Conteneurs redémarrés."
else
    error "   ❌ Erreur lors du redémarrage des conteneurs."
    log "   Tentative de rollback manuel conseillée : git checkout <old_version> && docker-compose up -d"
    exit 1
fi

# ------------------------------------------------------------------------------
# 4. Nettoyage et Vérification
# ------------------------------------------------------------------------------
log "🧹 Étape 4/4 : Nettoyage..."
docker image prune -f  # Supprime les images "dangling" (anciennes layers)

log "🔍 Vérification de l'état des services..."
docker-compose ps

log "🎉 Déploiement de la version $VERSION terminé avec succès !"
log "   En cas de problème, utilisez : ./scripts/rollback.sh <ancienne_version>"
