#!/bin/bash

# ==============================================================================
# Setup des utilisateurs deploy et gitadmin - Transport Quote
# ==============================================================================
# Usage: sudo bash scripts/setup-users.sh
#
# Ce script crée :
#   - Groupe partagé "transport"
#   - Utilisateur "deploy"  (déploiement, docker, lecture repo)
#   - Utilisateur "gitadmin" (gestion git, push/tag/merge)
#
# Pré-requis :
#   - Exécuter en tant que root (sudo)
#   - Le groupe "docker" doit exister
# ==============================================================================

set -euo pipefail

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT_DIR="/home/ubuntu/opt/transport_quote"

log()   { echo -e "${GREEN}[OK]    $1${NC}"; }
warn()  { echo -e "${YELLOW}[WARN]  $1${NC}"; }
info()  { echo -e "${CYAN}[INFO]  $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}"; }

# ------------------------------------------------------------------------------
# Vérifications
# ------------------------------------------------------------------------------
if [ "$(id -u)" -ne 0 ]; then
    error "Ce script doit être exécuté en tant que root (sudo)."
    exit 1
fi

if ! getent group docker > /dev/null 2>&1; then
    error "Le groupe 'docker' n'existe pas. Installez Docker d'abord."
    exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
    error "Répertoire projet introuvable : $PROJECT_DIR"
    exit 1
fi

info "=== Setup des utilisateurs Transport Quote ==="

# ------------------------------------------------------------------------------
# 1. Création du groupe partagé "transport"
# ------------------------------------------------------------------------------
info "1. Création du groupe 'transport'..."
if getent group transport > /dev/null 2>&1; then
    warn "Le groupe 'transport' existe déjà."
else
    groupadd transport
    log "Groupe 'transport' créé."
fi

# ------------------------------------------------------------------------------
# 2. Création de l'utilisateur "deploy"
# ------------------------------------------------------------------------------
info "2. Création de l'utilisateur 'deploy'..."
if id deploy > /dev/null 2>&1; then
    warn "L'utilisateur 'deploy' existe déjà."
    # S'assurer qu'il est dans les bons groupes
    usermod -aG docker,transport deploy
    log "Groupes de 'deploy' mis à jour (docker, transport)."
else
    useradd -m -s /bin/bash -G docker,transport deploy
    log "Utilisateur 'deploy' créé (groupes: docker, transport)."
fi

# ------------------------------------------------------------------------------
# 3. Création de l'utilisateur "gitadmin"
# ------------------------------------------------------------------------------
info "3. Création de l'utilisateur 'gitadmin'..."
if id gitadmin > /dev/null 2>&1; then
    warn "L'utilisateur 'gitadmin' existe déjà."
    usermod -aG transport gitadmin
    log "Groupes de 'gitadmin' mis à jour (transport)."
else
    useradd -m -s /bin/bash -G transport gitadmin
    log "Utilisateur 'gitadmin' créé (groupe: transport)."
fi

# ------------------------------------------------------------------------------
# 4. Ajout de l'utilisateur "ubuntu" au groupe "transport"
# ------------------------------------------------------------------------------
info "4. Ajout de 'ubuntu' au groupe 'transport'..."
if id ubuntu > /dev/null 2>&1; then
    usermod -aG transport ubuntu
    log "Utilisateur 'ubuntu' ajouté au groupe 'transport'."
else
    warn "L'utilisateur 'ubuntu' n'existe pas, étape ignorée."
fi

# ------------------------------------------------------------------------------
# 5. Génération des clés SSH
# ------------------------------------------------------------------------------
info "5. Génération des clés SSH (ed25519)..."

generate_ssh_key() {
    local user=$1
    local home_dir
    home_dir=$(eval echo "~$user")
    local ssh_dir="$home_dir/.ssh"
    local key_file="$ssh_dir/id_ed25519"

    mkdir -p "$ssh_dir"

    if [ -f "$key_file" ]; then
        warn "Clé SSH de '$user' existe déjà : $key_file"
    else
        ssh-keygen -t ed25519 -C "${user}@transport-quote" -f "$key_file" -N ""
        log "Clé SSH générée pour '$user' : $key_file"
    fi

    # Permissions
    chown -R "$user:$user" "$ssh_dir"
    chmod 700 "$ssh_dir"
    chmod 600 "$key_file"
    chmod 644 "${key_file}.pub"
}

generate_ssh_key deploy
generate_ssh_key gitadmin

# ------------------------------------------------------------------------------
# 6. Configuration Git pour les utilisateurs
# ------------------------------------------------------------------------------
info "6. Configuration Git pour les utilisateurs..."

sudo -u deploy git config --global user.name "deploy"
sudo -u deploy git config --global user.email "deploy@transport-quote"

sudo -u gitadmin git config --global user.name "gitadmin"
sudo -u gitadmin git config --global user.email "gitadmin@transport-quote"

log "Configuration Git appliquée."

# ------------------------------------------------------------------------------
# 7. Permissions du répertoire projet
# ------------------------------------------------------------------------------
info "7. Ajustement des permissions du répertoire projet..."

# Changer le groupe owner en "transport"
chgrp -R transport "$PROJECT_DIR"

# Permissions : owner rwx, group r-x, others ---
# Le owner (ubuntu) garde le contrôle total
chmod -R u+rwX,g+rX,o-rwx "$PROJECT_DIR"

# Permettre l'écriture au groupe sur le répertoire .git (pour gitadmin)
chmod -R g+w "$PROJECT_DIR/.git"

# Setgid sur les répertoires pour que les nouveaux fichiers héritent du groupe
find "$PROJECT_DIR" -type d -exec chmod g+s {} +

log "Permissions ajustées sur $PROJECT_DIR"
log "  - Owner (ubuntu) : lecture/écriture/exécution"
log "  - Groupe (transport) : lecture/exécution"
log "  - .git : écriture pour le groupe (gitadmin)"
log "  - Others : aucun accès"

# ------------------------------------------------------------------------------
# 8. Configuration sudoers pour "deploy"
# ------------------------------------------------------------------------------
info "8. Configuration sudoers pour 'deploy'..."

SUDOERS_FILE="/etc/sudoers.d/deploy"

cat > "$SUDOERS_FILE" << 'EOF'
# Sudoers pour l'utilisateur deploy - Transport Quote
# Accès limité à docker compose et aux scripts de déploiement

deploy ALL=(root) NOPASSWD: /usr/bin/docker compose *
deploy ALL=(root) NOPASSWD: /usr/bin/docker-compose *
EOF

chmod 440 "$SUDOERS_FILE"

# Vérification de la syntaxe sudoers
if visudo -cf "$SUDOERS_FILE" > /dev/null 2>&1; then
    log "Fichier sudoers créé et validé : $SUDOERS_FILE"
else
    error "Erreur de syntaxe dans $SUDOERS_FILE — fichier supprimé par sécurité."
    rm -f "$SUDOERS_FILE"
    exit 1
fi

# ------------------------------------------------------------------------------
# 9. Résumé et affichage des clés publiques
# ------------------------------------------------------------------------------
echo ""
info "=========================================="
info "  SETUP TERMINÉ AVEC SUCCÈS"
info "=========================================="
echo ""

echo -e "${CYAN}Utilisateurs créés :${NC}"
echo "  deploy   — Groupes : $(id -nG deploy)"
echo "  gitadmin — Groupes : $(id -nG gitadmin)"
echo ""

echo -e "${CYAN}Clé publique de 'deploy' (deploy key read-only sur GitHub) :${NC}"
echo "---"
cat /home/deploy/.ssh/id_ed25519.pub
echo "---"
echo ""

echo -e "${CYAN}Clé publique de 'gitadmin' (deploy key read-write sur GitHub) :${NC}"
echo "---"
cat /home/gitadmin/.ssh/id_ed25519.pub
echo "---"
echo ""

echo -e "${YELLOW}Actions manuelles restantes :${NC}"
echo "  1. Ajouter la clé de 'deploy' comme Deploy Key READ-ONLY sur GitHub"
echo "     → https://github.com/tieng7ng/transport_quote/settings/keys"
echo "  2. Ajouter la clé de 'gitadmin' comme Deploy Key READ-WRITE sur GitHub"
echo "     → https://github.com/tieng7ng/transport_quote/settings/keys"
echo ""
echo -e "${YELLOW}Test rapide :${NC}"
echo "  sudo -u deploy bash -c 'cd $PROJECT_DIR && git fetch --tags'"
echo "  sudo -u deploy bash -c 'docker ps'"
echo "  sudo -u gitadmin bash -c 'cd $PROJECT_DIR && git status'"
echo ""
