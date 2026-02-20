#!/usr/bin/env bash
#
# backup.sh — Sauvegarde complete de Transport Quote
#
# Usage : ./backup.sh [repertoire_destination]
#
# Exemples :
#   ./backup.sh                     # Sauvegarde dans ./backups/
#   ./backup.sh /mnt/backup/        # Sauvegarde dans /mnt/backup/
#

set -euo pipefail

# --- Configuration ---
DB_CONTAINER="transport_quote_db"
DB_USER="user"
DB_NAME="transport_quote"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_DEST="${1:-${PROJECT_DIR}/backups}"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_DEST}/backup_${BACKUP_DATE}"

# --- Couleurs ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${GREEN}[BACKUP]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# --- Verifications ---
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    error "Le container ${DB_CONTAINER} n'est pas en cours d'execution."
    error "Demarrez l'application avec : docker compose up -d"
    exit 1
fi

# --- Creation du repertoire ---
mkdir -p "${BACKUP_DIR}"
log "Sauvegarde dans : ${BACKUP_DIR}"

# --- 1. Base de donnees ---
log "Sauvegarde de la base de donnees..."
docker exec "${DB_CONTAINER}" pg_dump \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=custom \
    --compress=9 \
    -f /tmp/backup.dump

docker cp "${DB_CONTAINER}:/tmp/backup.dump" "${BACKUP_DIR}/database.dump"
docker exec "${DB_CONTAINER}" rm /tmp/backup.dump
log "Base de donnees sauvegardee ($(du -sh "${BACKUP_DIR}/database.dump" | cut -f1))"

# --- 2. Fichiers .env ---
log "Sauvegarde des fichiers d'environnement..."
if [ -f "${PROJECT_DIR}/.env" ]; then
    cp "${PROJECT_DIR}/.env" "${BACKUP_DIR}/env_root"
fi
if [ -f "${PROJECT_DIR}/backend/.env" ]; then
    cp "${PROJECT_DIR}/backend/.env" "${BACKUP_DIR}/env_backend"
fi
log "Fichiers .env sauvegardes"

# --- 3. Uploads utilisateurs ---
if [ -d "${PROJECT_DIR}/backend/uploads" ]; then
    log "Sauvegarde des uploads utilisateurs..."
    tar -czf "${BACKUP_DIR}/uploads.tar.gz" -C "${PROJECT_DIR}/backend" uploads/
    log "Uploads sauvegardes ($(du -sh "${BACKUP_DIR}/uploads.tar.gz" | cut -f1))"
else
    warn "Dossier backend/uploads/ non trouve — ignore."
fi

# --- 4. Fichiers d'import tarifs ---
if [ -d "${PROJECT_DIR}/file_import" ]; then
    log "Sauvegarde des fichiers d'import..."
    tar -czf "${BACKUP_DIR}/file_import.tar.gz" -C "${PROJECT_DIR}" file_import/
    log "Fichiers d'import sauvegardes ($(du -sh "${BACKUP_DIR}/file_import.tar.gz" | cut -f1))"
else
    warn "Dossier file_import/ non trouve — ignore."
fi

# --- 5. Configurations partenaires ---
if [ -d "${PROJECT_DIR}/backend/configs" ]; then
    log "Sauvegarde des configurations..."
    tar -czf "${BACKUP_DIR}/configs.tar.gz" -C "${PROJECT_DIR}/backend" configs/
    log "Configurations sauvegardees"
else
    warn "Dossier backend/configs/ non trouve — ignore."
fi

# --- 6. Certificats SSL ---
if [ -d "${PROJECT_DIR}/certbot/conf" ]; then
    log "Sauvegarde des certificats SSL..."
    tar -czf "${BACKUP_DIR}/certbot.tar.gz" -C "${PROJECT_DIR}" certbot/
    log "Certificats sauvegardes"
else
    warn "Dossier certbot/conf/ non trouve — ignore."
fi

# --- Archive finale ---
log "Creation de l'archive finale..."
tar -czf "${BACKUP_DIR}.tar.gz" -C "${BACKUP_DEST}" "backup_${BACKUP_DATE}"
rm -rf "${BACKUP_DIR}"

# --- Resume ---
ARCHIVE_SIZE=$(du -sh "${BACKUP_DIR}.tar.gz" | cut -f1)
log "============================================"
log "Sauvegarde terminee avec succes !"
log "Archive : ${BACKUP_DIR}.tar.gz"
log "Taille  : ${ARCHIVE_SIZE}"
log "============================================"

# --- Nettoyage des anciennes sauvegardes (garder les 5 dernieres) ---
BACKUP_COUNT=$(ls -1 "${BACKUP_DEST}"/backup_*.tar.gz 2>/dev/null | wc -l)
if [ "${BACKUP_COUNT}" -gt 5 ]; then
    log "Nettoyage des anciennes sauvegardes (conservation des 5 dernieres)..."
    ls -1t "${BACKUP_DEST}"/backup_*.tar.gz | tail -n +6 | xargs rm -f
    log "Anciennes sauvegardes supprimees."
fi
