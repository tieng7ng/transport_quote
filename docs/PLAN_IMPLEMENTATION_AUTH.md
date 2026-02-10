# Plan d'Implémentation - Module d'Authentification

> **Dernière mise à jour** : 2026-02-09
> **Basé sur** : `PROPOSITIONS_MODULE_AUTHENTIFICATION.md`
> **Statut global** : En cours (~60% complété)

---

## Bilan synthétique

| Catégorie | Fait | Reste | Bloqué |
|-----------|------|-------|--------|
| Infrastructure backend | 4/4 | 0 | 0 |
| Base de données & modèles | 2/3 | 1 | 0 |
| Sécurité & authentification | 4/6 | 2 | 0 |
| Endpoints API auth | 5/5 | 0 | 0 |
| Gestion utilisateurs (backend) | 2/4 | 2 | 0 |
| Protection des routes backend | 3/6 | 3 | 0 |
| Frontend auth | 6/6 | 0 | 0 |
| Frontend pages admin | 0/3 | 3 | 0 |
| Bugs critiques à corriger | — | 2 | 0 |
| Failles sécurité à corriger | — | 6 | 0 |

---

## 1. Infrastructure Backend

### 1.1 Dépendances Python — FAIT
- `python-jose[cryptography]==3.3.0`
- `passlib[bcrypt]==1.7.4`
- `bcrypt==4.0.1`
- `redis==5.0.1`
- `email-validator==2.1.0`

### 1.2 Configuration Redis — FAIT
- `backend/app/core/redis.py` : client singleton, `get_redis()` dependency
- Docker Compose : `redis:7-alpine` sur port 6379
- Variables d'environnement `REDIS_HOST`, `REDIS_PORT` configurées

### 1.3 Variables d'environnement — FAIT
- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `ALLOWED_EMAIL_DOMAINS` (défaut : `toto.fr`)
- `REDIS_HOST`, `REDIS_PORT`

### 1.4 Dépendances Frontend — FAIT
- `jwt-decode@^4.0.0`
- `axios@^1.13.3`

---

## 2. Base de Données & Modèles

### 2.1 Modèle User — FAIT
**Fichier** : `backend/app/models/user.py`

Colonnes : `id` (UUID), `email` (unique, indexé), `hashed_password`, `first_name`, `last_name`, `role` (String), `is_active`, `must_change_password`, `last_login_at`, `created_at`, `updated_at`

### 2.2 Migration Alembic — FAIT
**Fichier** : `backend/alembic/versions/5ec4c3702320_add_user_model_and_enhance_customerquote.py`

- Crée la table `users`
- Ajoute `created_by` et `updated_by` (FK vers `users`) sur `customer_quotes`

### 2.3 Alimentation `created_by`/`updated_by` — A FAIRE
**Fichiers concernés** : `backend/app/api/customer_quotes.py`, `backend/app/services/customer_quote_service.py`

Les colonnes existent en base mais ne sont **jamais renseignées**. Les endpoints `customer_quotes` doivent injecter l'utilisateur courant et peupler ces champs à la création et modification des devis.

**Travail à réaliser** :
- Ajouter `Depends(get_current_user)` aux endpoints de création/modification
- Passer `current_user.id` au service pour renseigner `created_by` / `updated_by`

---

## 3. Sécurité & Authentification (Backend)

### 3.1 Module de sécurité — FAIT
**Fichier** : `backend/app/core/security.py`

- `hash_password()`, `verify_password()` via bcrypt/passlib
- `create_access_token()` avec `jti` (UUID) et expiration configurable
- `create_refresh_token()` avec `type: "refresh"` et `jti`
- `decode_token()`

### 3.2 Dépendances FastAPI — FAIT
**Fichier** : `backend/app/core/deps.py`

- `get_current_user()` : JWT decode + blacklist Redis + user actif
- `get_current_active_user()` : wrapper (redondant)
- `require_role(*roles)` : factory avec bypass SUPER_ADMIN

### 3.3 Service d'authentification — FAIT
**Fichier** : `backend/app/services/auth_service.py`

- `authenticate_user()` : vérification email/password
- `create_user()` : validation domaine, doublon, création inactive par défaut
- `update_last_login()` : timestamp de dernière connexion

### 3.4 CLI création admin — FAIT
**Fichier** : `backend/app/cli/create_admin.py`

Crée un utilisateur `ADMIN` (actif, `must_change_password=False`).

### 3.5 Validation du type de token — A FAIRE
**Fichier** : `backend/app/core/deps.py` (ligne 32)

`get_current_user()` ne vérifie **pas** que le token est un access token. Un refresh token peut actuellement authentifier des requêtes API.

**Travail à réaliser** :
```python
# Après decode du token, ajouter :
if payload.get("type") == "refresh":
    raise credentials_exception
```

### 3.6 Enforcement du `must_change_password` — A FAIRE
**Fichiers concernés** : `backend/app/core/deps.py`, nouveau endpoint `POST /auth/change-password`

Le flag `must_change_password` est positionné à `True` à la création d'un utilisateur mais **jamais vérifié**. Un utilisateur peut utiliser l'application sans changer son mot de passe initial.

**Travail à réaliser** :
- Vérifier `must_change_password` dans `get_current_user()` → retourner une 403 spécifique (`"must_change_password": true`)
- Créer un endpoint `POST /auth/change-password` (old_password, new_password)
- Mettre `must_change_password = False` après un changement réussi
- Côté frontend : intercepter cette 403 et rediriger vers un formulaire de changement de mot de passe

---

## 4. Endpoints API Auth

### 4.1 Login — FAIT
`POST /api/v1/auth/login` : OAuth2 form-data, retourne access + refresh tokens

### 4.2 Refresh — FAIT
`POST /api/v1/auth/refresh` : valide le type refresh, vérifie blacklist, retourne nouveau access token

### 4.3 Logout — FAIT (avec bug critique, voir section 8.1)
`POST /api/v1/auth/logout` : blacklist le token dans Redis

### 4.4 Me — FAIT
`GET /api/v1/auth/me` : retourne l'utilisateur courant

### 4.5 Register — FAIT
`POST /api/v1/auth/register` : auto-inscription VIEWER, inactif par défaut, validation domaine

---

## 5. Gestion des Utilisateurs (Backend)

### 5.1 CRUD Admin — FAIT (partiel)
**Fichier** : `backend/app/api/users.py`

Endpoints existants :
- `GET /users/` : liste tous les utilisateurs (ADMIN)
- `GET /users/{id}` : détail d'un utilisateur (ADMIN)
- `PUT /users/{id}` : modification (nom, password, rôle, is_active) (ADMIN)

### 5.2 Endpoint DELETE — A FAIRE
**Fichier** : `backend/app/api/users.py`

Pas de `DELETE /users/{id}`. Un admin ne peut que désactiver un utilisateur via le PUT, pas le supprimer.

**Travail à réaliser** :
- Ajouter `DELETE /users/{id}` avec `require_role("ADMIN")`
- Soft delete (désactivation) ou hard delete selon le choix métier
- Empêcher la suppression de son propre compte

### 5.3 Protection contre l'escalade de privilèges — A FAIRE
**Fichier** : `backend/app/api/users.py`

Actuellement, un ADMIN peut changer le rôle de n'importe quel utilisateur, y compris se promouvoir en SUPER_ADMIN ou modifier un autre ADMIN.

**Travail à réaliser** :
- Un ADMIN ne peut pas attribuer le rôle SUPER_ADMIN
- Un ADMIN ne peut pas modifier un autre ADMIN (sauf SUPER_ADMIN qui peut tout faire)
- Un utilisateur ne peut pas modifier son propre rôle

### 5.4 Création SUPER_ADMIN — A FAIRE
**Fichier** : `backend/app/cli/create_admin.py`

Le CLI crée uniquement un `ADMIN`. Aucun mécanisme pour créer un `SUPER_ADMIN`.

**Travail à réaliser** :
- Ajouter un argument `--role` au script CLI (défaut `ADMIN`, option `SUPER_ADMIN`)
- Ou créer un script dédié `create_superadmin.py`

---

## 6. Protection des Routes Backend

### 6.1 Partners — FAIT
- Lecture : tous authentifiés
- Création/Modification : ADMIN, OPERATOR
- Suppression : ADMIN

### 6.2 Quotes (tarifs) — FAIT
- Lecture : tous authentifiés
- Création/Suppression : ADMIN, OPERATOR

### 6.3 Imports — FAIT
- Toutes actions : ADMIN, OPERATOR

### 6.4 Customer Quotes — A FAIRE
**Fichier** : `backend/app/api/customer_quotes.py`

**Les 8 endpoints sont totalement non protégés.** Aucun `Depends(get_current_user)` ni `require_role()`.

**Travail à réaliser** :
| Endpoint | Protection requise |
|----------|-------------------|
| `POST /customer-quotes/` | Tous authentifiés |
| `GET /customer-quotes/` | Tous authentifiés (COMMERCIAL : ses devis uniquement) |
| `GET /customer-quotes/{id}` | Tous authentifiés |
| `PUT /customer-quotes/{id}` | ADMIN, COMMERCIAL |
| `DELETE /customer-quotes/{id}` | ADMIN |
| `POST /customer-quotes/{id}/items` | ADMIN, COMMERCIAL |
| `PUT /customer-quotes/{id}/items/{item_id}` | ADMIN, COMMERCIAL |
| `DELETE /customer-quotes/{id}/items/{item_id}` | ADMIN |

### 6.5 Matching (recherche) — A FAIRE
**Fichier** : `backend/app/api/matching.py`

Le endpoint `POST /api/v1/match/` n'a aucune protection.

**Travail à réaliser** :
- Ajouter `Depends(get_current_user)` — accessible à tous les utilisateurs authentifiés

### 6.6 Cities (suggestions) — A FAIRE
**Fichier** : `backend/app/api/cities.py`

Le endpoint `GET /api/v1/cities/suggest` n'a aucune protection.

**Travail à réaliser** :
- Ajouter `Depends(get_current_user)` — accessible à tous les utilisateurs authentifiés

---

## 7. Frontend — Authentification

### 7.1 AuthContext — FAIT
**Fichier** : `frontend/src/context/AuthContext.tsx`

Gestion centralisée : `user`, `token`, `isAuthenticated`, `isLoading`, `error`, `hasRole()`

### 7.2 Page Login — FAIT
**Fichier** : `frontend/src/pages/Login.tsx`

Formulaire email/password, gestion erreurs, redirection

### 7.3 Page Register — FAIT
**Fichier** : `frontend/src/pages/Register.tsx`

Auto-inscription, message de validation admin requise

### 7.4 ProtectedRoute — FAIT
**Fichier** : `frontend/src/components/auth/ProtectedRoute.tsx`

Redirection vers `/login` si non authentifié, vérification des rôles

### 7.5 RoleGate — FAIT
**Fichier** : `frontend/src/components/auth/RoleGate.tsx`

Affichage conditionnel par rôle (composant disponible mais sous-utilisé)

### 7.6 Intercepteur Axios — FAIT
**Fichier** : `frontend/src/services/api.ts`

Request interceptor (ajout Bearer token), Response interceptor (refresh sur 401)

---

## 8. Bugs Critiques à Corriger

### 8.1 BUG : Endpoint `/logout` cassé — CRITIQUE
**Fichier** : `backend/app/api/auth.py` (ligne 103)

```python
# ACTUEL (cassé) :
ttl = exp - datetime.utcnow().timestamp()
# Erreur : seul `timedelta` est importé, pas `datetime`
# → NameError: name 'datetime' is not defined
```

**Correction** :
```python
# Option 1 : ajouter l'import
from datetime import datetime, timedelta

# Option 2 : utiliser time.time() (plus simple)
import time
ttl = exp - time.time()
```

### 8.2 BUG : Imports dupliqués dans App.tsx — CRITIQUE
**Fichier** : `frontend/src/App.tsx` (lignes 1-13)

Les lignes 1-13 dupliquent les lignes 15-30. Les 13 premières lignes doivent être supprimées. Cela provoque une erreur de compilation TypeScript.

---

## 9. Failles de Sécurité à Corriger

### 9.1 Validation du type de token — HAUTE
**Fichier** : `backend/app/core/deps.py`
**Détail** : voir section 3.5

### 9.2 Vérification du rôle SUPER_ADMIN (substring match) — MOYENNE
**Fichier** : `backend/app/core/deps.py` (ligne 65)

```python
# ACTUEL (incorrect) :
if current_user.role not in allowed_roles and "SUPER_ADMIN" not in current_user.role:
# "SUPER_ADMIN" not in current_user.role → teste si la CHAINE "SUPER_ADMIN"
# est une sous-chaîne de current_user.role. Devrait être une comparaison stricte.

# CORRECTION :
if current_user.role not in allowed_roles and current_user.role != "SUPER_ADMIN":
```

### 9.3 Rôle en String libre en base — MOYENNE
**Fichier** : `backend/app/models/user.py`

Le rôle est un `String` sans contrainte. Toute valeur peut être stockée.

**Correction recommandée** :
```python
from sqlalchemy import Enum as SAEnum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    COMMERCIAL = "COMMERCIAL"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"

role = Column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
```

### 9.4 Pas de rotation du refresh token — MOYENNE
**Fichier** : `backend/app/api/auth.py` (ligne 82)

Le même refresh token est réutilisé. Un token volé reste valide 7 jours.

**Correction recommandée** :
- Blacklister l'ancien refresh token
- Émettre un nouveau refresh token à chaque refresh

### 9.5 `datetime.utcnow()` déprécié (Python 3.12) — BASSE
**Fichiers** : `backend/app/core/security.py` (lignes 22, 24, 31), `backend/app/services/auth_service.py` (ligne 61)

```python
# ACTUEL (déprécié) :
datetime.utcnow()

# CORRECTION :
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

### 9.6 Timing attack sur `authenticate_user` — BASSE
**Fichier** : `backend/app/services/auth_service.py` (ligne 51)

Retour immédiat si l'utilisateur n'existe pas, vs hash bcrypt si l'utilisateur existe. Permet de distinguer les emails existants.

**Correction recommandée** :
```python
if not user:
    # Toujours exécuter un hash pour éviter le timing attack
    security.hash_password("dummy_password")
    return None
```

---

## 10. Frontend — Pages et Fonctionnalités Manquantes

### 10.1 Page d'administration des utilisateurs — A FAIRE
**Fichier à créer** : `frontend/src/pages/Users.tsx`

L'API backend `GET/PUT /users/` existe mais aucune page frontend ne l'exploite. Un admin ne peut pas :
- Voir la liste des utilisateurs
- Activer/désactiver un compte
- Modifier un rôle
- Valider les inscriptions en attente

**Travail à réaliser** :
- Créer `pages/Users.tsx` : tableau avec colonnes (Nom, Email, Rôle, Statut, Actions)
- Modale de modification d'un utilisateur
- Bouton d'activation/désactivation
- Filtres par rôle et statut
- Ajouter la route `/users` dans `App.tsx` avec `ProtectedRoute allowedRoles={['ADMIN']}`
- Ajouter le lien dans la Sidebar (visible uniquement pour ADMIN)

### 10.2 Filtrage de la Sidebar par rôle — A FAIRE
**Fichier** : `frontend/src/components/layout/Sidebar.tsx`

Tous les liens de navigation sont affichés pour tous les utilisateurs, peu importe leur rôle. Le composant `RoleGate` existe mais n'est pas utilisé.

**Travail à réaliser** :
```tsx
// Wraper les liens selon les rôles :
<RoleGate allowedRoles={['ADMIN', 'OPERATOR']}>
    <SidebarLink to="/partners" icon={Users} label="Partenaires" />
    <SidebarLink to="/imports" icon={UploadCloud} label="Imports" />
</RoleGate>

<RoleGate allowedRoles={['ADMIN']}>
    <SidebarLink to="/users" icon={UserCog} label="Utilisateurs" />
</RoleGate>
```

### 10.3 Page profil utilisateur — A FAIRE
**Fichier à créer** : `frontend/src/pages/Profile.tsx`

Le `UserMenu` contient un lien vers `/profile` mais cette route n'existe pas dans `App.tsx`.

**Travail à réaliser** :
- Créer `pages/Profile.tsx` : affichage des infos personnelles, formulaire de changement de mot de passe
- Ajouter la route `/profile` dans `App.tsx`

---

## 11. Améliorations Qualité de Code

### 11.1 `oauth2_scheme` défini en double — BASSE
**Fichiers** : `backend/app/core/security.py` (ligne 12) et `backend/app/core/deps.py` (ligne 17)

Supprimer la définition dans `security.py` ou dans `deps.py`, et n'en garder qu'une seule.

### 11.2 `get_current_active_user` redondant — BASSE
**Fichier** : `backend/app/core/deps.py` (lignes 58-61)

Identique à `get_current_user` (qui vérifie déjà `is_active`). Peut être supprimé si non utilisé ailleurs.

### 11.3 Refresh token en query parameter — BASSE
**Fichier** : `backend/app/api/auth.py` (ligne 53)

Le refresh token est passé en paramètre d'URL (visible dans les logs serveur et l'historique navigateur).

**Correction recommandée** :
```python
# ACTUEL :
def refresh_token(refresh_token: str, ...):

# CORRECTION : utiliser le body
from app.schemas.auth import RefreshRequest  # déjà défini mais non utilisé

@router.post("/refresh")
def refresh_token(body: RefreshRequest, ...):
    token = body.refresh_token
```

### 11.4 Race condition sur les 401 concurrents — BASSE
**Fichier** : `frontend/src/services/api.ts`

Si plusieurs requêtes échouent avec 401 simultanément, chacune tente un refresh indépendant.

**Correction recommandée** : implémenter un mutex/queue pour le refresh :
- Stocker la promesse de refresh en cours
- Les requêtes suivantes attendent cette promesse au lieu de lancer un nouveau refresh

### 11.5 Validation domaine email insensible à la casse — BASSE
**Fichier** : `backend/app/services/auth_service.py` (ligne 20)

```python
# ACTUEL :
domain = user_in.email.split("@")[-1]

# CORRECTION :
domain = user_in.email.split("@")[-1].lower()
```

### 11.6 Gestion erreur Redis — BASSE
**Fichier** : `backend/app/core/redis.py`

Aucun health check ni gestion d'erreur de connexion. Si Redis est down, les dépendances auth lèvent une exception non gérée.

**Correction recommandée** : ajouter un try/except dans `get_current_user` pour la vérification blacklist, avec un fallback gracieux (log + continuer sans blacklist check ou erreur 503).

---

## 12. Audit Logging — A FAIRE (Phase 2)

Proposé dans les spécifications mais **non implémenté**.

**Travail à réaliser** :
- Créer une table `audit_log` (id, user_id, action, entity_type, entity_id, details JSON, created_at)
- Créer un service `AuditService.log(user, action, entity, details)`
- Logger les événements critiques : login, logout, échec de login, création/modification/suppression d'entités
- Ajouter un endpoint admin `GET /api/v1/audit-logs/` avec filtres

---

## 13. Migration Alembic downgrade — A CORRIGER

**Fichier** : `backend/alembic/versions/5ec4c3702320_*.py`

La fonction `downgrade()` utilise `op.drop_constraint(None, ...)` avec `None` comme nom de contrainte. La migration retour échouera.

**Correction** : nommer explicitement les foreign keys dans le `upgrade()` et utiliser ces noms dans le `downgrade()`.

---

## 14. Récapitulatif — Ordre de Priorité

### Priorité 1 — Bugs critiques (bloquants)
| # | Tâche | Fichier | Effort |
|---|-------|---------|--------|
| 1 | Corriger import `datetime` dans `/logout` | `backend/app/api/auth.py` | 5 min |
| 2 | Supprimer imports dupliqués dans `App.tsx` | `frontend/src/App.tsx` | 5 min |

### Priorité 2 — Failles de sécurité
| # | Tâche | Fichier | Effort |
|---|-------|---------|--------|
| 3 | Ajouter validation type token (access vs refresh) | `backend/app/core/deps.py` | 15 min |
| 4 | Protéger les endpoints `customer-quotes` | `backend/app/api/customer_quotes.py` | 30 min |
| 5 | Protéger les endpoints `match` et `cities` | `backend/app/api/matching.py`, `cities.py` | 15 min |
| 6 | Corriger substring match SUPER_ADMIN | `backend/app/core/deps.py` | 5 min |
| 7 | Enum DB pour les rôles | `backend/app/models/user.py` + migration | 30 min |
| 8 | Rotation du refresh token | `backend/app/api/auth.py` | 30 min |

### Priorité 3 — Fonctionnalités manquantes
| # | Tâche | Fichier(s) | Effort |
|---|-------|------------|--------|
| 9 | Page admin gestion utilisateurs | `frontend/src/pages/Users.tsx` + route | 3-4h |
| 10 | Filtrage Sidebar par rôle | `frontend/src/components/layout/Sidebar.tsx` | 30 min |
| 11 | Page profil + changement mot de passe | `frontend/src/pages/Profile.tsx` + endpoint | 2h |
| 12 | Alimenter `created_by`/`updated_by` | `backend/app/api/customer_quotes.py` | 1h |
| 13 | Enforcement `must_change_password` | Backend deps + frontend redirect | 2h |
| 14 | Protection escalade de privilèges | `backend/app/api/users.py` | 30 min |
| 15 | CLI création SUPER_ADMIN | `backend/app/cli/create_admin.py` | 15 min |

### Priorité 4 — Qualité et Phase 2
| # | Tâche | Effort |
|---|-------|--------|
| 16 | Remplacement `datetime.utcnow()` | 15 min |
| 17 | Suppression `oauth2_scheme` dupliqué | 5 min |
| 18 | Refresh token en body (pas query param) | 15 min |
| 19 | Mutex refresh dans Axios interceptor | 1h |
| 20 | Validation domaine email case-insensitive | 5 min |
| 21 | Gestion erreur Redis | 30 min |
| 22 | Correction downgrade Alembic | 30 min |
| 23 | Audit logging complet | 4-5h |
| 24 | Endpoint DELETE user | 30 min |

---

**Effort total estimé** : ~18-20h de développement pour compléter l'intégralité du module.
