# Deploiement sur un nouveau domaine

## Pre-requis

- Serveur Linux avec Docker et Docker Compose
- Nginx installe sur le host
- Certbot installe (`apt install certbot python3-certbot-nginx`)

## Etapes

### 1. DNS

Faire pointer le nouveau domaine vers l'IP du serveur (enregistrement A).

### 2. Variables d'environnement (`.env`)

Modifier `ALLOWED_ORIGINS` pour inclure le nouveau domaine :

```
ALLOWED_ORIGINS=https://nouveau-domaine.com
```

### 3. URL de l'API frontend (`docker-compose.yml`)

Modifier le build arg `VITE_API_URL` dans la section `frontend` :

```yaml
frontend:
  build:
    context: ./frontend
    args:
      VITE_API_URL: https://nouveau-domaine.com/transport/api/v1
      VITE_BASE_PATH: /transport/
```

### 4. Nginx reverse proxy (`nginx-reverse-proxy.conf`)

Modifier le `server_name` :

```nginx
server_name nouveau-domaine.com;
```

Puis copier la config et tester :

```bash
sudo cp nginx-reverse-proxy.conf /etc/nginx/sites-enabled/reverse-proxy.conf
sudo nginx -t
sudo nginx -s reload
```

### 5. Certificat SSL

Obtenir un certificat Let's Encrypt pour le nouveau domaine :

```bash
sudo certbot --nginx -d nouveau-domaine.com --redirect
```

### 6. Rebuild et redemarrage

```bash
sudo docker compose build frontend
sudo docker compose up -d frontend
```

## Verification

```bash
curl -s -o /dev/null -w "%{http_code}" https://nouveau-domaine.com/
curl -s -o /dev/null -w "%{http_code}" https://nouveau-domaine.com/transport/
curl -s -o /dev/null -w "%{http_code}" https://nouveau-domaine.com/transport/api/v1/quotes/count
```

Les trois commandes doivent retourner `200`.

## Fichiers concernes (resume)

| Fichier                   | Modification                          |
|---------------------------|---------------------------------------|
| `.env`                    | `ALLOWED_ORIGINS`                     |
| `docker-compose.yml`      | `VITE_API_URL` (build arg frontend)   |
| `nginx-reverse-proxy.conf`| `server_name`                         |
| Certbot (SSL)             | `certbot --nginx -d <domaine>`        |
