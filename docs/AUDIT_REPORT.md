# Audit Qualite & Securite - Transport Quote

**Date :** 2026-02-07
**Derniere verification :** 2026-02-08
**Auditeur :** Lead Tech (Claude)
**Scope :** Backend (Python/FastAPI), Frontend (React/TypeScript), Infrastructure (Docker/Nginx)

---

## Resume Executif

L'application Transport Quote est un MVP fonctionnel pour la gestion de tarifs de transport et la generation de devis. L'audit initial a revele **96 problemes**. Apres un premier passage de corrections, **6 items ont ete resolus et 2 partiellement corriges**. Il reste **41 items non corriges**.

### Progression globale

| Categorie | Corrige | Partiel | Non corrige | Total |
|-----------|---------|---------|-------------|-------|
| Backend | 3 | 2 | 17 | 22 |
| Frontend | 1 | 0 | 13 | 14 |
| Infrastructure | 2 | 0 | 11 | 13 |
| **TOTAL** | **6** | **2** | **41** | **49** |

---

# PARTIE 1 : BACKEND (Python / FastAPI)

## 1.1 Securite

### CRITICAL-B1 : Credentials en dur dans le code source
**Fichier :** `backend/app/core/config.py` (ligne 13)
```python
database_url: str = "postgresql://user:password@localhost:5432/transport_quote"
```
Aussi dans `.env`, `.env.example` et `alembic.ini`.

**Impact :** Acces direct a la base de donnees si le repo est expose.
**Remediation :** Utiliser exclusivement des variables d'environnement, supprimer les valeurs par defaut.
**Status :** :warning: PARTIEL - `config.py` corrige (`Field(..., env="DATABASE_URL")` sans valeur par defaut), `docker-compose.yml` corrige (`${POSTGRES_USER}`). Mais `alembic.ini:6` contient encore `postgresql://user:password@...` et `.env:1` aussi.

---

### CRITICAL-B2 : CORS ouvert a toutes les origines
**Fichier :** `backend/app/main.py` (lignes 17-23)
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**Impact :** CSRF et vol de credentials possibles depuis n'importe quel domaine.
**Remediation :** Whitelister les origines autorisees par environnement.
**Status :** :white_check_mark: CORRIGE - `main.py:17` lit `settings.allowed_origins.split(",")` dynamiquement depuis la variable d'environnement `ALLOWED_ORIGINS`.

---

### HIGH-B3 : Upload de fichiers sans validation
**Fichier :** `backend/app/api/imports.py` (lignes 11-31), `backend/app/services/import_service.py` (lignes 44-68)

- Pas de validation du type MIME
- Pas de verification de l'extension (whitelist)
- Pas de limite de taille cote API
- Extension extraite directement du nom de fichier utilisateur

**Remediation :** Whitelister les extensions (.xlsx, .csv), valider le MIME, enforcer une taille max.
**Status :** :white_check_mark: CORRIGE - `imports.py:26-53` valide extension (xlsx, xls, csv), MIME type, et taille (50MB max via seek/tell).

---

### HIGH-B4 : setattr dynamique sur les modeles DB
**Fichier :** `backend/app/services/customer_quote_service.py` (ligne 225)
```python
for key, value in update_dict.items():
    setattr(quote, key, value)
```
Meme pattern dans `partner_service.py` (ligne 39).

**Impact :** Si la validation Pydantic est contournee, permet de modifier n'importe quel champ (is_active, created_at...).
**Remediation :** Utiliser un mapping explicite des champs autorisees.
**Status :** :x: NON CORRIGE - `customer_quote_service.py:225` et `partner_service.py:39` utilisent toujours `setattr()`.

---

### HIGH-B5 : Aucune authentification/autorisation
**Fichier :** Tous les endpoints dans `backend/app/api/`

- Aucun middleware d'authentification
- Pas de RBAC
- Pas de rate limiting
- `DELETE /partners/{id}/quotes` supprime tout sans confirmation

**Remediation :** Ajouter JWT ou OAuth2, implementer le RBAC.
**Status :** :x: NON CORRIGE - Aucun middleware d'auth. Tous les endpoints restent publics.

---

### HIGH-B6 : Risque de Path Traversal
**Fichier :** `backend/app/services/import_service.py` (lignes 50-52)
```python
file_ext = os.path.splitext(file.filename)[1]
safe_filename = f"{partner_id}_{timestamp}{file_ext}"
```
**Remediation :** Whitelister les extensions, ne jamais utiliser le nom original.
**Status :** :warning: PARTIEL - `imports.py` valide l'extension en amont, mais `import_service.py:50` extrait toujours l'extension depuis `file.filename` avec `os.path.splitext` sans re-verification.

---

### HIGH-B7 : Validation insuffisante dans le matching
**Fichier :** `backend/app/services/matching_service.py` (lignes 19-20)

`ilike` sans validation que les codes pays sont au format ISO 2 caracteres.

**Remediation :** Valider dans le schema Pydantic (longueur exacte = 2).
**Status :** :x: NON CORRIGE - `matching.py` schema n'a pas de contrainte `min_length=2, max_length=2` sur `origin_country`/`dest_country`.

---

### MEDIUM-B8 : Bare except partout
**Fichiers :**
- `column_mapper.py` lignes 649-650 : `except: pass`
- `column_mapper.py` ligne 686 : `except: return 0.0, 0.0`
- `csv_parser.py` lignes 9-13 : `except Exception:` (trop large)
- `data_normalizer.py` ligne 66 : `except ValueError: return None`

**Impact :** Erreurs silencieuses, debug tres difficile.
**Remediation :** Utiliser des exceptions specifiques et logger.
**Status :** :x: NON CORRIGE - `column_mapper.py:649,686` contiennent toujours `except:` nu.

---

### MEDIUM-B9 : Duplication de code dans column_mapper.py
**Fichier :** `backend/app/services/import_logic/column_mapper.py`

`map_row()` et `map_row_with_sheet_config()` contiennent ~100+ lignes de logique quasi-identique (dual_grid, single_grid, zone_matrix, flat).

**Remediation :** Extraire la logique commune dans des methodes helper.
**Status :** :x: NON CORRIGE

---

### MEDIUM-B10 : God function
**Fichier :** `backend/app/services/import_logic/column_mapper.py`

- `map_row()` : 280+ lignes gerant 4 types de layout
- Parsing + mapping + transformation + validation dans une seule classe

**Remediation :** Decouper en classes par layout (GridMapper, DualGridMapper, ZoneMatrixMapper...).
**Status :** :x: NON CORRIGE

---

### MEDIUM-B11 : Couplage fort ImportService <-> FileSystem
**Fichier :** `backend/app/services/import_service.py`

Acces direct au filesystem (`os.path.join`, `open()`...) dans la couche service.

**Remediation :** Creer une abstraction FileStorage (facilite les tests et le passage au cloud).
**Status :** :x: NON CORRIGE

---

### MEDIUM-B12 : Pas de logging (uniquement print)
**Fichiers :** Tous les services

Aucun `import logging`, uniquement des `print()`. Pas de log de requete, pas d'audit trail.

**Remediation :** Implementer le module `logging` avec niveaux (DEBUG, INFO, WARNING, ERROR).
**Status :** :x: NON CORRIGE - Aucun fichier backend n'utilise `import logging`.

---

### MEDIUM-B13 : Types manquants / Optional non declare
**Fichier :** `backend/app/services/matching_service.py` (ligne 112)
```python
def _is_location_match(search_cp: str, ...) -> bool:
# search_cp peut etre None, devrait etre Optional[str]
```

**Remediation :** Ajouter `Optional[str]` pour les parametres nullable.
**Status :** :x: NON CORRIGE

---

### MEDIUM-B14 : Pas de validation min < max sur les schemas
**Fichier :** `backend/app/schemas/partner_quote.py` (lignes 17-20)
```python
weight_min: Optional[float] = None
weight_max: Optional[float] = None
```
Aucune validation que `weight_min < weight_max` ni que les valeurs soient positives.
**Status :** :x: NON CORRIGE

---

### MEDIUM-B15 : Gestion d'erreur inconsistante dans import_service
**Fichier :** `backend/app/services/import_service.py` (lignes 279-281)

Format d'erreur dict vs list selon les branches. Pas de format unifie.
**Status :** :x: NON CORRIGE - `import_service.py:281` utilise toujours `{"error": str(e)}` (dict) vs list ailleurs.

---

### MEDIUM-B16 : N+1 queries dans customer_quote_service
**Fichier :** `backend/app/services/customer_quote_service.py` (lignes 60-70)

3 queries separees pour charger quote + partner_quote + partner.

**Remediation :** Utiliser `joinedload` ou `selectinload`.
**Status :** :x: NON CORRIGE - Aucun `joinedload`/`selectinload` dans le code.

---

### MEDIUM-B17 : Index manquants
**Fichier :** `backend/app/models/partner_quote.py`

Pas d'index sur `origin_city`, `dest_city`, `valid_until` malgre leur utilisation frequente dans les filtres.
**Status :** :warning: PARTIEL - Index existants sur `origin_country+dest_country`, `transport_mode`, `is_active+valid_until`. Mais pas d'index dedies sur `origin_city`, `dest_city`.

---

### MEDIUM-B18 : TODO laisses dans le code
**Fichier :** `backend/app/services/customer_quote_service.py` (lignes 73-78)
```python
# TODO: Logique complexe de grille tarifaire si necessaire...
```
Aussi dans `quote_generator.py`.
**Status :** :x: NON CORRIGE - 5 TODO encore presents (column_mapper, quote_generator, customer_quote_service, generated_quotes, customers).

---

### LOW-B19 : Pas de tests unitaires
Aucun repertoire `tests/` trouve. Pas de fixtures, pas d'integration tests.
**Status :** :x: NON CORRIGE - Aucun fichier de test trouve.

---

### LOW-B20 : Commentaires en francais et anglais melanges
Certains docstrings en francais, d'autres en anglais. Pas de standard.
**Status :** :x: NON CORRIGE

---

### LOW-B21 : Pas d'Alembic migrations versionnees
Les modeles SQLAlchemy existent mais pas de strategy de migration claire.
**Status :** :x: NON CORRIGE

---

### LOW-B22 : Chemin hardcode pour la config YAML
**Fichier :** `column_mapper.py` (ligne 9)
```python
CONFIG_PATH = os.path.join(os.path.dirname(...), "configs", "partner_mapping.yaml")
```
Fragile, devrait etre configurable.
**Status :** :x: NON CORRIGE

---

# PARTIE 2 : FRONTEND (React / TypeScript)

## 2.1 Securite

### CRITICAL-F1 : Messages d'erreur backend affiches sans sanitization
**Fichiers :** `frontend/src/pages/Search.tsx` (ligne 85), `frontend/src/components/SearchModal.tsx` (ligne 150)
```typescript
const msg = error.response?.data?.detail?.[0]?.msg || error.response?.data?.detail || "Erreur";
alert(msg);
```
**Impact :** Si le backend retourne du contenu malicieux, il est affiche tel quel.
**Remediation :** Utiliser des messages d'erreur predicts ou sanitizer (DOMPurify).
**Status :** :white_check_mark: CORRIGE - Les deux fichiers affichent desormais un message generique fixe (`"Une erreur est survenue lors de la recherche..."`) sans exposer le contenu brut du backend.

---

### HIGH-F2 : Aucune validation des reponses API
**Fichiers :** Tous les services (`quoteService.ts`, `customerQuoteService.ts`, `partnerService.ts`)

Les reponses API sont utilisees directement sans validation de structure.

**Remediation :** Utiliser `zod` ou `io-ts` pour valider les reponses.
**Status :** :x: NON CORRIGE - Pas de validation des reponses API.

---

### HIGH-F3 : Donnees sensibles dans localStorage
**Fichier :** `frontend/src/context/CustomerQuoteContext.tsx` (lignes 71-88)

IDs de devis stockes dans localStorage sans chiffrement.

**Remediation :** Utiliser sessionStorage ou gestion de session cote serveur.
**Status :** :x: NON CORRIGE - Toujours `localStorage`.

---

### MEDIUM-F4 : URL API hardcodee en fallback
**Fichier :** `frontend/src/services/api.ts` (ligne 4)
```typescript
baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3000/api/v1'
```
**Remediation :** Lever une erreur si `VITE_API_URL` n'est pas defini en production.
**Status :** :x: NON CORRIGE - Fallback `localhost:3000` toujours present.

---

### MEDIUM-F5 : Pas de protection CSRF
Aucun token CSRF envoye avec les requetes POST/PUT/DELETE.
**Status :** :x: NON CORRIGE

---

## 2.2 Qualite du Code

### HIGH-F6 : Type `any` dans les services
**Fichier :** `frontend/src/services/quoteService.ts` (ligne 24)
```typescript
search: async (criteria: any) => {
```
**Remediation :** Typer correctement avec `SearchCriteria`.
**Status :** :x: NON CORRIGE - `criteria: any` toujours present.

---

### HIGH-F7 : Pas d'Error Boundary
**Fichier :** `frontend/src/App.tsx`

Aucun Error Boundary React. Un crash de composant fait crasher toute l'app.

**Remediation :** Ajouter un composant Error Boundary global.
**Status :** :x: NON CORRIGE - `App.tsx` n'a pas d'Error Boundary.

---

### HIGH-F8 : Duplication du formulaire de recherche
**Fichiers :** `frontend/src/pages/Search.tsx` et `frontend/src/components/SearchModal.tsx`

Le formulaire de recherche est quasi-identique dans les deux fichiers (100+ lignes dupliquees).

**Remediation :** Extraire dans un composant reutilisable `SearchForm`.
**Status :** :x: NON CORRIGE

---

### MEDIUM-F9 : Gestion d'erreur inconsistante
Certaines erreurs: `console.error()` silencieux. D'autres: `alert()`. Pas de pattern unifie.

**Remediation :** Implementer un systeme de toast notifications.
**Status :** :x: NON CORRIGE

---

### MEDIUM-F10 : `window.confirm()` pour actions destructives
**Fichier :** `frontend/src/pages/Partners.tsx` (ligne 39)

UX pauvre et pas assez securise pour les suppressions.

**Remediation :** Utiliser un modal de confirmation custom.
**Status :** :x: NON CORRIGE

---

### MEDIUM-F11 : Pas de loading states sur les operations async
**Fichier :** `frontend/src/components/customer-quote/editor/QuoteItemEditor.tsx`

`handleMarginChange` envoie la requete API sans indicateur de chargement.
**Status :** :x: NON CORRIGE

---

### MEDIUM-F12 : Pas d'i18n
Toutes les chaines sont hardcodees en francais.

**Remediation :** Implementer `react-intl` ou `i18next`.
**Status :** :x: NON CORRIGE

---

### MEDIUM-F13 : Context surcharge
**Fichier :** `frontend/src/context/CustomerQuoteContext.tsx`

Un seul context gere : CRUD devis, gestion items, UI (sidebar, modal), recherche, calculs.

**Remediation :** Decouper en `QuoteContext`, `UIContext`, `SearchContext`.
**Status :** :x: NON CORRIGE

---

## 2.3 Performance

### HIGH-F14 : Composants non memoises
**Fichier :** `frontend/src/pages/Results.tsx`

La liste de resultats (map) n'est pas memoizee. Chaque re-render recree tous les cards.

**Remediation :** Utiliser `React.memo` sur le composant card.
**Status :** :x: NON CORRIGE

---

### MEDIUM-F15 : Pas de pagination sur la page Quotes
**Fichier :** `frontend/src/pages/Quotes.tsx` (ligne 150)
```typescript
{filteredQuotes.slice(0, 100).map((quote) => {
```
Charge tout depuis l'API mais n'affiche que 100 lignes sans UI de pagination.
**Status :** :x: NON CORRIGE

---

### MEDIUM-F16 : Pas de debounce sur QuoteItemEditor
Chaque frappe sur le champ marge declenche un appel API.
**Status :** :x: NON CORRIGE

---

## 2.4 Accessibilite

### MEDIUM-F17 : Attributs ARIA manquants
- Pas de `aria-label` sur les boutons avec icones
- Pas de `aria-live` pour les zones de chargement
- Pas de focus trap dans les modals
**Status :** :x: NON CORRIGE

---

### MEDIUM-F18 : Modes transport desactives sans explication
**Fichier :** `frontend/src/components/SearchModal.tsx` (lignes 186-191)

RAIL, AIR, SEA sont desactives sans tooltip/message explicatif.
**Status :** :x: NON CORRIGE

---

### LOW-F19 : Styles de boutons inconsistants
Pas de composant Button reutilisable. Classes Tailwind dupliquees partout.
**Status :** :x: NON CORRIGE

---

### LOW-F20 : Null checks manquants dans le rendu
**Fichier :** `frontend/src/pages/CustomerQuoteDetail.tsx` (lignes 109-115)

Valeurs potentiellement null rendues sans fallback ("undefined" affiche).
**Status :** :x: NON CORRIGE

---

# PARTIE 3 : INFRASTRUCTURE (Docker / Nginx / Deploiement)

## 3.1 Securite

### CRITICAL-I1 : Credentials hardcodes dans docker-compose.yml
**Fichier :** `docker-compose.yml` (lignes 8-10)
```yaml
POSTGRES_USER: user
POSTGRES_PASSWORD: password
POSTGRES_DB: transport_quote
```
Aussi ligne 34 (DATABASE_URL du backend) et `alembic.ini` ligne 6.

**Remediation :** Utiliser Docker secrets ou `.env` non versionne.
**Status :** :warning: PARTIEL - `docker-compose.yml` corrige (utilise `${POSTGRES_USER}`, `${POSTGRES_PASSWORD}`, `${DATABASE_URL}`). Mais `alembic.ini:6` contient encore `postgresql://user:password@localhost:5432/transport_quote` en dur. `.env:1` aussi.

---

### CRITICAL-I2 : Pas de HTTPS/TLS
**Fichiers :** `frontend/nginx.conf`, `nginx.staging.conf`, `nginx-reverse-proxy.conf`

Tout le trafic sur port 80 en HTTP.

**Impact :** Donnees transmises en clair, vulnerable au MITM.
**Remediation :** Configurer Let's Encrypt + redirection HTTPS. Voir `docs/CHECKLIST_HTTPS.md`.
**Status :** :x: NON CORRIGE - Nginx ecoute toujours uniquement sur port 80.

---

### HIGH-I3 : IP serveur exposee dans le code
**Fichier :** `nginx-reverse-proxy.conf` (ligne 3)
```nginx
server_name 135.125.103.119;
```
**Remediation :** Utiliser un nom de domaine.
**Status :** :x: NON CORRIGE

---

### HIGH-I4 : Pas de headers de securite Nginx
**Fichiers :** Tous les fichiers nginx

Manquant : `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Content-Security-Policy`, `X-XSS-Protection`, `Referrer-Policy`.
**Status :** :white_check_mark: CORRIGE - `nginx-reverse-proxy.conf:6-11` contient X-Frame-Options, X-XSS-Protection, X-Content-Type-Options, Referrer-Policy, CSP + `server_tokens off`.

---

### HIGH-I5 : Upload de fichiers non valide (cote Nginx)
50M autorise par Nginx sans validation applicative.
**Status :** :white_check_mark: CORRIGE (via backend) - La validation est maintenant faite cote API (`imports.py:26-53`). Nginx reste a 50M comme limite haute.

---

### MEDIUM-I6 : Pas d'authentification sur les endpoints API
Les endpoints d'upload et de suppression sont accessibles sans authentification.
**Status :** :x: NON CORRIGE

---

## 3.2 Infrastructure

### HIGH-I7 : Pas de health checks Docker
**Fichier :** `docker-compose.yml`

Aucun `healthcheck` sur les 4 services (PostgreSQL, Redis, Backend, Frontend).

**Remediation :** Ajouter des health checks a chaque service.
**Status :** :x: NON CORRIGE

---

### HIGH-I8 : Pas de limites de ressources sur les containers
**Fichier :** `docker-compose.yml`

Pas de `mem_limit`, `cpus` sur aucun service.

**Impact :** Risque d'epuisement des ressources, DoS.
**Remediation :** Ajouter des limites memoire/CPU.
**Status :** :x: NON CORRIGE

---

### MEDIUM-I9 : Ports de bases de donnees exposes sur l'hote
**Fichier :** `docker-compose.yml` (lignes 11-12, 22-23)
```yaml
ports:
  - "5432:5432"  # PostgreSQL
  - "6379:6379"  # Redis
```
**Remediation :** Retirer le mapping de ports, acceder via le reseau Docker interne uniquement.
**Status :** :x: NON CORRIGE

---

### MEDIUM-I10 : Port backend expose directement
**Fichier :** `docker-compose.yml` (lignes 31-32)
```yaml
ports:
  - "3000:3000"
```
Accessible directement en bypassant le reverse proxy Nginx.
**Status :** :x: NON CORRIGE

---

### MEDIUM-I11 : Pas de logs centralises
Aucune configuration de logging Docker driver. Pas de ELK/CloudWatch.
**Status :** :x: NON CORRIGE

---

### MEDIUM-I12 : Pas de monitoring/metriques
Pas de Prometheus, Sentry, DataDog. Aucun endpoint de metriques.
**Status :** :x: NON CORRIGE

---

### MEDIUM-I13 : Pas de backup base de donnees
Aucun script de backup/restore trouve.
**Status :** :x: NON CORRIGE

---

### MEDIUM-I14 : Pas de gestion d'erreur dans les migrations
**Fichier :** `backend/entrypoint.sh` (lignes 6-7)
```bash
alembic upgrade head
```
Si la migration echoue, le container demarre quand meme.
**Status :** :x: NON CORRIGE

---

## 3.3 Deploiement

### HIGH-I15 : Dependances non pinees (frontend)
**Fichier :** `frontend/package.json`

Utilise `^` (caret) partout, permettant des mises a jour mineures imprevisibles.
**Status :** :x: NON CORRIGE

---

### HIGH-I16 : Dependances Python obsoletes (2+ ans)
**Fichier :** `backend/requirements.txt`

- `fastapi==0.109.2` (fev 2024)
- `sqlalchemy==2.0.25` (fev 2024)
- `pandas==2.2.0` (fev 2024)

Audit CVE necessaire.
**Status :** :x: NON CORRIGE

---

### MEDIUM-I17 : Images Docker non pinees
**Fichier :** `backend/Dockerfile` : `FROM python:3.12-slim` (sans version patch)
**Fichier :** `frontend/Dockerfile` : `FROM node:20-alpine`, `FROM nginx:alpine`

Builds non reproductibles.
**Status :** :x: NON CORRIGE

---

### MEDIUM-I18 : Pool SQLAlchemy potentiellement insuffisant
**Fichier :** `backend/app/core/database.py` (lignes 7-12)

`pool_size=10`, pas de `pool_recycle` configure.
**Status :** :x: NON CORRIGE

---

### LOW-I19 : Chemin production hardcode dans restart.sh
**Fichier :** `restart.sh` (ligne 8)
```bash
PROJECT_DIR="/home/ubuntu/opt/transport_quote"
```
**Status :** :x: NON CORRIGE

---

### LOW-I20 : Scripts debug encore dans le repo
Les fichiers `debug_*.py` sont dans le `.gitignore` mais certains sont encore trackes par git.
**Status :** :x: NON CORRIGE

---

### LOW-I21 : Code commente dans le Dockerfile
**Fichier :** `backend/Dockerfile` (lignes 5-10) - Commentaire duplique et code mort.
**Status :** :x: NON CORRIGE

---

# PLAN DE REMEDIATION PRIORITAIRE

## Sprint 1 - Immediat (Critique)

| # | Action | Fichiers concernes | Effort | Status |
|---|--------|-------------------|--------|--------|
| 1 | Supprimer credentials hardcodes, utiliser Docker secrets | docker-compose.yml, .env, config.py, alembic.ini | 2h | :warning: PARTIEL - `config.py` et `docker-compose.yml` OK, mais `alembic.ini` et `.env` restent |
| 2 | Configurer HTTPS/TLS avec Let's Encrypt | nginx configs, docker-compose | 4h | :x: A FAIRE (voir `docs/CHECKLIST_HTTPS.md`) |
| 3 | Restreindre CORS par environnement | main.py, config.py | 1h | :white_check_mark: FAIT |
| 4 | Ajouter validation upload (MIME, extension, taille) | imports.py, import_service.py | 2h | :white_check_mark: FAIT |
| 5 | Sanitizer les messages d'erreur frontend | Search.tsx, SearchModal.tsx | 1h | :white_check_mark: FAIT |

## Sprint 2 - Court terme (1-2 semaines)

| # | Action | Effort | Status |
|---|--------|--------|--------|
| 6 | Ajouter authentification JWT | 2-3j | :x: A FAIRE |
| 7 | Ajouter headers de securite Nginx | 2h | :white_check_mark: FAIT |
| 8 | Ajouter health checks Docker | 2h | :x: A FAIRE |
| 9 | Ajouter limites ressources Docker | 1h | :x: A FAIRE |
| 10 | Implementer Error Boundary React | 2h | :x: A FAIRE |
| 11 | Extraire composant SearchForm reutilisable | 4h | :x: A FAIRE |
| 12 | Remplacer alert() par toast notifications | 4h | :x: A FAIRE |

## Sprint 3 - Moyen terme (2-4 semaines)

| # | Action | Effort | Status |
|---|--------|--------|--------|
| 13 | Ecrire tests unitaires backend | 3-5j | :x: A FAIRE |
| 14 | Refactorer column_mapper.py (duplication) | 2j | :x: A FAIRE |
| 15 | Fixer N+1 queries | 1j | :x: A FAIRE |
| 16 | Implementer logging proper | 1j | :x: A FAIRE |
| 17 | Ajouter pagination server-side | 1j | :x: A FAIRE |
| 18 | Mettre a jour les dependances + audit CVE | 1j | :x: A FAIRE |
| 19 | Configurer monitoring (Sentry/Prometheus) | 1j | :x: A FAIRE |
| 20 | Backup automatique PostgreSQL | 4h | :x: A FAIRE |

---

# PARTIE 4 : CHECKLIST MISE EN PRODUCTION

Etat actuel de preparation : **~25%** - Application NON prete pour la production.

## 4.1 Pre-requis BLOQUANTS (Go/No-Go)

Ces elements doivent etre resolus **avant** toute mise en production.

| # | Element | Statut | Detail |
|---|---------|--------|--------|
| 1 | **HTTPS/TLS** | :x: Non fait | Aucune config SSL. Tout le trafic est en HTTP clair (port 80). Voir `docs/CHECKLIST_HTTPS.md`. |
| 2 | **Authentification** | :x: Non fait | Aucun mecanisme d'auth (JWT, OAuth, API key). Tous les endpoints sont publics. |
| 3 | **Gestion des secrets** | :warning: Partiel | `config.py` et `docker-compose.yml` corriges. Mais `alembic.ini` et `.env` contiennent encore `user:password`. |
| 4 | **CORS restreint** | :white_check_mark: Fait | CORS dynamique depuis `ALLOWED_ORIGINS` env var. |
| 5 | **Nom de domaine** | :x: Non fait | Nginx pointe sur IP brute (`135.125.103.119`). |
| 6 | **Validation des uploads** | :white_check_mark: Fait | Extension, MIME, taille valides dans `imports.py`. |
| 7 | **Headers de securite Nginx** | :white_check_mark: Fait | X-Frame-Options, X-XSS-Protection, X-Content-Type-Options, Referrer-Policy, CSP. |
| 8 | **docker-compose.prod.yml** | :x: Non fait | Pas de configuration Docker specifique production. |
| 9 | **Backup base de donnees** | :x: Non fait | Aucun script de backup/restore PostgreSQL. |
| 10 | **Dependances a jour** | :x: Non fait | FastAPI 0.109, SQLAlchemy 2.0.25, Pandas 2.2.0 datent de fev 2024. |

## 4.2 Indispensables (Semaine 1-2 post-Go)

| # | Element | Statut | Detail |
|---|---------|--------|--------|
| 11 | **Health checks Docker** | :x: Non fait | Aucun healthcheck sur les 4 services. |
| 12 | **Limites ressources containers** | :x: Non fait | Pas de `mem_limit` / `cpus`. |
| 13 | **Ports DB non exposes** | :x: Non fait | PostgreSQL (5432) et Redis (6379) toujours exposes sur l'hote. |
| 14 | **Port backend non expose** | :x: Non fait | Port 3000 toujours accessible directement. |
| 15 | **Monitoring & alerting** | :x: Non fait | Pas de Sentry, Prometheus, ni DataDog. |
| 16 | **Logging structure** | :x: Non fait | Uniquement `print()` dans le code. |
| 17 | **Error Boundary React** | :x: Non fait | Un crash de composant fait crasher toute l'app. |
| 18 | **Gestion d'erreur globale FastAPI** | :x: Non fait | Pas de middleware global d'exception. |
| 19 | **Rate limiting** | :x: Non fait | Aucune protection contre l'abus d'API. |
| 20 | **Non-root dans Docker** | :x: Non fait | Les containers tournent en root. |

## 4.3 Importants (Semaine 3-4)

| # | Element | Statut | Detail |
|---|---------|--------|--------|
| 21 | **CI/CD Pipeline** | :x: Non fait | Aucun GitHub Actions / GitLab CI. |
| 22 | **Tests automatises** | :x: ~5% | Pas de suite de tests, pas de coverage. |
| 23 | **Pre-commit hooks** | :x: Non fait | Pas de `.pre-commit-config.yaml`. |
| 24 | **Entrypoint robuste** | :x: Non fait | `alembic upgrade head` sans gestion d'erreur. |
| 25 | **Images Docker pinees** | :x: Non fait | `python:3.12-slim`, `node:20-alpine` sans version patch. |
| 26 | **Pool connexions DB** | :x: Non fait | `pool_size=10`, pas de `pool_recycle`. |
| 27 | **Pagination server-side** | :x: Non fait | Frontend charge tout et slice en JS. |
| 28 | **Background tasks persistantes** | :x: Non fait | Utilise FastAPI `BackgroundTasks` (perdu au restart). |

## 4.4 Nice-to-have (Moyen terme)

| # | Element | Statut | Detail |
|---|---------|--------|--------|
| 29 | **Internationalisation (i18n)** | :x: Non fait | Strings hardcodees en francais. |
| 30 | **Documentation deploiement** | :warning: Partiel | `CHECKLIST_HTTPS.md` cree. Pas de runbook ops complet. |
| 31 | **Variables d'environnement documentees** | :x: Non fait | `.env.example` avec valeurs par defaut dangereuses. |
| 32 | **Compression Gzip Nginx** | :x: Non fait | Pas de compression des reponses. |
| 33 | **Cache headers Nginx** | :x: Non fait | Pas de cache sur les assets statiques. |
| 34 | **Graceful shutdown** | :x: Non fait | Pas de handler de shutdown propre cote backend. |
| 35 | **Distributed tracing** | :x: Non fait | Pas de correlation ID sur les requetes. |

## 4.5 Resume par categorie

| Categorie | Avancement | Priorite |
|-----------|-----------|----------|
| Securite (auth, secrets, CORS, headers) | 40% | BLOQUANT |
| HTTPS / TLS | 0% | BLOQUANT |
| Configuration prod (docker, env) | 15% | BLOQUANT |
| Backup & recovery | 0% | BLOQUANT |
| Monitoring & logging | 0% | Semaine 1-2 |
| CI/CD | 0% | Semaine 3-4 |
| Tests | 5% | Semaine 3-4 |
| Performance (pagination, cache) | 30% | Moyen terme |
| Documentation ops | 10% | Moyen terme |

---

*Rapport genere le 2026-02-07. Derniere verification le 2026-02-08.*
*Prochaine revue recommandee dans 2 semaines apres correction des pre-requis bloquants restants.*
