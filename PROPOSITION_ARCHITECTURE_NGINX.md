# Proposition d'architecture Nginx — Double couche proxy

## Contexte : architecture actuelle

```
Internet (ports 80/443 exposés)
         │
   [nginx] ─── app-network (bridge)
    /    \           │
[front] [back]  [redis] [postgres] [certbot]
```

**Problèmes identifiés :**
- Un réseau unique `app-network` : si nginx est compromis, l'attaquant atteint directement postgres et redis
- nginx cumule TLS, routing et sécurité sans isolation
- postgres et redis sont sur le même plan réseau que le proxy exposé
- Le port 8080 expose en clair une deuxième entrée HTTP non nécessaire en production

---

## Principe cible : segmentation réseau avec deux Nginx

```
Internet (port 80/443 uniquement)
         │
  [nginx-edge]          ← Zone DMZ (réseau dmz-net)
         │                TLS, rate-limit, headers sécurité
  [nginx-internal]      ← Pivot sur deux réseaux
         │                Routing interne, pas de port exposé
    ─────┼──────────────────────────────────
    [frontend]  [backend]  [redis]  [postgres]
                          └─ réseau internal-net (internal: true)
```

Les deux réseaux :
- `dmz-net` : bridge classique, partagé entre nginx-edge et nginx-internal
- `internal-net` : bridge avec `internal: true` (Docker bloque tout routage vers l'extérieur) — seuls les conteneurs membres peuvent se parler

---

## Option 1 — Double nginx + segmentation réseau (recommandée)

**Principe :** nginx-edge gère uniquement la terminaison TLS et les politiques de sécurité périmétrique. nginx-internal gère le routing vers les services.

### Avantages
- postgres et redis sont sur `internal-net` uniquement, inaccessibles depuis la DMZ
- Séparation claire des responsabilités
- Un seul point d'entrée externe (ports 80/443 sur nginx-edge)
- Si nginx-edge est compromis, il ne voit que nginx-internal

### Inconvénients
- Double hop HTTP (légère latence, ~1ms sur localhost)
- Deux configs nginx à maintenir

### Structure docker-compose (option 1)

```yaml
networks:
  dmz-net:
    driver: bridge
  internal-net:
    driver: bridge
    internal: true   # aucun routage vers l'extérieur possible

services:
  nginx-edge:
    image: nginx:1.25-alpine
    container_name: transport_nginx_edge
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/edge.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    networks:
      - dmz-net
    depends_on:
      - nginx-internal
    restart: always

  nginx-internal:
    image: nginx:1.25-alpine
    container_name: transport_nginx_internal
    # Aucun port exposé vers l'hôte
    volumes:
      - ./nginx/internal.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - dmz-net       # reçoit de nginx-edge
      - internal-net  # accède aux services
    depends_on:
      backend:
        condition: service_healthy
      frontend:
        condition: service_started
    restart: always

  certbot:
    image: certbot/certbot
    container_name: transport_certbot
    volumes:
      - ./certbot/conf:/etc/letsencrypt
      - ./certbot/www:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - dmz-net

  backend:
    build: ./backend
    container_name: transport_backend
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      REDIS_PASSWORD: ${REDIS_PASSWORD}
      UPLOAD_DIR: /app/uploads
      PARTNER_CONFIGS_DIR: /app/configs/partners
      SECRET_KEY: ${SECRET_KEY}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS}
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/configs:/app/configs
      - ./file_import:/app/file_import
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - internal-net  # jamais sur dmz-net
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M

  frontend:
    build:
      context: ./frontend
      args:
        VITE_API_URL: /transport/api/v1
    container_name: transport_frontend
    networks:
      - internal-net  # jamais sur dmz-net
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M

  postgres:
    image: postgres:16-alpine
    container_name: transport_db
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - internal-net  # jamais sur dmz-net
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M

  redis:
    image: redis:7-alpine
    container_name: transport_redis
    command: redis-server --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - internal-net  # jamais sur dmz-net
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.25'
          memory: 256M

volumes:
  postgres_data:
```

### Configuration nginx-edge (`nginx/edge.conf`)

```nginx
# HTTP → HTTPS + ACME challenge
server {
    listen 80;
    server_name transportquote.duckdns.org;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name transportquote.duckdns.org;

    ssl_certificate     /etc/letsencrypt/live/transportquote.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/transportquote.duckdns.org/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;
    ssl_session_cache   shared:SSL:10m;

    # En-têtes sécurité périmétrique
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' https: data: blob: 'unsafe-inline'" always;

    # Rate limiting global (défini dans nginx.conf principal)
    # limit_req zone=global burst=50 nodelay;

    # Tout le trafic va vers nginx-internal — pas de connaissance des services
    location / {
        proxy_pass         http://nginx-internal:80;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

### Configuration nginx-internal (`nginx/internal.conf`)

```nginx
server {
    listen 80;
    server_name _;

    # Frontend React
    location / {
        proxy_pass         http://frontend:80;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $http_x_real_ip;
        proxy_set_header   X-Forwarded-For   $http_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $http_x_forwarded_proto;
    }

    # API Backend FastAPI
    location /transport/api/ {
        proxy_pass         http://backend:3000/api/;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $http_x_real_ip;
        proxy_set_header   X-Forwarded-For   $http_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $http_x_forwarded_proto;
        client_max_body_size 50M;
        proxy_read_timeout   120s;
    }
}
```

---

## Option 2 — Double nginx + ModSecurity WAF sur l'edge

**Principe :** même segmentation réseau que l'option 1, mais l'image nginx-edge est remplacée par `owasp/modsecurity-crs:nginx-alpine`, qui embarque un Web Application Firewall.

### Avantages supplémentaires vs option 1
- Filtrage OWASP Top 10 (SQLi, XSS, LFI, RCE…) au niveau périmétrique
- Les logs d'attaques sont isolés sur nginx-edge
- Détection automatique de patterns d'attaques connues

### Inconvénients supplémentaires
- Faux positifs possibles (règles à ajuster selon l'application)
- Image plus lourde (~200MB vs ~25MB)
- Configuration plus complexe

### Modification du docker-compose

```yaml
  nginx-edge:
    image: owasp/modsecurity-crs:nginx-alpine
    container_name: transport_nginx_edge
    ports:
      - "80:80"
      - "443:443"
    environment:
      BACKEND: "http://nginx-internal:80"
      MODSEC_RULE_ENGINE: "On"
      PARANOIA: 1           # Niveau 1 à 4 (1 = peu de faux positifs)
      ANOMALY_INBOUND: 5    # Score seuil pour bloquer
      ANOMALY_OUTBOUND: 4
    volumes:
      - ./nginx/edge-waf.conf:/etc/nginx/templates/conf.d/default.conf.template:ro
      - ./certbot/conf:/etc/letsencrypt:ro
      - ./certbot/www:/var/www/certbot:ro
    networks:
      - dmz-net
    restart: always
```

---

## Option 3 — Nginx Edge + Traefik interne (discovery automatique)

**Principe :** nginx-edge reste en DMZ pour la terminaison TLS. L'orchestration interne est assurée par Traefik, qui découvre les services via les labels Docker.

### Avantages
- Pas de configuration nginx-internal à maintenir manuellement
- Ajout de nouveaux services sans modifier la config (labels sur le conteneur)
- Dashboard Traefik pour visualiser les routes (accessible en interne uniquement)
- Middleware intégrés (auth, retry, circuit breaker)

### Inconvénients
- Traefik a accès au socket Docker (`/var/run/docker.sock`) — surface d'attaque plus large
- Courbe d'apprentissage Traefik
- Moins prévisible que nginx pour du routing simple

### Structure partielle

```yaml
  traefik:
    image: traefik:v3.0
    container_name: transport_traefik
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.docker.network=internal-net"
      - "--entrypoints.web.address=:80"
      - "--api.dashboard=true"
      - "--api.insecure=false"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - dmz-net
      - internal-net
    restart: always

  frontend:
    # ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.frontend.rule=PathPrefix(`/`)"
      - "traefik.http.services.frontend.loadbalancer.server.port=80"
    networks:
      - internal-net

  backend:
    # ...
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.backend.rule=PathPrefix(`/transport/api/`)"
      - "traefik.http.services.backend.loadbalancer.server.port=3000"
    networks:
      - internal-net
```

---

## Comparaison des options

| Critère                         | Option 1 (double nginx) | Option 2 (+ WAF)     | Option 3 (Traefik)   |
|---------------------------------|------------------------|----------------------|----------------------|
| Isolation réseau                | Forte                  | Forte                | Forte                |
| Complexité de mise en place     | Faible                 | Moyenne              | Moyenne              |
| Maintenabilité                  | Bonne                  | Bonne                | Très bonne           |
| Protection applicative (WAF)    | Non                    | Oui (OWASP CRS)      | Partielle (middleware)|
| Accès socket Docker             | Non                    | Non                  | Oui (risque)         |
| Ressources supplémentaires      | Faibles (~25MB)        | Élevées (~200MB)     | Moyennes (~100MB)    |
| Adapté à ce projet              | Oui (recommandé)       | Si exposition forte  | Si services multiples|

---

## Recommandation

**Option 1** est la mieux adaptée à ce projet :
- L'application n'est pas exposée à un trafic massif nécessitant un WAF
- L'architecture est simple et lisible
- La segmentation réseau (`internal: true`) protège postgres et redis efficacement
- Zéro port exposé sur les services métier

Si le projet monte en charge ou est exposé publiquement sans pare-feu devant, passer à **Option 2** en remplaçant uniquement l'image nginx-edge.

---

## Migration depuis l'architecture actuelle

1. Créer le dossier `nginx/` à la racine du projet
2. Déplacer `nginx-reverse-proxy.conf` → `nginx/edge.conf` et l'adapter (voir ci-dessus)
3. Créer `nginx/internal.conf` (voir ci-dessus)
4. Modifier `docker-compose.yml` :
   - Renommer le service `nginx` → `nginx-edge` + `nginx-internal`
   - Supprimer `app-network`, créer `dmz-net` et `internal-net`
   - Affecter chaque service au bon réseau
   - Supprimer le port `8080:80` (non nécessaire en production)
5. `docker compose down && docker compose up -d`

> **Note réseau interne :** avec `internal: true`, les conteneurs sur `internal-net` ne peuvent pas initier de connexions vers l'extérieur (pas d'accès internet). Si le backend doit appeler des API externes, il faut lui ajouter une route vers un troisième réseau bridge standard (ou utiliser un proxy HTTP sortant dédié).
