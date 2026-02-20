# Guide de sauvegarde et restauration — Transport Quote

## Table des matieres

1. [Vue d'ensemble](#1-vue-densemble)
2. [Inventaire des donnees a sauvegarder](#2-inventaire-des-donnees-a-sauvegarder)
3. [Procedure de sauvegarde](#3-procedure-de-sauvegarde)
4. [Procedure de restauration](#4-procedure-de-restauration)
5. [Script de sauvegarde automatisable](#5-script-de-sauvegarde-automatisable)
6. [Notes de securite](#6-notes-de-securite)

---

## 1. Vue d'ensemble

### Architecture de l'application

Transport Quote est une application conteneurisee composee de 6 services Docker :

| Service  | Container                  | Image               | Role                       |
| -------- | -------------------------- | ------------------- | -------------------------- |
| postgres | `transport_quote_db`       | postgres:16-alpine  | Base de donnees PostgreSQL |
| redis    | `transport_quote_redis`    | redis:7-alpine      | Cache et sessions          |
| backend  | `transport_quote_backend`  | Custom (./backend)  | API FastAPI (Python)       |
| frontend | `transport_quote_frontend` | Custom (./frontend) | Application React          |
| nginx    | `transport_quote_nginx`    | nginx:1.25-alpine   | Reverse proxy + SSL        |
| certbot  | `transport_quote_certbot`  | certbot/certbot     | Renouvellement certificats |

**Reseau Docker :** `app-network` (bridge)
**Domaine :** `transportquote.duckdns.org`

### Ce qui doit etre sauvegarde

Une sauvegarde complete inclut **6 categories** de donnees :
- Base de donnees PostgreSQL
- Fichiers d'environnement (secrets)
- Fichiers uploades par les utilisateurs
- Fichiers d'import tarifs partenaires
- Configurations partenaires
- Certificats SSL

Le code source etant gere par Git, il n'a pas besoin d'etre inclus dans la sauvegarde (il suffit de cloner le depot).

---

## 2. Inventaire des donnees a sauvegarder

| Categorie                  | Emplacement                                                        | Taille approx.         | Criticite    | Notes                                                               |
| -------------------------- | ------------------------------------------------------------------ | ---------------------- | ------------ | ------------------------------------------------------------------- |
| **Base de donnees**        | Volume Docker `transport_quote_postgres_data`                      | Variable (~100-500 MB) | **Critique** | Contient toutes les donnees metier                                  |
| **Secrets / .env**         | `./.env` et `./backend/.env`                                       | < 1 KB                 | **Critique** | Mots de passe, cles, URLs de connexion                              |
| **Uploads utilisateurs**   | `./backend/uploads/`                                               | ~38 MB (61 fichiers)   | Haute        | Fichiers .xlsx/.csv importes par les utilisateurs                   |
| **Imports tarifs**         | `./file_import/`                                                   | ~50 MB (12 fichiers)   | Haute        | Grilles tarifaires partenaires (source)                             |
| **Configs partenaires**    | `./backend/configs/`                                               | ~21 KB                 | Haute        | `partner_mapping.yaml` + templates                                  |
| **Certificats SSL**        | `./certbot/conf/`                                                  | Quelques KB            | Moyenne      | Peut etre regenere via Let's Encrypt                                |
| **Config nginx**           | `./nginx-reverse-proxy.conf`                                       | ~2 KB                  | Basse        | Versionne dans Git                                                  |
| **Scripts de deploiement** | `./start.sh`, `./stop.sh`, `./restart.sh`, `./init-letsencrypt.sh` | < 10 KB                | Basse        | Versionnes dans Git                                                 |
| **Docker Compose**         | `./docker-compose.yml`, `./docker-compose.staging.yml`             | ~3.5 KB                | Basse        | Versionnes dans Git                                                 |
| **Cache Redis**            | Container `transport_quote_redis`                                  | Ephemere               | Basse        | Se reconstruit automatiquement (voir [note Redis](#note-sur-redis)) |

### Detail des fichiers .env

Les fichiers `.env` contiennent les variables suivantes :

**Racine (`./.env`)** — utilise par Docker Compose :

```
POSTGRES_USER=user
POSTGRES_PASSWORD=<secret>
POSTGRES_DB=transport_quote
DATABASE_URL=postgresql://user:<secret>@postgres:5432/transport_quote
SECRET_KEY=<secret>
ALLOWED_ORIGINS=https://transportquote.duckdns.org
REDIS_PASSWORD=<secret>
```

**Backend (`./backend/.env`)** — utilise par l'application en dev local :

```
DATABASE_URL=postgresql://user:<secret>@localhost:5432/transport_quote
REDIS_HOST=localhost
REDIS_PORT=6379
DEBUG=true
UPLOAD_DIR=./uploads
PARTNER_CONFIGS_DIR=./configs/partners
SECRET_KEY=<secret>
ALLOWED_ORIGINS=http://localhost:8080,https://transportquote.duckdns.org
```

### Note sur Redis

Redis stocke le cache applicatif et les **tokens JWT revoques** (blacklist de logout). Ces donnees sont ephemeres et **n'ont pas besoin d'etre sauvegardees** :

- Le cache se reconstruit naturellement a l'usage
- Les tokens JWT ont une duree d'expiration courte (quelques heures)
- Apres une restauration (qui implique une interruption de service), tous les utilisateurs se reconnectent de toute facon

**Risque residuel :** Un utilisateur deconnecte avant la sauvegarde pourrait theoriquement reutiliser son ancien token jusqu'a expiration. Ce risque est negligeable etant donne la courte duree de vie des tokens.

### Detail des certificats SSL

```
certbot/
├── conf/
│   └── live/
│       └── transportquote.duckdns.org/
│           ├── fullchain.pem
│           └── privkey.pem
└── www/
```

---

## 3. Procedure de sauvegarde

### 3.1. Prerequis

- Acces SSH au serveur source
- Docker et Docker Compose en cours d'execution
- Espace disque suffisant pour stocker la sauvegarde (~200 MB minimum)

### 3.2. Sauvegarde de la base de donnees

```bash
# Creer un dump complet de la base PostgreSQL
docker exec transport_quote_db pg_dump \
  -U user \
  -d transport_quote \
  --format=custom \
  --compress=9 \
  -f /tmp/transport_quote_backup.dump

# Copier le dump depuis le container
docker cp transport_quote_db:/tmp/transport_quote_backup.dump ./backup_db.dump

# Nettoyer le fichier temporaire dans le container
docker exec transport_quote_db rm /tmp/transport_quote_backup.dump
```

> **Note :** Le format `--format=custom` est recommande car il permet une restauration selective (tables individuelles) et inclut la compression.

### 3.3. Sauvegarde des fichiers

```bash
# Depuis la racine du projet (/path/to/transport_quote/)

# Fichiers d'environnement (SECRETS)
cp .env ./backup_env_root.env
cp backend/.env ./backup_env_backend.env

# Uploads utilisateurs
tar -czf backup_uploads.tar.gz -C backend uploads/

# Fichiers d'import tarifs
tar -czf backup_file_import.tar.gz file_import/

# Configurations partenaires
tar -czf backup_configs.tar.gz -C backend configs/

# Certificats SSL
tar -czf backup_certbot.tar.gz certbot/
```

### 3.4. Creer une archive unique

```bash
# Regrouper tous les fichiers de sauvegarde
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backup_transport_quote_${BACKUP_DATE}"

mkdir -p "${BACKUP_DIR}"
mv backup_db.dump "${BACKUP_DIR}/"
mv backup_env_root.env "${BACKUP_DIR}/"
mv backup_env_backend.env "${BACKUP_DIR}/"
mv backup_uploads.tar.gz "${BACKUP_DIR}/"
mv backup_file_import.tar.gz "${BACKUP_DIR}/"
mv backup_configs.tar.gz "${BACKUP_DIR}/"
mv backup_certbot.tar.gz "${BACKUP_DIR}/"

# Creer l'archive finale
tar -czf "${BACKUP_DIR}.tar.gz" "${BACKUP_DIR}/"

# Nettoyer le dossier temporaire
rm -rf "${BACKUP_DIR}"

echo "Sauvegarde creee : ${BACKUP_DIR}.tar.gz"
```

### 3.5. Transferer la sauvegarde

```bash
# Vers un serveur distant via SCP
scp backup_transport_quote_*.tar.gz user@backup-server:/backups/

# Ou vers un stockage cloud (exemple avec rclone)
rclone copy backup_transport_quote_*.tar.gz remote:backups/transport_quote/
```

---

## 4. Procedure de restauration

### Etape 0 — Prerequis sur la nouvelle machine

```bash
# Installer Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Installer Docker Compose (v2)
sudo apt-get install docker-compose-plugin
# Verifier
docker compose version

# Installer Git
sudo apt-get install -y git
```

### Etape 1 — Cloner le depot

```bash
git clone <URL_DU_DEPOT> transport_quote
cd transport_quote
```

### Etape 2 — Restaurer les fichiers .env

```bash
# Extraire l'archive de sauvegarde
tar -xzf backup_transport_quote_YYYYMMDD_HHMMSS.tar.gz
cd backup_transport_quote_YYYYMMDD_HHMMSS/

# Copier les fichiers d'environnement
cp backup_env_root.env ../transport_quote/.env
cp backup_env_backend.env ../transport_quote/backend/.env

cd ../transport_quote/
```

> **Important :** Verifier et adapter les variables d'environnement si le nouveau serveur a une configuration differente (domaine, ports, IP).

### Etape 3 — Restaurer les fichiers de donnees

```bash
# Uploads utilisateurs
tar -xzf ../backup_transport_quote_*/backup_uploads.tar.gz -C backend/

# Fichiers d'import tarifs
tar -xzf ../backup_transport_quote_*/backup_file_import.tar.gz

# Configurations partenaires
tar -xzf ../backup_transport_quote_*/backup_configs.tar.gz -C backend/

# Certificats SSL (optionnel — voir note ci-dessous)
tar -xzf ../backup_transport_quote_*/backup_certbot.tar.gz

# Ajuster les permissions
chmod -R 755 backend/uploads/
chmod -R 755 backend/configs/
chmod -R 755 file_import/
```

> **Note SSL :** Si le domaine change, les anciens certificats ne seront pas valides. Dans ce cas, regenerer les certificats avec `./init-letsencrypt.sh` apres le demarrage.

### Etape 4 — Demarrer les containers (sans donnees)

```bash
# Construire et demarrer tous les services
docker compose up -d --build

# Verifier que tous les containers tournent
docker compose ps
```

Attendre que le container `transport_quote_db` soit `healthy` :

```bash
# Attendre que PostgreSQL soit pret
until docker exec transport_quote_db pg_isready -U user; do
  echo "En attente de PostgreSQL..."
  sleep 2
done
echo "PostgreSQL est pret."
```

### Etape 5 — Restaurer la base de donnees

```bash
# Copier le dump dans le container
docker cp ../backup_transport_quote_*/backup_db.dump transport_quote_db:/tmp/backup.dump

# Supprimer la base existante (creee au premier demarrage) et la recreer vide
docker exec transport_quote_db dropdb -U user transport_quote
docker exec transport_quote_db createdb -U user transport_quote

# Restaurer depuis le dump
docker exec transport_quote_db pg_restore \
  -U user \
  -d transport_quote \
  --no-owner \
  --no-privileges \
  /tmp/backup.dump

# Nettoyer
docker exec transport_quote_db rm /tmp/backup.dump
```

### Etape 6 — Appliquer les migrations de schema

Le backend execute automatiquement `alembic upgrade head` au demarrage (via `entrypoint.sh`). Toutefois, apres une restauration de dump, il est recommande de verifier manuellement :

```bash
# Verifier l'etat actuel des migrations
docker exec transport_quote_backend alembic current

# Si necessaire, appliquer les migrations manquantes
docker exec transport_quote_backend alembic upgrade head
```

> **Note :** Cela est surtout important si le code source (Git) est plus recent que le dump de la base de donnees.

### Etape 7 — Redemarrer les services

```bash
# Redemarrer le backend pour qu'il prenne en compte la BD restauree
docker compose restart backend

# Ou redemarrer l'ensemble
docker compose down && docker compose up -d
```

### Etape 8 — Verification

```bash
# 1. Verifier que tous les containers tournent
docker compose ps

# 2. Tester la connexion a la BD
docker exec transport_quote_db psql -U user -d transport_quote -c "SELECT count(*) FROM users;"

# 3. Verifier les utilisateurs et roles
docker exec transport_quote_db psql -U user -d transport_quote \
  -c "SELECT login, role FROM users LIMIT 5;"

# 4. Tester l'API backend
curl -s http://localhost:3000/api/health | head -20

# 5. Tester l'authentification
curl -s -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"admin","password":"<motdepasse>"}'

# 6. Tester l'acces web (si le domaine est configure)
curl -s -o /dev/null -w "%{http_code}" https://transportquote.duckdns.org

# 7. Verifier les fichiers uploades
ls -la backend/uploads/ | head -5

# 8. Verifier les configurations partenaires
ls -la backend/configs/

# 9. Verifier les fichiers d'import
ls -la file_import/

# 10. Verifier l'etat des migrations Alembic
docker exec transport_quote_backend alembic current
```

---

## 5. Script de sauvegarde automatisable

Creer un fichier `backup.sh` a la racine du projet :

```bash
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
```

### Utilisation

```bash
# Rendre executable
chmod +x backup.sh

# Lancer une sauvegarde
./backup.sh

# Ou specifier un repertoire de destination
./backup.sh /mnt/external/backups/
```

### Automatisation avec cron

```bash
# Ouvrir l'editeur cron
crontab -e

# Sauvegarde quotidienne a 2h du matin
0 2 * * * cd /home/ubuntu/transport_quote && ./backup.sh /mnt/backups/ >> /var/log/transport_quote_backup.log 2>&1
```

**Exemples de planification cron** :

```bash
# Tous les jours a 2h
0 2 * * * /path/to/transport_quote/backup.sh

# Tous les jours a 3h30
30 3 * * * /path/to/transport_quote/backup.sh

# Tous les dimanches a 1h (sauvegarde hebdomadaire)
0 1 * * 0 /path/to/transport_quote/backup.sh /mnt/weekly-backups/

# Tous les 1er du mois a 4h (sauvegarde mensuelle)
0 4 1 * * /path/to/transport_quote/backup.sh /mnt/monthly-backups/
```

**Verification** :

```bash
# Voir les taches cron actives
crontab -l

# Voir les logs de sauvegarde
tail -f /var/log/transport_quote_backup.log

# Tester manuellement
cd /path/to/transport_quote && ./backup.sh
```

### Alternative : Systemd Timer (Linux moderne)

Plus moderne et flexible que cron, avec meilleure gestion des erreurs :

```bash
# Creer /etc/systemd/system/transport-quote-backup.service
sudo tee /etc/systemd/system/transport-quote-backup.service > /dev/null <<EOF
[Unit]
Description=Transport Quote Backup

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/transport_quote
ExecStart=/home/ubuntu/transport_quote/backup.sh /mnt/backups/
StandardOutput=journal
StandardError=journal
EOF

# Creer /etc/systemd/system/transport-quote-backup.timer
sudo tee /etc/systemd/system/transport-quote-backup.timer > /dev/null <<EOF
[Unit]
Description=Transport Quote Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Activer et demarrer
sudo systemctl daemon-reload
sudo systemctl enable transport-quote-backup.timer
sudo systemctl start transport-quote-backup.timer

# Verifier le statut
sudo systemctl status transport-quote-backup.timer
sudo systemctl list-timers --all | grep transport-quote
```

### Alternative : Container Docker avec Cron

Ajouter un service de sauvegarde dans `docker-compose.yml` :

```yaml
backup:
  image: alpine:latest
  container_name: transport_quote_backup
  volumes:
    - ./backup.sh:/backup.sh:ro
    - ./backups:/backups
    - /var/run/docker.sock:/var/run/docker.sock
  environment:
    - BACKUP_SCHEDULE=0 2 * * *  # 2h du matin
  command: >
    sh -c "apk add --no-cache docker-cli dcron &&
           echo '$${BACKUP_SCHEDULE} /backup.sh /backups' > /etc/crontabs/root &&
           crond -f -l 2"
  restart: unless-stopped
  networks:
    - app-network
```

**Avantages** : Sauvegarde automatique meme si le serveur redémarre.

### Recommandation

Pour un serveur de production, **cron** est recommande car :
- Simple et fiable
- Natif sur Linux/macOS
- Pas de dependance externe
- Logs faciles a consulter

---

## 6. Ameliorations futures (non prioritaires)

Les ameliorations suivantes sont envisageables pour un guide plus mature, mais ne sont pas critiques pour une utilisation en production :

### 6.1. Script restore.sh

**Statut** : Non prioritaire  
**Justification** : La procedure manuelle de restauration est deja bien documentee et testable etape par etape. Un script automatise apporterait un gain de temps marginal et introduirait un risque d'erreur silencieuse en cas de probleme.

**Si implemente** : Le script devrait inclure des verifications strictes et demander confirmation avant chaque etape critique (suppression de la base existante, ecrasement de fichiers).

### 6.2. Scenarios de restauration avances

**Statut** : Non prioritaire  
**Justification** : Bonne idee pour un guide plus mature, mais les cas d'usage principaux (restauration complete, restauration partielle de la BD) sont deja couverts.

**Scenarios envisageables** :
- Restauration selective de tables PostgreSQL
- Migration vers un nouveau domaine (adaptation des certificats SSL)
- Restauration apres corruption partielle de donnees
- Rollback a une sauvegarde anterieure avec conservation des donnees recentes

### 6.3. Monitoring et retention long terme

**Statut** : Non prioritaire  
**Justification** : Ces aspects relevent plus de l'exploitation et de la supervision que du guide de backup lui-meme. Ils meritent une documentation separee (runbook d'exploitation).

**Elements a documenter ailleurs** :
- Alertes en cas d'echec de sauvegarde (email, Slack, PagerDuty)
- Verification automatique de la taille des archives (detection d'anomalies)
- Logs centralises des sauvegardes
- Tests de restauration automatises (trimestriels)
- Strategie de retention long terme (archivage mensuel sur 1 an)

---

## 7. Notes de securite

### Chiffrement des sauvegardes

Les archives de sauvegarde contiennent des donnees sensibles (mots de passe, cles secretes, donnees metier). Il est fortement recommande de les chiffrer avant tout transfert ou stockage :

```bash
# Chiffrer avec GPG (symetrique, par mot de passe)
gpg --symmetric --cipher-algo AES256 backup_transport_quote_*.tar.gz
# Produit : backup_transport_quote_*.tar.gz.gpg

# Dechiffrer
gpg --decrypt backup_transport_quote_*.tar.gz.gpg > backup_restored.tar.gz
```

```bash
# Alternative : chiffrer avec openssl
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -in backup_transport_quote_*.tar.gz \
  -out backup_transport_quote_encrypted.tar.gz.enc

# Dechiffrer
openssl enc -aes-256-cbc -d -pbkdf2 \
  -in backup_transport_quote_encrypted.tar.gz.enc \
  -out backup_restored.tar.gz
```

### Bonnes pratiques de stockage

| Regle                                | Detail                                                                    |
| ------------------------------------ | ------------------------------------------------------------------------- |
| **Regle 3-2-1**                      | 3 copies, 2 supports differents, 1 hors site                              |
| **Ne pas stocker les .env en clair** | Toujours chiffrer les sauvegardes contenant des secrets                   |
| **Limiter les acces**                | `chmod 600` sur les fichiers de sauvegarde                                |
| **Rotation**                         | Le script conserve automatiquement les 5 dernieres sauvegardes            |
| **Tester la restauration**           | Effectuer un test de restauration complet au moins une fois par trimestre |

### Checklist de securite

- [ ] Les sauvegardes sont chiffrees avant transfert
- [ ] Les fichiers `.env` ne sont jamais commites dans Git (verifier `.gitignore`)
- [ ] Les mots de passe de chiffrement sont stockes separement des sauvegardes
- [ ] Le serveur de sauvegarde a des acces restreints
- [ ] Les logs de sauvegarde sont surveilles (echecs, taille anormale)
- [ ] Un test de restauration est effectue regulierement
