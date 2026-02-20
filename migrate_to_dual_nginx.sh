#!/bin/bash
# =============================================================================
# migrate_to_dual_nginx.sh
#
# Script de MIGRATION vers l'architecture Dual-Nginx (Option A)
# À exécuter UNE SEULE FOIS sur le serveur de production.
#
# Ce script :
#   1. Sauvegarde l'ancienne configuration Nginx
#   2. Vérifie les prérequis (fichiers de config, certificats SSL)
#   3. Arrête l'ancienne architecture
#   4. Démarre la nouvelle architecture Dual-Nginx
#   5. Vérifie que tout fonctionne
#
# Usage : ./migrate_to_dual_nginx.sh
# =============================================================================

set -e  # Arrêter le script si une commande échoue

# --- Couleurs pour les messages ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_success() { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Répertoire du projet ---
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo ""
echo "============================================================"
echo "  Migration vers l'architecture Dual-Nginx (Option A)"
echo "============================================================"
echo ""
log_info "Répertoire projet : $PROJECT_DIR"
echo ""

# =============================================================================
# ÉTAPE 1 : Vérification des prérequis
# =============================================================================
log_info "Étape 1/6 : Vérification des prérequis..."

# Vérifier que docker-compose est disponible
if ! command -v docker &> /dev/null; then
    log_error "Docker n'est pas installé ou pas dans le PATH."
    exit 1
fi
log_success "Docker disponible : $(docker --version)"

# Vérifier que le fichier .env existe
if [ ! -f "$PROJECT_DIR/.env" ]; then
    log_error "Fichier .env introuvable. Créez-le à partir de .env.example."
    exit 1
fi
log_success "Fichier .env présent"

# Vérifier que les nouvelles configs Nginx existent
if [ ! -f "$PROJECT_DIR/nginx/external.conf" ]; then
    log_error "nginx/external.conf introuvable."
    exit 1
fi
log_success "nginx/external.conf présent"

if [ ! -f "$PROJECT_DIR/nginx/internal.conf" ]; then
    log_error "nginx/internal.conf introuvable."
    exit 1
fi
log_success "nginx/internal.conf présent"

# Vérifier la présence des certificats SSL (si Let's Encrypt est déjà configuré)
CERT_PATH="$PROJECT_DIR/certbot/conf/live/transportquote.duckdns.org"
if [ -d "$CERT_PATH" ]; then
    log_success "Certificats SSL présents dans $CERT_PATH"
else
    log_warning "Certificats SSL non trouvés dans $CERT_PATH"
    log_warning "Le Nginx External démarrera sans SSL (port 443 inactif)."
    log_warning "Lancez certbot après le démarrage pour obtenir vos certificats."
fi

echo ""

# =============================================================================
# ÉTAPE 2 : Sauvegarde de l'ancienne configuration
# =============================================================================
log_info "Étape 2/6 : Sauvegarde de l'ancienne configuration..."

BACKUP_DIR="$PROJECT_DIR/backup_old_nginx_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Sauvegarder l'ancien docker-compose si présent en git
if git diff --name-only HEAD 2>/dev/null | grep -q "docker-compose.yml"; then
    log_info "Sauvegarde git de l'état HEAD du docker-compose.yml..."
    git show HEAD:docker-compose.yml > "$BACKUP_DIR/docker-compose.yml.bak" 2>/dev/null || true
fi

# Sauvegarder l'ancienne config Nginx unique
if [ -f "$PROJECT_DIR/nginx-reverse-proxy.conf" ]; then
    cp "$PROJECT_DIR/nginx-reverse-proxy.conf" "$BACKUP_DIR/"
    log_success "Sauvegardé : nginx-reverse-proxy.conf → $BACKUP_DIR/"
fi

log_success "Backup créé dans : $BACKUP_DIR"
echo ""

# =============================================================================
# ÉTAPE 3 : Validation de la syntaxe Nginx
# =============================================================================
log_info "Étape 3/6 : Validation de la syntaxe des configs Nginx..."

# Note : nginx -t en dehors du réseau Docker échoue normalement car les
# upstreams (nginx-internal, frontend, backend) ne sont pas résolvables
# et les certificats SSL ne sont pas montés. On vérifie la syntaxe de base.

for conf in "external.conf" "internal.conf"; do
    CONF_PATH="$PROJECT_DIR/nginx/$conf"
    # Vérifier que le fichier n'est pas vide et contient des blocs server {}
    if grep -q "server {" "$CONF_PATH"; then
        log_success "nginx/$conf : structure OK (blocs server {} présents)"
    else
        log_error "nginx/$conf : fichier vide ou structure invalide"
        exit 1
    fi
done

# Test complet possible uniquement s'il n'y a pas de dépendances DNS externes
# (il sera validé au démarrage réel des containers)
log_info "La syntaxe complète sera validée au démarrage des containers."
echo ""

# =============================================================================
# ÉTAPE 4 : Arrêt de l'ancienne architecture
# =============================================================================
log_info "Étape 4/6 : Arrêt de l'ancienne architecture..."

# Arrêter et supprimer les containers existants (sans supprimer les volumes)
docker compose down --remove-orphans
log_success "Anciens containers arrêtés et supprimés"

echo ""

# =============================================================================
# ÉTAPE 5 : Démarrage de la nouvelle architecture
# =============================================================================
log_info "Étape 5/6 : Démarrage de la nouvelle architecture Dual-Nginx..."

# Démarrer tous les services en arrière-plan
docker compose up -d --build

log_success "Containers démarrés"
echo ""

# Attendre quelques secondes que les services s'initialisent
log_info "Attente de l'initialisation des services (15s)..."
sleep 15

echo ""

# =============================================================================
# ÉTAPE 6 : Vérification post-démarrage
# =============================================================================
log_info "Étape 6/6 : Vérification de l'architecture..."

echo ""
log_info "État des containers :"
docker compose ps
echo ""

# Vérifier que nginx-external tourne
if docker compose ps nginx-external | grep -q "running\|Up"; then
    log_success "nginx-external : UP"
else
    log_error "nginx-external : DOWN - vérifiez les logs : docker logs transport_quote_nginx_external"
fi

# Vérifier que nginx-internal tourne
if docker compose ps nginx-internal | grep -q "running\|Up"; then
    log_success "nginx-internal : UP"
else
    log_error "nginx-internal : DOWN - vérifiez les logs : docker logs transport_quote_nginx_internal"
fi

# Vérifier que le backend est healthy
if docker compose ps backend | grep -q "healthy"; then
    log_success "backend : HEALTHY"
else
    log_warning "backend : pas encore healthy (normal au démarrage)"
fi

echo ""

# Test de connectivité HTTP
log_info "Test HTTP sur localhost:80..."
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://localhost/ | grep -qE "^(200|301|302)"; then
    log_success "HTTP localhost:80 → répond correctement"
else
    log_warning "HTTP localhost:80 → pas de réponse (normal si pas encore prêt)"
fi

# Test health check nginx-internal
log_info "Test nginx-internal health check..."
if docker exec transport_quote_nginx_internal curl -s -o /dev/null -w "%{http_code}" http://localhost/nginx-health 2>/dev/null | grep -q "200"; then
    log_success "nginx-internal /nginx-health → 200 OK"
else
    log_warning "nginx-internal /nginx-health → vérifiez les logs"
fi

echo ""
echo "============================================================"
echo ""
log_success "Migration terminée !"
echo ""
echo "  Prochaines étapes :"
echo ""
echo "  1) Vérifier les logs en cas d'erreur :"
echo "     docker logs transport_quote_nginx_external"
echo "     docker logs transport_quote_nginx_internal"
echo ""
echo "  2) Si les certificats SSL sont absents, les obtenir :"
echo "     ./init-letsencrypt.sh"
echo ""
echo "  3) Tester l'accès HTTPS :"
echo "     curl -I https://transportquote.duckdns.org"
echo ""
echo "  4) Vérifier l'isolation réseau :"
echo "     # Le backend NE doit PAS accéder à Internet :"
echo "     docker exec transport_quote_backend curl --connect-timeout 5 https://example.com"
echo ""
echo "  Le backup de l'ancienne config est dans : $BACKUP_DIR"
echo ""
