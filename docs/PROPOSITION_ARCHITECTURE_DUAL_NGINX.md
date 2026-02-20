# Proposition d'Architecture Dual-Nginx

## Contexte

Actuellement, l'application utilise un seul Nginx reverse proxy (`nginx-reverse-proxy.conf`) exposé sur les ports 80/443 qui route directement vers les containers `frontend` (port 80) et `backend` (port 3000) via le réseau Docker `app-network`. Tous les services partagent le même réseau, ce qui signifie que chaque container peut communiquer avec n'importe quel autre container.

**Problème identifié :** si un attaquant compromet le reverse proxy, il a accès direct à tous les services internes (PostgreSQL, Redis, Backend) via le réseau partagé.

---

## Architecture Cible

Mettre en place **deux containers Nginx** avec **isolation réseau** via des réseaux Docker séparés :

- **Nginx External (DMZ)** : seul point d'entrée depuis l'extérieur (ports 80/443)
- **Nginx Internal** : routeur interne qui distribue le trafic vers les services applicatifs

```
                    INTERNET
                       │
                       ▼
              ┌────────────────┐
              │  Nginx External│    Réseau: dmz-network
              │  (DMZ Proxy)   │    Ports exposés: 80, 443
              │                │
              │  SSL/TLS       │
              │  Rate Limiting │
              │  WAF Rules     │
              │  Security Hdrs │
              └───────┬────────┘
                      │
            ══════════╧═══════════  dmz-network (bridge)
                      │
              ┌───────┴────────┐
              │ Nginx Internal │    Réseaux: dmz-network + app-network
              │ (App Router)   │
              │                │
              │  Load Balance  │
              │  Circuit Break │
              │  Access Control│
              └──┬──────────┬──┘
                 │          │
       ══════════╧══════════╧═══  app-network (internal, driver: bridge)
                 │          │
         ┌───────┴──┐  ┌───┴────────┐
         │ Frontend │  │  Backend   │
         │ (React)  │  │  (FastAPI) │
         │ port 80  │  │  port 3000 │
         └──────────┘  └─────┬──┬───┘
                             │  │
                    ┌────────┘  └────────┐
                    │                    │
              ┌─────┴──────┐     ┌──────┴─────┐
              │ PostgreSQL │     │   Redis    │
              │ port 5432  │     │  port 6379 │
              └────────────┘     └────────────┘

              ───────── app-network (internal) ─────────
```

---

## Comprendre le flux HTTPS : de ton navigateur à l'application

### Le trajet complet d'une requête

Quand tu tapes `https://transportquote.duckdns.org` dans ton navigateur, voici ce qui se passe :

```
 TON NAVIGATEUR
      │
      │ 1. Résolution DNS
      ▼
 DuckDNS (DNS)  ──▶  renvoie l'IP publique de ton serveur
      │
      │ 2. Connexion TCP sur le port 443
      ▼
 TA BOX / ROUTEUR
      │
      │ 3. NAT : redirige le port 443 vers ton serveur local
      ▼
 TON SERVEUR (port 443)
      │
      │ 4. Docker redirige le port 443 vers le container
      ▼
 NGINX EXTERNAL (container, port 443)
      │
      │ 5. Handshake TLS (certificat Let's Encrypt)
      │ 6. Déchiffre la requête HTTPS → HTTP en clair
      │ 7. Ajoute les headers de sécurité
      │ 8. Forward en HTTP vers le réseau interne
      ▼
 NGINX INTERNAL (container, port 80)
      │
      │ 9. Route vers le bon service
      ├──────────────────────┐
      ▼                      ▼
 FRONTEND (/)         BACKEND (/transport/api/)
```

### Détail de chaque étape

#### 1. Résolution DNS (`duckdns.org`)

Ton navigateur demande "quelle est l'IP de `transportquote.duckdns.org` ?" Le service DuckDNS répond avec **l'IP publique de ta box** (ex: `86.234.x.x`). Tu as configuré ça sur [duckdns.org](https://www.duckdns.org).

#### 2-3. Ta box / routeur

Ton routeur reçoit la connexion sur le **port 443** (HTTPS) depuis Internet. Dans la configuration NAT/Port Forwarding de ta box, tu as une règle :

```
Port externe 443  →  IP locale du serveur : port 443
Port externe 80   →  IP locale du serveur : port 80
```

Sans cette règle, la requête s'arrête à ta box.

#### 4. Docker fait le lien

Dans le `docker-compose.yml`, la ligne `ports: "443:443"` du Nginx External fait que Docker écoute sur le port 443 de la machine hôte et redirige vers le port 443 **à l'intérieur** du container.

#### 5-6. Le chiffrement SSL/TLS (le coeur du HTTPS)

C'est ici que la "magie" du HTTPS se passe. Le Nginx External :

**a) Possède le certificat SSL** (généré par Let's Encrypt via Certbot) :

```nginx
ssl_certificate     /etc/letsencrypt/live/transportquote.duckdns.org/fullchain.pem;  # clé publique
ssl_certificate_key /etc/letsencrypt/live/transportquote.duckdns.org/privkey.pem;     # clé privée
```

**b) Fait le "handshake TLS"** avec ton navigateur :

```
Navigateur : "Bonjour, je veux parler en HTTPS"
Nginx      : "Voici mon certificat (signé par Let's Encrypt)"
Navigateur : "Je fais confiance à Let's Encrypt, OK. Voici une clé de session chiffrée"
Nginx      : "Reçu. On communique maintenant avec cette clé"
             → Tout le trafic est chiffré entre les deux
```

**c) Déchiffre** la requête HTTPS et la transforme en HTTP simple pour la transmettre en interne. C'est ce qu'on appelle la **terminaison SSL** : le chiffrement s'arrête au Nginx External.

#### 7-8. Forward vers le réseau interne

Le trafic circule **en HTTP non chiffré** entre Nginx External et Nginx Internal. Ce n'est pas un problème car :
- C'est un **réseau Docker interne** (pas Internet)
- Seuls les containers sur `dmz-network` voient ce trafic
- C'est comme parler dans une pièce fermée

#### 9. Routage applicatif

Le Nginx Internal regarde l'URL et décide :
- `/transport/api/*` → envoie au **Backend** (port 3000)
- `/` (tout le reste) → envoie au **Frontend** (port 80)

### Comment le certificat SSL est obtenu et renouvelé

```
1. Certbot demande un certificat à Let's Encrypt
2. Let's Encrypt dit : "Prouve que tu possèdes ce domaine,
   place ce fichier dans /.well-known/acme-challenge/"
3. Certbot place le fichier (volume partagé avec Nginx)
4. Let's Encrypt vérifie en appelant :
   http://transportquote.duckdns.org/.well-known/acme-challenge/xxx
5. Vérification OK → certificat délivré (valide 90 jours)
6. Le container Certbot renouvelle automatiquement toutes les 12h
```

C'est pour ça que le **port 80 doit rester ouvert** : Let's Encrypt en a besoin pour le challenge HTTP, même si ensuite tout le trafic utilisateur passe par le 443.

### Résumé du chiffrement par segment

| Segment | Protocole | Chiffré ? |
|---|---|---|
| Navigateur → Ta box | HTTPS | Oui |
| Ta box → Nginx External | HTTPS | Oui |
| Nginx External → Nginx Internal | HTTP | Non (réseau Docker isolé) |
| Nginx Internal → Frontend/Backend | HTTP | Non (réseau Docker isolé) |

Le **Nginx External est le seul** à connaître la clé privée SSL. Il est le gardien qui déchiffre le trafic extérieur et le redistribue en interne de manière sécurisée.

---

## Proposition A : Dual-Nginx avec isolation réseau (Recommandée)

### Principe

Séparer le réseau en **deux zones** :

| Réseau | Type | Services | Accès externe |
|---|---|---|---|
| `dmz-network` | bridge | Nginx External, Nginx Internal | Oui (ports 80/443) |
| `app-network` | **internal** | Nginx Internal, Frontend, Backend, PostgreSQL, Redis | **Non** |

Le Nginx Internal est le **seul service connecté aux deux réseaux**, faisant office de passerelle contrôlée.

### Avantages

- **Isolation forte** : les services applicatifs (backend, DB, cache) ne sont pas accessibles depuis le réseau DMZ
- **Défense en profondeur** : compromission du Nginx External ne donne pas accès aux services internes
- **Séparation des responsabilités** : SSL/sécurité externe vs routage applicatif interne
- **Possibilité de WAF** : le Nginx External peut embarquer ModSecurity ou des règles de filtrage avancées
- **Scalabilité** : le Nginx Internal peut faire du load balancing vers plusieurs instances backend

### Inconvénients

- Complexité accrue (2 configs Nginx à maintenir)
- Légère latence additionnelle (un hop réseau supplémentaire)
- Debugging plus complexe (traces à suivre à travers 2 proxies)

### Configuration docker-compose

```yaml
services:
  # ============================================================
  # ZONE DMZ - Exposée à l'extérieur
  # ============================================================
  nginx-external:
    image: nginx:1.25-alpine
    container_name: transport_quote_nginx_external
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/external.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    networks:
      - dmz-network
    depends_on:
      nginx-internal:
        condition: service_started
    restart: always
    deploy:
      resources:
        limits:
          cpus: "0.25"
          memory: 128M

  certbot:
    image: certbot/certbot
    container_name: transport_quote_certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    networks:
      - dmz-network
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"

  # ============================================================
  # ZONE INTERNE - Passerelle entre DMZ et App
  # ============================================================
  nginx-internal:
    image: nginx:1.25-alpine
    container_name: transport_quote_nginx_internal
    volumes:
      - ./nginx/internal.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - dmz-network
      - app-network
    depends_on:
      backend:
        condition: service_healthy
      frontend:
        condition: service_started
    restart: always
    deploy:
      resources:
        limits:
          cpus: "0.25"
          memory: 128M

  # ============================================================
  # ZONE APPLICATIVE - Isolée de l'extérieur
  # ============================================================
  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: /transport/api/v1
    container_name: transport_quote_frontend
    networks:
      - app-network
    # Pas de ports exposés
    restart: always
    deploy:
      resources:
        limits:
          cpus: "0.50"
          memory: 512M

  backend:
    build:
      context: ./backend
    container_name: transport_quote_backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
      - UPLOAD_DIR=/app/uploads
      - PARTNER_CONFIGS_DIR=/app/configs/partners
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/configs:/app/configs
      - ./file_import:/app/file_import
    networks:
      - app-network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    # Pas de ports exposés
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: always
    deploy:
      resources:
        limits:
          cpus: "0.50"
          memory: 512M

  postgres:
    image: postgres:16-alpine
    container_name: transport_quote_db
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network
    # Pas de ports exposés
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always
    deploy:
      resources:
        limits:
          cpus: "0.50"
          memory: 512M

  redis:
    image: redis:7-alpine
    container_name: transport_quote_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    networks:
      - app-network
    # Pas de ports exposés
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always
    deploy:
      resources:
        limits:
          cpus: "0.25"
          memory: 256M

# ============================================================
# RESEAUX
# ============================================================
networks:
  dmz-network:
    driver: bridge
    # Réseau accessible depuis l'extérieur (via ports exposés)
  app-network:
    driver: bridge
    internal: true
    # IMPORTANT: "internal: true" empêche tout accès extérieur
    # Les containers sur ce réseau ne peuvent PAS accéder à Internet

volumes:
  postgres_data:
```

### Configuration Nginx External (`nginx/external.conf`)

```nginx
# ============================================================
# Nginx External - Point d'entrée DMZ
# Rôle : SSL, sécurité, filtrage, forward vers Nginx Internal
# ============================================================

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login_limit:10m rate=3r/m;
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

# Redirect HTTP -> HTTPS
server {
    listen 80;
    server_name transportquote.duckdns.org;

    # ACME challenge pour Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS - Point d'entrée principal
server {
    listen 443 ssl;
    http2 on;
    server_name transportquote.duckdns.org;

    # --- SSL ---
    ssl_certificate /etc/letsencrypt/live/transportquote.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/transportquote.duckdns.org/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_stapling on;
    ssl_stapling_verify on;

    # --- Security Headers ---
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: blob: 'unsafe-inline'" always;
    add_header X-Request-ID $request_id always;

    # --- Limites globales ---
    limit_conn conn_limit 20;
    client_max_body_size 50M;

    # --- Bloquer les user-agents malveillants ---
    if ($http_user_agent ~* (bot|crawler|spider|scraper|wget|curl)) {
        # Autoriser les bots légitimes si nécessaire
        # return 403;
    }

    # --- Bloquer les chemins sensibles ---
    location ~ /\. {
        deny all;
        return 404;
    }

    location ~* ^/(wp-admin|wp-login|phpmyadmin|admin|\.env|\.git) {
        deny all;
        return 404;
    }

    # --- Rate limiting sur l'API login ---
    location /transport/api/v1/auth/login {
        limit_req zone=login_limit burst=5 nodelay;
        proxy_pass http://nginx-internal;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
    }

    # --- API avec rate limiting ---
    location /transport/api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://nginx-internal;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
    }

    # --- Frontend (moins de restrictions) ---
    location / {
        proxy_pass http://nginx-internal;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Request-ID $request_id;
    }
}
```

### Configuration Nginx Internal (`nginx/internal.conf`)

```nginx
# ============================================================
# Nginx Internal - Routeur applicatif
# Rôle : routage vers frontend/backend, pas de SSL (trafic interne)
# ============================================================

# Upstreams avec health checks
upstream frontend_upstream {
    server frontend:80;
    # Possibilité d'ajouter des instances pour le load balancing :
    # server frontend-2:80;
}

upstream backend_upstream {
    server backend:3000;
    # Possibilité d'ajouter des instances :
    # server backend-2:3000;
}

server {
    listen 80;
    server_name _;

    # --- Vérifier que la requête vient du Nginx External ---
    # Accepter uniquement les requêtes avec le header X-Request-ID
    # (ajouté par le Nginx External)
    # Optionnel mais renforce la sécurité :
    # if ($http_x_request_id = "") {
    #     return 403;
    # }

    # --- Logs internes ---
    access_log /var/log/nginx/internal_access.log;
    error_log /var/log/nginx/internal_error.log warn;

    # --- API Backend ---
    location /transport/api/ {
        proxy_pass http://backend_upstream/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $http_x_real_ip;
        proxy_set_header X-Forwarded-For $http_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
        proxy_set_header X-Request-ID $http_x_request_id;

        # Timeouts
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering pour les réponses volumineuses
        proxy_buffering on;
        proxy_buffer_size 16k;
        proxy_buffers 4 32k;

        client_max_body_size 50M;
    }

    # --- Frontend ---
    location / {
        proxy_pass http://frontend_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $http_x_real_ip;
        proxy_set_header X-Forwarded-For $http_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;

        # Cache des assets statiques
        proxy_cache_valid 200 1h;
    }

    # --- Health check endpoint (pour monitoring interne) ---
    location /nginx-health {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

---

## Proposition B : Dual-Nginx avec réseau dédié pour la base de données

### Principe

Aller plus loin dans l'isolation en ajoutant un **troisième réseau** pour la base de données :

| Réseau | Type | Services |
|---|---|---|
| `dmz-network` | bridge | Nginx External, Nginx Internal |
| `app-network` | internal | Nginx Internal, Frontend, Backend |
| `data-network` | internal | Backend, PostgreSQL, Redis |

```
    INTERNET
       │
  ┌────┴─────┐
  │  Nginx   │     dmz-network
  │ External │
  └────┬─────┘
       │
  ┌────┴─────┐
  │  Nginx   │     dmz-network + app-network
  │ Internal │
  └──┬────┬──┘
     │    │
  ┌──┴─┐ ┌┴────────┐
  │ FE │ │ Backend │    app-network + data-network
  └────┘ └─┬────┬──┘
           │    │
     ┌─────┴┐ ┌┴─────┐
     │ PgSQL│ │Redis │    data-network
     └──────┘ └──────┘
```

### Avantages supplémentaires

- Le Frontend ne peut **jamais** communiquer avec PostgreSQL/Redis
- Même si le Frontend est compromis, les données sont protégées
- Principe du moindre privilège appliqué à chaque service

### Inconvénients

- Plus complexe à maintenir
- Peut compliquer le debugging
- Nécessite de bien documenter la topologie

### Delta de configuration

Seules les sections `networks` changent :

```yaml
services:
  nginx-internal:
    networks:
      - dmz-network
      - app-network
      # PAS de data-network

  frontend:
    networks:
      - app-network
      # PAS de data-network : le frontend n'a pas besoin d'accéder à la DB

  backend:
    networks:
      - app-network
      - data-network
      # Connecté aux deux pour recevoir le trafic ET accéder aux données

  postgres:
    networks:
      - data-network
      # Uniquement sur le réseau données

  redis:
    networks:
      - data-network
      # Uniquement sur le réseau données

networks:
  dmz-network:
    driver: bridge
  app-network:
    driver: bridge
    internal: true
  data-network:
    driver: bridge
    internal: true
```

---

## Proposition C : Nginx External + Nginx Interne avec Fail2ban

### Principe

Même architecture que la Proposition A, mais avec un sidecar **Fail2ban** qui analyse les logs du Nginx External pour bannir automatiquement les IPs malveillantes.

### Architecture additionnelle

```
  ┌─────────────┐     ┌──────────┐
  │ Nginx Ext.  │────▶│ Fail2ban │
  │ (logs)      │     │ (sidecar)│
  └─────────────┘     └──────────┘
        │                   │
        │              iptables/
        │              nftables
        ▼
  ┌─────────────┐
  │ Nginx Int.  │
  └─────────────┘
```

### Service additionnel

```yaml
  fail2ban:
    image: crazymax/fail2ban:latest
    container_name: transport_quote_fail2ban
    network_mode: host
    cap_add:
      - NET_ADMIN
      - NET_RAW
    volumes:
      - ./nginx/logs:/var/log/nginx:ro
      - ./fail2ban/jail.d:/etc/fail2ban/jail.d:ro
      - ./fail2ban/filter.d:/etc/fail2ban/filter.d:ro
      - fail2ban_data:/var/lib/fail2ban
    restart: always
```

### Config Fail2ban (`fail2ban/jail.d/nginx.conf`)

```ini
[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/external_access.log
maxretry = 5
bantime = 3600

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
logpath = /var/log/nginx/external_access.log
maxretry = 2
bantime = 86400

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/external_error.log
maxretry = 10
bantime = 7200
```

---

## Tableau comparatif

| Critère | Actuel | Prop. A | Prop. B | Prop. C |
|---|---|---|---|---|
| **Isolation réseau** | Aucune (1 réseau) | Bonne (2 réseaux) | Maximale (3 réseaux) | Bonne (2 réseaux) |
| **Protection DB** | Faible | Moyenne | Forte | Moyenne |
| **Complexité** | Simple | Modérée | Élevée | Modérée+ |
| **Performance** | Optimale | ~identique | ~identique | ~identique |
| **Protection DDoS** | Aucune | Rate limiting | Rate limiting | Rate limiting + ban IP |
| **Maintenance** | 1 config Nginx | 2 configs | 2 configs + 3 réseaux | 2 configs + Fail2ban |
| **Debugging** | Simple | Modéré | Complexe | Modéré |
| **Coût mémoire additionnel** | - | ~128 Mo | ~128 Mo | ~256 Mo |

---

## Recommandation

**Pour votre cas d'usage, je recommande la Proposition A** (Dual-Nginx avec isolation réseau) car :

1. Elle apporte un **gain de sécurité significatif** par rapport à l'architecture actuelle
2. La complexité reste **raisonnable** pour une petite équipe
3. Le réseau `internal: true` de Docker empêche physiquement tout accès externe aux services applicatifs
4. Elle est **évolutive** : on peut facilement passer à la Proposition B ou C plus tard

### Migration depuis l'architecture actuelle

Les changements nécessaires sont :

1. Créer le dossier `nginx/` avec `external.conf` et `internal.conf`
2. Remplacer le service `nginx` unique par `nginx-external` et `nginx-internal`
3. Passer `app-network` en `internal: true`
4. Ajouter `dmz-network`
5. Supprimer les ports exposés des services internes (déjà le cas actuellement)
6. Tester la connectivité entre les zones

### Points d'attention

- **`internal: true`** empêche les containers de ce réseau d'accéder à Internet. Si le backend doit appeler des APIs externes (webhooks, email, etc.), il faudra ajouter un réseau `egress-network` dédié.
- Les **healthchecks Docker** fonctionnent en local dans chaque container, donc ne sont pas impactés par l'isolation réseau.
- Le **Nginx Internal ne doit PAS exposer de ports** sur l'hôte.
