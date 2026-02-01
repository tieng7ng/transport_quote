# Guide de Déploiement en Production 🚀

Ce guide détaille les étapes pour déployer l'application **Transport Quote** sur un serveur de production (VPS type OVH, DigitalOcean, AWS EC2, etc.).

## 1. Architecture

L'application est composée de 4 services Docker orchestrés via Docker Compose :

1.  **Frontend** : Serveur Nginx servant l'application React et agissant comme "Reverse Proxy" (Port 80/443).
2.  **Backend** : API Python FastAPI (Port 3000, non exposé directement).
3.  **Postgres** : Base de données (Port 5432, non exposé directement).
4.  **Redis** : Cache et Broker de messages (Port 6379, non expossé directement).

> **Stratégie "Single Entry Point"** : En production, seul le conteneur **Frontend** sera accessible depuis l'extérieur. Il servira l'interface utilisateur ET redirigera les requêtes API vers le backend. Cela simplifie la gestion des ports et du SSL.

---

## 2. Prérequis

*   Un serveur Linux (Ubuntu 22.04 ou Debian 11 recommandé).
*   Un nom de domaine (ex: `app.mon-transport.com`) pointant vers l'IP du serveur.
*   **Docker** et **Docker Compose** installés sur le serveur.

### Installation rapide de Docker (si absent)
```bash
# Sur le serveur
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

---

## 3. Configuration de Production

### 3.1. Cloner le projet
```bash
git clone https://github.com/votre-user/transport_quote.git
cd transport_quote
```

### 3.2. Configuration des variables d'environnement (.env)
Créez un fichier `.env` à la racine (ne pas le commiter sur Git !).

```bash
nano .env
```

**Contenu exemple :**
```ini
# Base de données
POSTGRES_USER=admin_prod
POSTGRES_PASSWORD=CHANGER_CE_MOT_DE_PASSE_TRES_FORT !
POSTGRES_DB=transport_quote_prod

# Backend
# Secret Key pour JWT (générez en une avec `openssl rand -hex 32`)
SECRET_KEY=votre_super_secret_key_ici_123456
access_token_expire_minutes=10080

# URLs (Important pour CORS si besoin, mais moins critique avec le proxy Nginx)
FRONTEND_URL=https://app.mon-transport.com
BACKEND_URL=https://app.mon-transport.com/api

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
```

### 3.3. Adapter le Backend
Dans `backend/app/core/config.py` (ou via des variables d'environnement), assurez-vous que la connexion DB utilise les variables du `.env`.

### 3.4. Configuration Nginx (Reverse Proxy)
Pour la production, nous allons modifier la configuration Nginx du frontend pour qu'il proxy les requêtes API.

**Action requise :** Modifier `frontend/nginx.conf` (ou créer `nginx.prod.conf`) :

```nginx
server {
    listen 80;
    server_name app.mon-transport.com;  # Remplacer par votre domaine

    # Frontend (React)
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Backend API Proxy
    location /api/ {
        proxy_pass http://backend:3000/; # Notez le slash final
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3.5 Docker Compose Production
Créez un fichier `docker-compose.prod.yml` pour surcharger la config de dev.

```yaml
version: '3.8'

services:
  postgres:
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_prod_data:/var/lib/postgresql/data
    ports: [] # Ne pas exposer le port DB en prod !

  redis:
    ports: [] # Ne pas exposer Redis en prod !

  backend:
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_HOST: redis
    ports: [] # Ne pas exposer le backend directement !

  frontend:
    ports:
      - "80:80" # Expose le port 80 standard
    # Optionnel : Montage du nginx.conf prod si diffrent
    # volumes:
    #   - ./nginx.prod.conf:/etc/nginx/conf.d/default.conf

volumes:
  postgres_prod_data:
```

---

## 4. Lancement

Lancer l'application avec le fichier de prod :

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

---

## 5. Sécurisation SSL (HTTPS)

La méthode la plus simple est d'utiliser un **Reverse Proxy Nginx sur le serveur hôte** (installé via apt) qui gère le SSL et redirige vers Docker, OU d'utiliser un outil comme **Traefik** ou **Nginx Proxy Manager**.

### Méthode recommandée : Nginx Proxy Manager (Conteneurisé)
Si vous voulez tout gérer via Docker :

1.  Ajoutez le service "Nginx Proxy Manager" à votre stack.
2.  Connectez-le au même réseau.
3.  Dans l'interface Admin, faites pointer votre domaine vers le conteneur `frontend` sur le port 80.
4.  Activez "Force SSL" et "Let's Encrypt".

### Méthode "Certbot" rapide (Sur l'hôte)
Si vous avez installé Nginx sur le serveur hôte (`apt install nginx`).

1.  Configurez le Nginx hôte pour faire un `proxy_pass` vers `http://localhost:80` (le port exposé par Docker).
2.  Lancez `certbot --nginx` pour générer le certificat.

---

## 6. Utilisation Quotidienne

*   **Logs** : `docker compose logs -f`
*   **Mise à jour** :
    ```bash
    git pull
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
    ```
*   **Backup DB** :
    ```bash
    docker exec -t transport_quote_db pg_dumpall -c -U admin_prod > dump_$(date +%Y-%m-%d).sql
    ```
