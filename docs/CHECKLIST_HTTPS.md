# Checklist de Deploiement HTTPS

Guide pas-a-pas pour passer l'application Transport Quote en HTTPS.

**Serveur :** Ubuntu (`/home/ubuntu/opt/transport_quote`)
**Architecture :** Nginx reverse proxy (hote) -> Docker containers (frontend:8081, backend:3000)
**Domaine :** `transportquote.duckdns.org`
**IP :** `135.125.103.119`

---

## Etape 1 : Configurer DuckDNS

> DuckDNS est un service DNS dynamique gratuit. Le domaine `transportquote.duckdns.org` doit pointer vers l'IP du serveur.

- [ ] Se connecter a https://www.duckdns.org/
- [ ] Verifier que le sous-domaine `transportquote` pointe vers `135.125.103.119`
- [ ] Verifier la propagation DNS :
  ```bash
  dig transportquote.duckdns.org +short
  # Doit retourner : 135.125.103.119
  ```
- [ ] (Optionnel) Si l'IP est dynamique, installer le script de mise a jour DuckDNS sur le serveur :
  ```bash
  # Creer le script de mise a jour
  mkdir -p ~/duckdns
  cat > ~/duckdns/duck.sh << 'EOF'
  #!/bin/bash
  echo url="https://www.duckdns.org/update?domains=transportquote&token=VOTRE_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
  EOF
  chmod +x ~/duckdns/duck.sh

  # Ajouter au crontab (toutes les 5 minutes)
  (crontab -l 2>/dev/null; echo "*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1") | crontab -
  ```
  Remplacer `VOTRE_TOKEN` par le token DuckDNS (visible sur le dashboard).

---

## Etape 2 : Installer Certbot sur le serveur

```bash
# Connexion au serveur
ssh ubuntu@135.125.103.119

# Installation de Certbot + plugin Nginx
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

---

## Etape 3 : Preparer Nginx pour la validation

Avant de lancer Certbot, mettre a jour le `server_name` dans le reverse proxy.

- [ ] Editer la config Nginx sur le serveur :
  ```bash
  sudo nano /etc/nginx/sites-available/default
  # ou le fichier utilise (ex: /etc/nginx/conf.d/reverse-proxy.conf)
  ```

- [ ] Remplacer l'IP par le domaine :
  ```nginx
  server {
      listen 80;
      server_name transportquote.duckdns.org;  # <-- remplacer 135.125.103.119
      # ... reste de la config inchange
  }
  ```

- [ ] Tester et recharger Nginx :
  ```bash
  sudo nginx -t
  sudo systemctl reload nginx
  ```

- [ ] Ouvrir le port 443 si ce n'est pas fait :
  ```bash
  sudo ufw allow 443/tcp
  ```

- [ ] Verifier que le site repond en HTTP sur le domaine :
  ```bash
  curl -I http://transportquote.duckdns.org/transport/
  # Doit retourner HTTP/1.1 200 OK
  ```

---

## Etape 4 : Generer le certificat SSL

```bash
sudo certbot --nginx -d transportquote.duckdns.org
```

Certbot va :
1. Verifier que le domaine pointe bien vers ce serveur
2. Generer le certificat SSL
3. Modifier automatiquement la config Nginx pour ajouter le bloc HTTPS
4. Configurer la redirection HTTP -> HTTPS

- [ ] Repondre aux questions Certbot (email, CGU)
- [ ] Choisir **"Redirect"** quand demande (redirection automatique HTTP -> HTTPS)

---

## Etape 5 : Verifier la config Nginx generee

Apres Certbot, la config devrait ressembler a ceci :

```nginx
# Bloc HTTPS (ajoute par Certbot)
server {
    listen 443 ssl;
    server_name transportquote.duckdns.org;

    ssl_certificate /etc/letsencrypt/live/transportquote.duckdns.org/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/transportquote.duckdns.org/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Content-Security-Policy "default-src 'self' https: data: blob: 'unsafe-inline'" always;
    server_tokens off;

    # Transport Quote - Frontend
    location /transport {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }

    # Autres apps (KPI, etc.)
    location /api/ {
        proxy_pass http://127.0.0.1:8082/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirection HTTP -> HTTPS (ajoute par Certbot)
server {
    listen 80;
    server_name transportquote.duckdns.org;
    return 301 https://$host$request_uri;
}
```

- [ ] Verifier que le header `Strict-Transport-Security` est bien present (HSTS)
- [ ] Tester la config :
  ```bash
  sudo nginx -t
  sudo systemctl reload nginx
  ```

---

## Etape 6 : Configurer le renouvellement automatique

Les certificats Let's Encrypt expirent apres 90 jours. Certbot installe un timer systemd automatiquement.

- [ ] Verifier que le timer est actif :
  ```bash
  sudo systemctl status certbot.timer
  # Doit afficher : active (waiting)
  ```

- [ ] Tester le renouvellement a sec :
  ```bash
  sudo certbot renew --dry-run
  ```

- [ ] (Optionnel) Ajouter un reload Nginx apres renouvellement :
  ```bash
  sudo nano /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
  ```
  Contenu :
  ```bash
  #!/bin/bash
  systemctl reload nginx
  ```
  ```bash
  sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
  ```

---

## Etape 7 : Mettre a jour le CORS backend

- [ ] Dans le fichier `.env` du backend (sur le serveur) :
  ```env
  ALLOWED_ORIGINS=https://transportquote.duckdns.org
  ```

- [ ] Verifier que `backend/app/main.py` utilise bien cette variable (deja corrige) :
  ```python
  origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
  ```

- [ ] Redemarrer le backend :
  ```bash
  cd /home/ubuntu/opt/transport_quote
  ./restart.sh backend
  ```

---

## Etape 8 : Mettre a jour le frontend

- [ ] Verifier que `VITE_API_URL` pointe sur HTTPS dans le build Docker :
  ```
  VITE_API_URL=https://transportquote.duckdns.org/transport/api/v1
  ```

- [ ] Rebuild le frontend :
  ```bash
  cd /home/ubuntu/opt/transport_quote
  ./restart.sh frontend
  ```

---

## Etape 9 : Mettre a jour le repo git

- [ ] Mettre a jour `nginx-reverse-proxy.conf` dans le repo :
  ```nginx
  server_name transportquote.duckdns.org;  # Remplacer l'IP
  ```

---

## Etape 10 : Validation finale

### Tests manuels

- [ ] Acces HTTPS fonctionne :
  ```bash
  curl -I https://transportquote.duckdns.org/transport/
  # HTTP/2 200
  ```

- [ ] Redirection HTTP -> HTTPS fonctionne :
  ```bash
  curl -I http://transportquote.duckdns.org/transport/
  # HTTP/1.1 301 Moved Permanently
  # Location: https://transportquote.duckdns.org/transport/
  ```

- [ ] API backend accessible :
  ```bash
  curl https://transportquote.duckdns.org/transport/api/v1/health
  ```

- [ ] Certificat valide dans le navigateur (cadenas vert)

### Test SSL Labs

- [ ] Lancer un scan sur https://www.ssllabs.com/ssltest/
  ```
  URL a tester : transportquote.duckdns.org
  Objectif : Note A ou A+
  ```

### Test headers de securite

- [ ] Lancer un scan sur https://securityheaders.com/
  ```
  URL a tester : https://transportquote.duckdns.org/transport/
  Objectif : Note A minimum
  ```

---

## Recapitulatif des fichiers modifies

| Fichier | Emplacement | Modification |
|---------|-------------|-------------|
| Nginx reverse proxy | `/etc/nginx/...` (serveur) | `server_name transportquote.duckdns.org` + SSL + HSTS + redirection |
| `.env` backend | Serveur | `ALLOWED_ORIGINS=https://transportquote.duckdns.org` |
| `nginx-reverse-proxy.conf` | Repo git | Remplacer IP par domaine |
| Build frontend | Docker | `VITE_API_URL=https://transportquote.duckdns.org/transport/api/v1` |

---

## En cas de probleme

| Symptome | Cause probable | Solution |
|----------|---------------|----------|
| `ERR_CONNECTION_REFUSED` sur 443 | Pare-feu bloque le port | `sudo ufw allow 443/tcp` |
| Certbot echoue validation | DNS pas propage ou DuckDNS pas a jour | Verifier `dig transportquote.duckdns.org +short` retourne la bonne IP |
| Mixed content warnings | Frontend charge des ressources HTTP | Verifier `VITE_API_URL` est en HTTPS |
| Certificat expire | Timer certbot inactif | `sudo certbot renew && sudo systemctl reload nginx` |
| CORS bloque les requetes | `ALLOWED_ORIGINS` pas mis a jour | Mettre `https://transportquote.duckdns.org` dans `.env` |
| DuckDNS IP desynchronisee | IP serveur a change | Mettre a jour sur duckdns.org ou verifier le cron duck.sh |
