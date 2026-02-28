# Propositions : Restriction d'accès direct aux API

## État actuel

```
Internet
  └── nginx-external (ports 80/443, réseau DMZ)
        └── nginx-internal (réseau app-network interne)
              ├── backend FastAPI (port 3000) ← pas exposé à l'extérieur
              ├── frontend React  (port 80)   ← pas exposé à l'extérieur
              ├── PostgreSQL                  ← pas exposé à l'extérieur
              └── Redis                       ← pas exposé à l'extérieur
```

**Ce qui est déjà protégé :**
- Le backend n'est pas joignable directement depuis l'extérieur (`app-network: internal: true`)
- Le rate limiting est en place sur `/auth/login` et les routes API
- Le JWT protège toutes les routes authentifiées

**Ce qui reste accessible :**
- `https://transportquote.duckdns.org/transport/api/v1/...` est appelable avec curl/Postman
- La documentation Swagger (`/docs`, `/redoc`) est accessible publiquement
- Rien n'empêche un utilisateur de contourner l'interface et d'appeler l'API directement

---

## Proposition 1 — Désactiver Swagger en production

### Principe
FastAPI expose automatiquement `/docs` (Swagger UI) et `/redoc` en développement.
En production, ces pages donnent une cartographie complète de toutes les routes, schémas et paramètres.

### Ce qu'on implémente

```python
# backend/app/main.py
from app.core.config import get_settings
settings = get_settings()

app = FastAPI(
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    openapi_url="/openapi.json" if settings.environment == "development" else None,
)
```

```bash
# .env.prod
ENVIRONMENT=production

# .env.local
ENVIRONMENT=development
```

### Avantages
- Trivial à implémenter (2 lignes)
- Élimine la cartographie publique de l'API
- L'API reste fonctionnelle, seule la documentation disparaît

### Inconvénients
- Ne bloque pas les appels directs (quelqu'un qui connaît les routes peut toujours appeler)

### Complexité : Très faible

---

## Proposition 2 — Header secret nginx → backend (X-Internal-Token)

### Principe
Nginx injecte un header secret `X-Internal-Token` dans chaque requête avant de la transmettre au backend.
Le backend rejette toute requête ne possédant pas ce header avec la bonne valeur.
Ainsi, seules les requêtes passant par nginx peuvent atteindre l'API.

### Architecture

```
curl https://transportquote.duckdns.org/transport/api/v1/...
  └── nginx-external
        └── Injecte : X-Internal-Token: <secret>
              └── nginx-internal
                    └── Injecte : X-Internal-Token: <secret>
                          └── backend FastAPI
                                └── Vérifie le header → accepte ou rejette 403
```

### Ce qu'on implémente

**nginx/external.conf** — ajout dans chaque `location /transport/api/` :
```nginx
proxy_set_header X-Internal-Token "${INTERNAL_API_SECRET}";
```

**nginx/internal.conf** — ajout dans `location /transport/api/` :
```nginx
proxy_set_header X-Internal-Token "${INTERNAL_API_SECRET}";
```

**backend/app/core/deps.py** — middleware de vérification :
```python
from fastapi import Request, HTTPException
from app.core.config import get_settings

async def verify_internal_token(request: Request):
    settings = get_settings()
    if settings.environment == "production":
        token = request.headers.get("X-Internal-Token")
        if token != settings.internal_api_secret:
            raise HTTPException(status_code=403, detail="Accès direct interdit")
```

**Enregistrement dans main.py :**
```python
app.add_middleware(InternalTokenMiddleware)
# ou via Depends() sur le router global
```

### Avantages
- Garantit que toutes les requêtes passent par nginx (rate limiting, logs, headers sécurité)
- Transparent pour le frontend
- Le secret est dans les variables d'environnement, jamais exposé au client

### Inconvénients
- Si quelqu'un intercepte le secret (ex : fuite de config), la protection tombe
- Nécessite de passer le secret à nginx via les variables d'environnement Docker

### Complexité : Faible

---

## Proposition 3 — CORS strict

### Principe
Configurer FastAPI pour n'autoriser que les requêtes CORS provenant du domaine officiel.
Un appel depuis `curl`, Postman ou un autre domaine sera bloqué **par le navigateur**.

### Ce qu'on implémente

```python
# backend/app/main.py — remplacer la config CORS actuelle
from app.core.config import get_settings
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),  # ex: "https://transportquote.duckdns.org"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

```bash
# .env.prod
ALLOWED_ORIGINS=https://transportquote.duckdns.org

# .env.local
ALLOWED_ORIGINS=http://localhost:8080
```

### Avantages
- Simple à configurer
- Bloque les appels depuis d'autres sites web (protection CSRF)
- Déjà partiellement en place (`ALLOWED_ORIGINS` existe dans le `.env`)

### Inconvénients
- **Ne bloque pas curl ou Postman** — CORS est une protection navigateur uniquement
- Un attaquant qui envoie des requêtes sans navigateur contourne complètement cette mesure

### Complexité : Très faible

---

## Proposition 4 — Bloquer /api/docs dans nginx en production

### Principe
Même si FastAPI expose `/docs`, nginx peut bloquer ces routes avant qu'elles n'atteignent le backend.

### Ce qu'on implémente

**nginx/external.conf** — ajout avant les autres `location` :
```nginx
# Bloquer la documentation API en production
location ~* ^/transport/api/(docs|redoc|openapi\.json) {
    deny all;
    return 404;
}
```

### Avantages
- Bloque la documentation même si elle est activée côté FastAPI
- Double protection avec la Proposition 1

### Complexité : Très faible

---

## Proposition 5 — Authentification mutuelle par IP (liste blanche)

### Principe
Restreindre l'accès aux routes API sensibles (administration, imports, gestion utilisateurs)
à certaines IPs connues (bureau, VPN, serveur CI/CD). Les routes publiques (login) restent ouvertes.

### Ce qu'on implémente

```nginx
# nginx/external.conf
geo $allowed_ip {
    default         0;
    192.168.1.0/24  1;   # Réseau bureau
    82.45.12.0/24   1;   # VPN entreprise
}

location /transport/api/v1/users {
    if ($allowed_ip = 0) {
        return 403;
    }
    proxy_pass http://nginx-internal;
}

location /transport/api/v1/imports {
    if ($allowed_ip = 0) {
        return 403;
    }
    proxy_pass http://nginx-internal;
}
```

### Avantages
- Routes d'administration inaccessibles depuis n'importe quelle IP
- Aucune modification du backend

### Inconvénients
- IPs dynamiques (FAI résidentiels, télétravail) rendent la liste difficile à maintenir
- Nécessite un VPN ou IP fixe pour les administrateurs distants

### Complexité : Faible (si IPs fixes) / Moyenne (avec VPN)

---

## Comparatif

| Critère                              | P1 Swagger | P2 Header secret | P3 CORS | P4 Nginx /docs | P5 IP whitelist |
|--------------------------------------|:----------:|:----------------:|:-------:|:--------------:|:---------------:|
| Bloque curl / Postman                | —          | +++              | —       | —              | ++              |
| Bloque les navigateurs tiers         | —          | +++              | ++      | —              | ++              |
| Cache la structure de l'API          | +++        | —                | —       | +++            | —               |
| Complexité d'implémentation          | Très faible| Faible           | Très faible | Très faible | Faible        |
| Impact sur le frontend               | Aucun      | Aucun            | Aucun   | Aucun          | Aucun           |
| Risque de casser l'app               | Très faible| Faible           | Moyen   | Très faible    | Moyen           |

---

## Recommandation

Combiner **P1 + P2 + P3 + P4** pour une protection complète sans complexité excessive :

| Étape | Proposition | Gain |
|---|---|---|
| 1 (immédiat) | P1 + P4 | Swagger invisible en prod |
| 2 (court terme) | P3 | CORS strict — bloque les appels cross-origin depuis un navigateur |
| 3 (court terme) | P2 | Header secret — garantit le passage par nginx pour tous les appels |

P5 (IP whitelist) est optionnel et pertinent uniquement si les administrateurs ont des IPs fixes ou un VPN.
