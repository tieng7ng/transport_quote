# Audit de Production Readiness - Transport Quote

**Date** : 10 février 2026
**Verdict global** : **PAS PRETE pour la prod** en l'état, mais la base est solide. Il y a des problèmes bloquants (critiques) et des améliorations importantes à faire.

---

## Table des matières

1. [Sécurité - Points critiques](#1-sécurité---points-critiques)
2. [Infrastructure & Docker](#2-infrastructure--docker)
3. [Backend - Code & Architecture](#3-backend---code--architecture)
4. [Frontend - Code & Architecture](#4-frontend---code--architecture)
5. [Tests](#5-tests)
6. [Opérationnel](#6-opérationnel)
7. [Plan d'action recommandé](#7-plan-daction-recommandé)

---

## 1. Sécurité - Points critiques

### BLOQUANT - Redis sans mot de passe

- **Fichier** : `backend/app/core/redis.py`
- Redis est connecté sans authentification ET le port 6379 est exposé sur l'hôte dans `docker-compose.yml:23`.
- **Risque** : N'importe qui sur le réseau peut accéder à Redis (et donc manipuler la blacklist de tokens).

### BLOQUANT - PostgreSQL exposé publiquement

- **Fichier** : `docker-compose.yml:12`
- Le port `5432:5432` est mappé sur l'hôte.
- **Risque** : En production, la base de données ne doit **jamais** être accessible depuis l'extérieur.

### BLOQUANT - Aucune validation de force de mot de passe

- **Fichier** : `backend/app/schemas/auth.py:34`
- `password: str` sans aucune contrainte (min_length, regex, etc.).
- **Risque** : Un utilisateur peut s'inscrire avec le mot de passe `"a"`.

### BLOQUANT - Swagger/Redoc exposés en prod

- **Fichier** : `backend/app/main.py:12-13`
- `/docs` et `/redoc` sont accessibles publiquement.
- **Risque** : Un attaquant peut voir l'intégralité du schéma API, les endpoints et les paramètres.

### BLOQUANT - Pas de rate limiting

- Aucune protection contre le brute force sur `/auth/login`.
- Pas de `slowapi` ou équivalent dans le projet.
- **Risque** : Attaque par force brute sur les mots de passe, DDoS applicatif.

### IMPORTANT - CORS trop permissif par défaut

- **Fichier** : `backend/app/core/config.py:25`
- `allowed_origins: list[str] = Field(["*"])` — si la variable d'env n'est pas définie, TOUTES les origines sont autorisées.

### IMPORTANT - Tokens JWT stockés en localStorage (frontend)

- **Fichier** : `frontend/src/services/api.ts:12`
- **Risque** : Vulnérable aux attaques XSS. Un script injecté peut voler les tokens.

### IMPORTANT - Header HSTS manquant

- **Fichier** : `nginx-reverse-proxy.conf`
- Pas de `Strict-Transport-Security`.
- **Risque** : Le navigateur ne force pas HTTPS après la première visite (attaque downgrade possible).

### IMPORTANT - Refresh token en query parameter

- **Fichier** : `backend/app/api/auth.py:51-56`
- Le `refresh_token` est passé en query param (comportement par défaut de FastAPI pour un `str` nu).
- **Risque** : Le token apparaît dans les logs serveur, les access logs Nginx, et l'historique du navigateur.

### IMPORTANT - CSP trop permissive

- **Fichier** : `nginx-reverse-proxy.conf:26`
- `'unsafe-inline'` autorise le JavaScript inline (vecteur XSS), `http:` autorise les ressources non-HTTPS.

### IMPORTANT - Pas de validation de la SECRET_KEY

- **Fichier** : `backend/app/core/config.py`
- Aucun contrôle que la SECRET_KEY a été changée depuis la valeur par défaut du `.env.example`.

---

## 2. Infrastructure & Docker

### Ce qui est bien fait

- Dockerfile backend utilise un **utilisateur non-root** (`appuser`)
- Let's Encrypt avec renouvellement auto (certbot)
- Nginx en reverse proxy avec SSL et headers de sécurité basiques
- `restart: always` sur tous les services
- Volumes persistants pour PostgreSQL
- Dépendances Python pinnées dans `requirements.txt`

### Problèmes

| Problème | Fichier | Sévérité |
|---|---|---|
| Port PostgreSQL 5432 exposé sur l'hôte | `docker-compose.yml:12` | **CRITIQUE** |
| Port Redis 6379 exposé sur l'hôte | `docker-compose.yml:23` | **CRITIQUE** |
| Port backend 3000 exposé (bypass nginx) | `docker-compose.yml:42` | MOYEN |
| Port frontend 8081 exposé (bypass nginx) | `docker-compose.yml:87` | MOYEN |
| Pas de health check Docker | `docker-compose.yml` | MOYEN |
| Pas de limites de ressources (mem/cpu) | `docker-compose.yml` | MOYEN |
| Redis sans persistence configurée | `docker-compose.yml:19-26` | FAIBLE |
| Pas de multi-stage build (image plus lourde) | `backend/Dockerfile` | MOYEN |
| Pas de hardening SSL Nginx (protocoles, ciphers) | `nginx-reverse-proxy.conf` | MOYEN |
| Pas de stratégie de backup PostgreSQL | `docker-compose.yml` | MOYEN |

---

## 3. Backend - Code & Architecture

### Ce qui est bien fait

- Authentification JWT avec access + refresh tokens
- Blacklist de tokens via Redis (révocation au logout)
- Hashage bcrypt des mots de passe (`passlib`)
- Validation des fichiers upload (extensions autorisées)
- Séparation propre : API / Services / Models / Schemas
- Pydantic pour la validation des données entrantes
- Alembic pour les migrations de base de données
- RBAC (Role-Based Access Control) avec `require_role()`
- Vérification `must_change_password` dans `deps.py:72`
- Pool de connexions SQLAlchemy configuré (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`)
- Email unique avec index dans le modèle User
- Endpoint `/health` présent

### Problèmes

| Problème | Fichier:ligne | Sévérité |
|---|---|---|
| Domaine email par défaut = `toto.fr` (placeholder) | `config.py:24` | MOYEN |
| Refresh token réutilisé (pas de rotation) | `auth.py:82` | MOYEN |
| `datetime.utcnow()` deprecated en Python 3.12+ | `security.py:21,23,30` | FAIBLE |
| Pas de logging structuré (utilise `print()`) | tout le backend | MOYEN |
| `except Exception` trop large dans le refresh | `auth.py:84-88` | MOYEN |
| `UPLOAD_DIR` hardcodé dans import_service | `import_service.py:22` | FAIBLE |
| Health check ne vérifie pas DB/Redis | `main.py:41-44` | MOYEN |
| Pas de handler d'exception global | `main.py` | MOYEN |
| Pas de timeout sur les connexions DB | `database.py` | MOYEN |
| Pas de max_length sur les champs string des schemas | `schemas/` | MOYEN |
| RBAC manquant sur lecture de quote individuelle | `customer_quotes.py:46-60` | MOYEN |
| `python-jose` n'est plus activement maintenu | `requirements.txt:37` | MOYEN |
| Dépendances datées de janvier 2024 | `requirements.txt` | MOYEN |
| MIME type check trop faible sur upload | `api/imports.py:37-46` | MOYEN |
| Pas de request ID pour le tracing | tout le backend | FAIBLE |

---

## 4. Frontend - Code & Architecture

### Ce qui est bien fait

- TypeScript strict activé (`tsconfig`)
- React 19 + Vite 7 (stack moderne et à jour)
- Routes protégées avec RBAC (`ProtectedRoute`)
- Refresh token automatique sur 401 (intercepteur axios)
- ESLint configuré avec plugins React + TypeScript
- Design responsive avec Tailwind CSS
- États de chargement et boutons disabled pendant les requêtes

### Problèmes

| Problème | Fichier | Sévérité |
|---|---|---|
| Tokens en localStorage (vulnérable XSS) | `services/api.ts:12` | **IMPORTANT** |
| Pas d'Error Boundary React | `App.tsx` | **IMPORTANT** |
| URL API hardcodée en fallback | `services/api.ts:4` | MOYEN |
| ~27 `console.log`/`console.error` en prod | multiples fichiers | MOYEN |
| `any` utilisé partout pour les erreurs | Pages + AuthContext | MOYEN |
| `alert()` pour les erreurs utilisateur | `pages/Users.tsx` | MOYEN |
| Race condition sur le refresh token | `services/api.ts:24` | MOYEN |
| Pas de timeout axios configuré | `services/api.ts` | FAIBLE |
| Pas de cancel request au unmount (memory leak) | Pages | FAIBLE |
| Pas de validation des réponses API (zod/yup) | `services/` | FAIBLE |
| Accessibilité : aria-labels manquants | `pages/Users.tsx` | FAIBLE |
| `window.confirm()` pour les confirmations | `Users.tsx`, `CustomerQuotes.tsx` | FAIBLE |

---

## 5. Tests

### État actuel

- **2 tests** seulement : `backend/app/tests/api/test_auth.py`
  - `test_login_access_token` : vérifie le login basique
  - `test_use_access_token` : vérifie l'utilisation du token
- Base de test sur SQLite in-memory (OK pour les tests unitaires)
- Aucun test frontend

### Ce qui manque

- Tests RBAC (vérifier que les rôles sont respectés)
- Tests de validation des mots de passe
- Tests de sécurité (token expiré, token blacklisté, brute force)
- Tests des endpoints partners, quotes, imports, users
- Tests d'intégration avec PostgreSQL réel
- Tests de charge (k6, locust)
- Tests E2E frontend (Playwright, Cypress)
- Pas de configuration pytest (`pytest.ini` ou `pyproject.toml`)
- Pas de mesure de couverture de code

---

## 6. Opérationnel

| Élément | État | Sévérité |
|---|---|---|
| Logging structuré | Absent (utilise `print()`) | MOYEN-HAUT |
| Monitoring / Métriques (Prometheus, etc.) | Absent | MOYEN |
| Alerting sur activités suspectes | Absent | MOYEN |
| Documentation de déploiement | Absente | FAIBLE |
| Procédure de backup/restore | Absente | MOYEN |
| Runbook d'incident | Absent | FAIBLE |
| Séparation des configs dev/prod/test | Absente | MOYEN |

---

## 7. Plan d'action recommandé

### Phase 1 — Bloquants avant mise en prod

| # | Action | Fichier(s) | Effort estimé |
|---|---|---|---|
| 1 | Retirer les ports exposés (5432, 6379, 3000, 8081) dans docker-compose | `docker-compose.yml` | 5 min |
| 2 | Ajouter un mot de passe Redis (env var + config) | `core/redis.py`, `docker-compose.yml` | 30 min |
| 3 | Ajouter validation mot de passe (min 8 chars, complexité) | `schemas/auth.py` | 15 min |
| 4 | Désactiver Swagger en prod (conditionner sur `settings.debug`) | `main.py` | 5 min |
| 5 | Ajouter rate limiting sur `/auth/login` | `api/auth.py`, `requirements.txt` | 2h |
| 6 | Changer le domaine email par défaut de `toto.fr` | `config.py` | 5 min |
| 7 | Ajouter HSTS dans la config Nginx | `nginx-reverse-proxy.conf` | 5 min |
| 8 | Ajouter validation de la SECRET_KEY (pas la valeur par défaut) | `config.py` | 15 min |
| 9 | Passer le refresh_token dans le body (pas query param) | `api/auth.py` | 15 min |
| 10 | Durcir la CSP Nginx (retirer `unsafe-inline` et `http:`) | `nginx-reverse-proxy.conf` | 10 min |

### Phase 2 — Important (première semaine)

| # | Action | Effort estimé |
|---|---|---|
| 11 | Mettre à jour les dépendances (surtout `python-jose` → `PyJWT`) | 1h |
| 12 | Ajouter un Error Boundary React | 30 min |
| 13 | Supprimer les `console.log` / remplacer par un logger conditionnel | 1h |
| 14 | Ajouter des health checks Docker (`depends_on` avec condition) | 30 min |
| 15 | Ajouter du logging structuré côté backend | 3h |
| 16 | Ajouter un handler d'exception global (FastAPI) | 30 min |
| 17 | Ajouter des timeouts sur les connexions DB | 15 min |
| 18 | Hardening SSL Nginx (protocoles TLS 1.2+, ciphers) | 30 min |

### Phase 3 — Améliorations (semaines 2-4)

| # | Action | Effort estimé |
|---|---|---|
| 19 | Migrer les tokens du localStorage vers des cookies httpOnly | 4h |
| 20 | Ajouter des tests backend (couverture > 70%) | 4-8h |
| 21 | Rotation des refresh tokens | 2h |
| 22 | Monitoring / alerting (Sentry, Prometheus, Grafana) | 4h |
| 23 | Ajouter des tests E2E frontend | 4h |
| 24 | Multi-stage Docker build | 30 min |
| 25 | Limites de ressources Docker (CPU/mémoire) | 15 min |
| 26 | Documentation de déploiement et runbook | 2h |
| 27 | Stratégie de backup PostgreSQL automatisée | 2h |

---

## Résumé

L'architecture est propre et le code est de bonne qualité. Les problèmes sont principalement liés à :

1. **La configuration de sécurité** : ports exposés, pas de rate limiting, pas de validation de mots de passe, Redis sans auth
2. **Les bonnes pratiques de production** : Swagger exposé, pas de logging structuré, tests insuffisants (2 tests)
3. **Le frontend** : tokens en localStorage, pas d'Error Boundary, console.logs en prod

Les corrections de **Phase 1 sont rapides** (~3-4h de travail) et débloqueront la mise en production.
