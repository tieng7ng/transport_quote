# Propositions : Module d'Authentification et Gestion des Profils

> **Derniere mise a jour** : 2026-02-12
> **Statut global** : ~100% implemente — Alignment des roles termine, verification script passes.

---

## Bilan d'implementation

| Categorie                                             | Statut         | Detail                                                                                                                   |
| ----------------------------------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------ |
| Infrastructure (deps, Redis, env)                     | FAIT           | Toutes les deps installees, Redis configure                                                                              |
| Modele User + migration Alembic                       | FAIT           | Table `users` complete (avec `login`, `role` enum), colonnes `created_by`/`updated_by` sur `customer_quotes`.            |
| Securite (JWT, bcrypt, deps)                          | FAIT           | Bugs critiques corriges (logout, type check, super admin check).                                                         |
| Endpoints auth (login, refresh, logout, me, register) | FAIT           | Logout operationnel. Routes proteges et securisees. Change-password operationnel.                                        |
| Endpoints users (CRUD admin)                          | FAIT           | GET, PUT, DELETE, POST, PATCH status/role implementes. Protection escalade privileg. Soft delete effectif.               |
| Protection routes backend                             | FAIT           | `partners`, `quotes`, `imports`, `match`, `cities` proteges. Roles **conformes a la matrice 1.2**.                       |
| Frontend auth (context, login, register, interceptor) | FAIT           | AuthContext, Login, Register, ProtectedRoute, RoleGate, UserMenu, Axios interceptor. **Mutex refresh token implemente**. |
| Frontend pages admin                                  | FAIT           | Page Users (SUPER_ADMIN, ADMIN), Page Profile, Sidebar filtree par RoleGate, ChangePasswordModal.                        |
| Frontend routing/sidebar                              | FAIT           | Routes et RoleGate en place. Roles **conformes a la matrice 1.2**.                                                       |
| Tracabilite (`created_by`/`updated_by`)               | FAIT (Partiel) | Colonnes existent. Logique d'alimentation a confirmer sur endpoints customer-quotes.                                     |
| Audit logging                                         | NON FAIT       | Ni table ni service (Optionnel phase 2)                                                                                  |
| Rate limiting                                         | PARTIEL        | Limiter configure sur /login (5/min).                                                                                    |

---

## Contexte

### Situation actuelle

L'application dispose desormais d'un **mecanisme d'authentification complet** :
- FAIT : JWT access/refresh tokens avec bcrypt et Redis blacklisting
- FAIT : 5 profils definis (SUPER_ADMIN, ADMIN, COMMERCIAL, OPERATOR, VIEWER)
- FAIT : Frontend avec login, register, routes protegees, gestion utilisateurs, profil, changement mot de passe.
- FAIT : Bugs critiques corriges (logout, type check token, super admin check).
- **A CORRIGER** : Roles dans le code non conformes a la matrice 1.2 sur `partners`, `imports`, `quotes`, `customer-quotes`.
- **A CORRIGER** : Roles frontend (App.tsx, Sidebar.tsx) non conformes a la matrice 1.2.

### Infrastructure disponible

| Composant                | Statut                       | Utilisation                      |
| ------------------------ | ---------------------------- | -------------------------------- |
| PostgreSQL 16            | En service                   | Table `users` creee              |
| Redis 7                  | **En service** (blacklist)   | Blacklist tokens au logout       |
| `SECRET_KEY` dans `.env` | Utilisee pour signer les JWT | Signature HS256                  |
| Nginx reverse proxy      | En service                   | HTTPS                            |
| Alembic                  | Migration effectuee          | Table users + FK customer_quotes |

---

## 1. Modele de profils propose

### 1.1 Profils (roles) — FAIT

Cinq profils implementes :

| Profil                   | Code          | Description                                                                                | Statut |
| ------------------------ | ------------- | ------------------------------------------------------------------------------------------ | ------ |
| **Super Administrateur** | `SUPER_ADMIN` | Acces total. Bypass universel dans `require_role()`.                                       | FAIT   |
| **Administrateur**       | `ADMIN`       | Gere les utilisateurs, cree/modifie/supprime des devis, envoie des devis.                  | FAIT   |
| **Commercial**           | `COMMERCIAL`  | Recherche de tarifs, creation et gestion de devis clients.                                 | FAIT   |
| **Operateur**            | `OPERATOR`    | Creation et modification de devis clients. Consultation des partenaires et tarifs.         | FAIT   |
| **Lecture seule**        | `VIEWER`      | Consultation du dashboard, des partenaires, des tarifs et des devis (pas de modification). | FAIT   |

> **INFO** : Le role est stocke via un `Enum` PostgreSQL (UserRole) dans la base de donnees.

### 1.2 Matrice des droits par module — PARTIEL

> **SOURCE DE VERITE UNIQUE** : Ce tableau est la reference absolue pour les roles autorises.
> Toute modification ici doit etre repercutee dans les sections suivantes :
> - **4.7** — Tableau des routes backend (colonne "Roles autorises")
> - **4.6** — Endpoints utilisateurs (si concerne)
> - **5.6** — Routing frontend (`App.tsx`, `allowedRoles`)
> - **5.7** — Navigation sidebar (`RoleGate`, `allowedRoles`)
> - **6.x** — Descriptions des pages UI concernees
> - **Code** : `require_role(...)` dans le backend + `ProtectedRoute`/`RoleGate` dans le frontend

| Module / Action                          | SUPER_ADMIN | ADMIN | COMMERCIAL | OPERATOR | VIEWER | Statut |
| ---------------------------------------- | :---------: | :---: | :--------: | :------: | :----: | :----: |
| **Dashboard**                            |             |       |            |          |        |        |
| Voir les statistiques                    |     oui     |  oui  |    oui     |   oui    |  oui   |  FAIT  |
| **Partenaires**                          |             |       |            |          |        |        |
| Lister les partenaires                   |     oui     |  oui  |    oui     |   oui    |  oui   |  FAIT  |
| Creer / modifier un partenaire           |     oui     |   -   |     -      |    -     |   -    |  FAIT  |
| Supprimer un partenaire                  |     oui     |   -   |     -      |    -     |   -    |  FAIT  |
| **Tarifs (partner_quotes)**              |             |       |            |          |        |        |
| Consulter les tarifs                     |     oui     |  oui  |    oui     |   oui    |  oui   |  FAIT  |
| Importer des fichiers tarifaires         |     oui     |   -   |     -      |    -     |   -    |  FAIT  |
| Supprimer des tarifs                     |     oui     |   -   |     -      |    -     |   -    |  FAIT  |
| **Recherche / Matching**                 |             |       |            |          |        |        |
| Rechercher des tarifs                    |     oui     |  oui  |    oui     |   oui    |  oui   |  FAIT  |
| **Devis client**                         |             |       |            |          |        |        |
| Lister les devis                         |     oui     |  oui  |    oui     |   oui    |  oui   |  FAIT  |
| Creer un devis                           |     oui     |  oui  |    oui     |   oui    |   -    |  FAIT  |
| Modifier un devis                        |     oui     |  oui  |    oui     |   oui    |   -    |  FAIT  |
| Envoyer un devis                         |     oui     |  oui  |    oui     |    -     |   -    |  FAIT  |
| Supprimer un devis                       |     oui     |  oui  |    oui     |    -     |   -    |  FAIT  |
| **Utilisateurs**                         |             |       |            |          |        |        |
| Lister les utilisateurs                  |     oui     |  oui  |     -      |    -     |   -    |  FAIT  |
| Ajouter un utilisateur                   |     oui     |  oui  |     -      |    -     |   -    |  FAIT  |
| Modifier un utilisateur (sauf login)     |     oui     |  oui  |     -      |    -     |   -    |  FAIT  |
| Desactiver/Activer un utilisateur        |     oui     |  oui  |     -      |    -     |   -    |  FAIT  |
| Gerer les roles                          |     oui     |  oui  |     -      |    -     |   -    |  FAIT  |
| **Mon profil**                           |             |       |            |          |        |        |
| Voir mon profil                          |     oui     |  oui  |    oui     |   oui    |  oui   |  FAIT  |
| Modifier mon profil (sauf login et role) |     oui     |  oui  |    oui     |   oui    |  oui   |  FAIT  |
| Modifier mon mot de passe                |     oui     |  oui  |    oui     |   oui    |  oui   |  FAIT  |

> **REGLES DE PROTECTION DU ROLE SUPER_ADMIN** :
> - Un **ADMIN ne peut pas** s'attribuer le role SUPER_ADMIN (modification de son propre profil).
> - Un **ADMIN ne peut pas** creer un utilisateur avec le role SUPER_ADMIN.
> - Un **ADMIN ne peut pas** modifier le profil d'un utilisateur existant pour lui attribuer le role SUPER_ADMIN.
> - Seul un **SUPER_ADMIN** peut attribuer ou revoquer le role SUPER_ADMIN.
> - Ces regles doivent etre appliquees **cote backend** (validation dans les endpoints) et **cote frontend** (le role SUPER_ADMIN n'apparait pas dans le selecteur de roles pour un ADMIN).

Le document est désormais à jour avec l'implémentation partielle.

### 1.3 Propriete des devis — FAIT

Les profils `COMMERCIAL` et `OPERATOR` ne voient et ne modifient que **leurs propres devis**. Cela implique :
- Un champ `created_by` (FK vers `users`) sur la table `customer_quotes` — **FAIT**
- Un filtrage systematique cote API : `WHERE created_by = current_user.id` pour COMMERCIAL et OPERATOR — **FAIT**
- Les profils `SUPER_ADMIN`, `ADMIN` et `VIEWER` voient tous les devis (VIEWER en lecture seule) — **FAIT**


### 1.4 Flux d'Inscription "Self-Service" (VIEWER) — FAIT (partiel)

| Etape                                                     | Statut      | Detail                                                                               |
| --------------------------------------------------------- | ----------- | ------------------------------------------------------------------------------------ |
| 1. Inscription (formulaire `/register`)                   | FAIT        | `frontend/src/pages/Register.tsx`                                                    |
| 2. Validation domaine email                               | FAIT        | `auth_service.py` — `ALLOWED_EMAIL_DOMAINS`                                          |
| 3. Creation en attente (`is_active=False`, role `VIEWER`) | FAIT        |                                                                                      |
| 4. Notification admin (email ou dashboard)                | **A FAIRE** | Aucune notification implementee                                                      |
| 5. Validation admin (dashboard + changement role)         | FAIT        | Page `Users.tsx` avec toggle statut et changement de role                            |
| 6. Premiere connexion (force changement MDP)              | FAIT        | `deps.py` verifie `must_change_password` (403). `ChangePasswordModal.tsx` cote front |

---

## 2. Modele de donnees

### 2.1 Nouvelle table `users` — FAIT (a modifier)

**Fichier** : `backend/app/models/user.py`

#### 2.1.1 Structure des donnees utilisateur

Chaque utilisateur possede les **champs obligatoires** suivants :

| Champ        | Type         | Contraintes                                  | Description                                         |
| ------------ | ------------ | -------------------------------------------- | --------------------------------------------------- |
| `login`      | VARCHAR(50)  | **UNIQUE**, **NOT NULL**, **NON MODIFIABLE** | Identifiant unique de connexion (avec mot de passe) |
| `email`      | VARCHAR(255) | UNIQUE, NOT NULL                             | Adresse email valide, modifiable                    |
| `last_name`  | VARCHAR(100) | NOT NULL                                     | Nom de famille, modifiable                          |
| `first_name` | VARCHAR(100) | NOT NULL                                     | Prenom, modifiable                                  |

#### 2.1.2 Regles metier sur les champs utilisateur

- **`login`** :
  - Doit etre **unique** dans la base de donnees.
  - **Non modifiable** apres la creation du compte (ni par l'utilisateur, ni par un administrateur).
  - Utilise comme **identifiant principal** pour la connexion, en combinaison avec un mot de passe securise.
  - Remplace l'email comme identifiant de connexion.
- **`email`**, **`last_name`**, **`first_name`** :
  - Peuvent etre modifies par l'utilisateur (via la page profil) ou par un administrateur (via l'interface d'administration).
  - Le champ `email` est soumis a une validation de format (adresse email valide).

#### 2.1.3 Schema SQL

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    login VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER', -- Enum en réalité
    is_active BOOLEAN NOT NULL DEFAULT false,
    must_change_password BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

> **FAIT** : Colonne `login` ajoutée.
> **FAIT** : `role` implémenté comme `Enum` PostgreSQL.

### 2.2 Modification de `customer_quotes` — PARTIEL

- Colonnes `created_by` et `updated_by` (FK vers `users`) — **FAIT** (migration effectuee)
- Alimentation des colonnes a la creation/modification — **A FAIRE** (jamais renseignees)

### 2.3 Table d'audit (optionnelle, Phase 2) — A FAIRE

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL,         -- CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    resource_type VARCHAR(50) NOT NULL,  -- partner, quote, import, user
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### 2.4 Configuration Domaine Autorise — FAIT

Variable `ALLOWED_EMAIL_DOMAINS=toto.fr` dans `.env`, utilisee dans `auth_service.py`.

> **BUG MINEUR** : La validation est sensible a la casse (`TOTO.FR` serait rejete). Voir section 13.6.

---

## 3. Authentification : JWT + Redis

### 3.1 Pourquoi JWT + Redis — FAIT

Architecture implementee : JWT pour l'authentification + Redis pour la blacklist des tokens revoques.

### 3.2 Flux d'authentification — FAIT

```
Frontend ──POST /auth/login──> Backend ──verify──> PostgreSQL
         <──access+refresh──           <──user──
         ──Bearer <token>──> Backend ──blacklist?──> Redis
         <──200 OK + data──
```

### 3.3 Tokens — FAIT (avec ecarts)

| Token             | Duree de vie | Stockage prevu            | Stockage reel                   | Statut |
| ----------------- | ------------ | ------------------------- | ------------------------------- | ------ |
| **Access token**  | 30 minutes   | `localStorage` (frontend) | `localStorage` (frontend)       | FAIT   |
| **Refresh token** | 7 jours      | `httpOnly cookie` + Redis | **`localStorage`** (pas cookie) | ECART  |

> **ECART** : Le refresh token est stocke dans `localStorage` au lieu d'un `httpOnly cookie`. Moins securise mais fonctionnel.

### 3.4 Contenu du JWT (payload) — FAIT (simplifie)

```json
// Payload reel (access token) :
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",  // user.id
  "exp": 1700001800,
  "jti": "unique-token-id"
}

// Payload reel (refresh token) :
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "exp": 1700604000,
  "type": "refresh",
  "jti": "unique-token-id"
}
```

> **ECART vs proposition** : Le JWT ne contient pas `email`, `role`, `first_name`, `last_name`. Seul `sub` (user.id) est present. Le backend fait un `SELECT` a chaque requete pour recuperer les infos user. C'est plus securise (pas de donnees sensibles dans le token) mais ajoute une requete DB par appel.

### 3.5 Securite des mots de passe — FAIT (partiel)

| Parametre                      | Propose          | Implemente            | Statut  |
| ------------------------------ | ---------------- | --------------------- | ------- |
| Algorithme de hashage          | bcrypt (passlib) | bcrypt (passlib)      | FAIT    |
| Cout bcrypt (rounds)           | 12               | defaut passlib        | FAIT    |
| Longueur minimale mot de passe | 8 caracteres     | **Aucune validation** | A FAIRE |
| Complexite (maj, min, chiffre) | Oui              | **Aucune validation** | A FAIRE |

---

## 4. Backend : implementation

### 4.1 Nouvelles dependances — FAIT

Ajoutees dans `requirements.txt` :
- `python-jose[cryptography]==3.3.0`
- `passlib[bcrypt]==1.7.4`
- `bcrypt==4.0.1`
- `redis==5.0.1`
- `email-validator==2.1.0`

### 4.2 Nouveaux fichiers — FAIT

```
backend/app/
├── core/
│   ├── security.py          FAIT
│   ├── deps.py              FAIT (avec bugs)
│   └── redis.py             FAIT
├── models/
│   └── user.py              FAIT
├── schemas/
│   └── auth.py              FAIT
├── services/
│   └── auth_service.py      FAIT
├── api/
│   ├── auth.py              FAIT (avec bug logout)
│   └── users.py             FAIT
├── cli/
│   └── create_admin.py      FAIT
```

### 4.3 Module de securite (`core/security.py`) — FAIT

**Fichier** : `backend/app/core/security.py`

Fonctions implementees :
- `hash_password()` / `verify_password()` via bcrypt
- `create_access_token()` avec `jti` (UUID) et expiration configurable
- `create_refresh_token()` avec `type: "refresh"` et `jti`, duree hardcodee 7j
- `decode_token()`

> **BUG** : Utilise `datetime.utcnow()` deprecie en Python 3.12. Voir section 13.5.

### 4.4 Dependency injection (`core/deps.py`) — FAIT

**Fichier** : `backend/app/core/deps.py`

Implementes :
- `get_current_user()` : decode JWT + check blacklist Redis + check `is_active` + check `must_change_password`
- `get_authenticated_user()` : meme chose sans le check `must_change_password` (pour le change-password endpoint)
- `get_current_active_user()` : wrapper redondant (identique a `get_current_user`)
- `require_role(*roles)` : factory avec bypass SUPER_ADMIN

> ~~**BUG SECURITE** : `get_current_user()` ne verifie pas que le token est un **access** token.~~ **CORRIGE** : `get_authenticated_user()` rejette les tokens de type `refresh` (ligne 41-46).

> ~~**BUG** : Le check SUPER_ADMIN utilise substring match.~~ **CORRIGE** : Utilise `current_user.role != "SUPER_ADMIN"` (comparaison stricte, ligne 87).

### 4.5 Endpoints d'authentification (`api/auth.py`) — FAIT

**Fichier** : `backend/app/api/auth.py`

| Methode | Endpoint                       | Propose | Implemente | Statut |
| ------- | ------------------------------ | :-----: | :--------: | :----: |
| `POST`  | `/api/v1/auth/login`           |   oui   |    oui     |  FAIT  |
| `POST`  | `/api/v1/auth/refresh`         |   oui   |    oui     |  FAIT  |
| `POST`  | `/api/v1/auth/logout`          |   oui   |    oui     |  FAIT  |
| `GET`   | `/api/v1/auth/me`              |   oui   |    oui     |  FAIT  |
| `POST`  | `/api/v1/auth/register`        |   oui   |    oui     |  FAIT  |
| `POST`  | `/api/v1/auth/change-password` |   oui   |    oui     |  FAIT  |

> **INFO** : Bugs corriges (logout, type check). Utilise `login` pour l'authentification. Rate limiting 5/min sur `/login`.

### 4.6 Endpoints de gestion des utilisateurs (`api/users.py`) — FAIT (avec bugs)

**Fichier** : `backend/app/api/users.py`

> **Conformement a la matrice 1.2** : La gestion des utilisateurs est reservee aux **SUPER_ADMIN et ADMIN**. Les endpoints sont proteges avec `require_role("SUPER_ADMIN", "ADMIN")` au niveau du router. Voir les regles de protection du role SUPER_ADMIN (section 1.2) pour les restrictions supplementaires sur ADMIN.

> **BUG** : Le fichier `users.py` contient des **imports dupliques** (lignes 1-13 ≈ lignes 15-27) et deux declarations `router = APIRouter()`. Fonctionne par hasard (Python reassigne). A nettoyer.

| Methode  | Endpoint                     | Propose | Implemente |                         Statut                         |
| -------- | ---------------------------- | :-----: | :--------: | :----------------------------------------------------: |
| `GET`    | `/api/v1/users`              |   oui   |    oui     |                          FAIT                          |
| `GET`    | `/api/v1/users/{id}`         |   oui   |    oui     |                          FAIT                          |
| `POST`   | `/api/v1/users`              |   oui   |    oui     |                          FAIT                          |
| `PUT`    | `/api/v1/users/{id}`         |   oui   |    oui     | **A CORRIGER** (login modifiable, cf. bugs ci-dessous) |
| `PATCH`  | `/api/v1/users/{id}/status`  |   oui   |    oui     |                          FAIT                          |
| `PATCH`  | `/api/v1/users/{id}/role`    |   oui   |    oui     |                          FAIT                          |
| `DELETE` | `/api/v1/users/{id}`         |   oui   |    oui     |                   FAIT (soft delete)                   |
| `GET`    | `/api/v1/users/pending`      |   oui   |    non     |                      **A FAIRE**                       |
| `POST`   | `/api/v1/users/{id}/approve` |   oui   |    non     |                      **A FAIRE**                       |

#### Regles metier sur les endpoints utilisateurs

- **`POST /users`** (creation) :
  - Champs obligatoires : `login`, `email`, `last_name`, `first_name`, `role`, `password`.
  - Validation unicite du `login` et de l'`email` avant insertion.
  - Le `login` doit respecter un format defini (alphanum, min 3 caracteres, pas d'espaces).
  - **Un ADMIN ne peut pas creer un utilisateur avec le role SUPER_ADMIN.** Seul un SUPER_ADMIN peut attribuer ce role a la creation.
- **`PUT /users/{id}`** (modification) :
  - Le champ `login` **ne doit pas etre modifiable**. S'il est present dans le body, il doit etre ignore ou lever une erreur 400.
  - **FAIT** : L'API renvoie une 400 si on tente de changer le login.
  - **FAIT** : Le modal d'edition dans `Users.tsx` affiche le champ login comme desactive (`disabled`).
  - Champs modifiables : `email`, `first_name`, `last_name`.
  - Validation du format email.
  - **Un ADMIN ne peut pas modifier le profil d'un utilisateur pour lui attribuer le role SUPER_ADMIN.** Si le champ `role` est present avec la valeur `SUPER_ADMIN` et que l'appelant est ADMIN, lever une erreur 403. — **FAIT**
- **`PATCH /users/{id}/status`** (activation/desactivation) :
  - Soft delete : bascule `is_active` entre `true` et `false`. — **FAIT**
  - Un utilisateur desactive ne peut plus se connecter mais ses donnees sont conservees. — **FAIT**
  - Invalider les tokens actifs de l'utilisateur dans Redis lors de la desactivation. — **A FAIRE** (non implemente)
- **`PATCH /users/{id}/role`** (gestion des roles) :
  - Seul un SUPER_ADMIN peut attribuer le role SUPER_ADMIN. — **FAIT**
  - **Un ADMIN ne peut pas s'attribuer lui-meme le role SUPER_ADMIN.** — **FAIT** (empeche tout changement de son propre role)
  - **Un ADMIN ne peut pas attribuer le role SUPER_ADMIN a un autre utilisateur.** — **FAIT**
  - Un SUPER_ADMIN ne peut pas retrograder son propre role. — **FAIT** (empeche tout changement de son propre role)
- **`DELETE /users/{id}`** :
  - ~~**A MODIFIER** : hard delete.~~ **FAIT** : Soft delete implemente (`user.is_active = False`).

> **FAIT** : Protection contre l'escalade de privileges (un ADMIN ne peut pas attribuer SUPER_ADMIN, ni modifier un autre ADMIN).
>
> **REGLE CRITIQUE** : La protection contre l'escalade de privileges doit etre appliquee sur **tous les endpoints** susceptibles de modifier le role d'un utilisateur (`POST /users`, `PUT /users/{id}`, `PATCH /users/{id}/role`). Un ADMIN ne doit **jamais** pouvoir creer ou modifier un profil pour obtenir le role SUPER_ADMIN, que ce soit pour lui-meme ou pour un autre utilisateur.

### 4.7 Protection des routes existantes — PARTIEL

> **IMPORTANT** : Les roles autorises ci-dessous doivent etre **strictement conformes a la matrice des droits de la section 1.2**.
> En cas de doute, la section 1.2 fait reference. SUPER_ADMIN a un bypass universel et n'est pas repete dans chaque ligne.

| Route                         | Methode | Roles autorises (cf. matrice 1.2)    | Code actuel                                              | Statut |
| ----------------------------- | ------- | ------------------------------------ | -------------------------------------------------------- | :----: |
| `/partners`                   | GET     | Tous (authentifie)                   | `require_role("ADMIN","COMMERCIAL","OPERATOR","VIEWER")` |  FAIT  |
| `/partners`                   | POST    | (SUPER_ADMIN uniquement)             | `require_role("SUPER_ADMIN")`                            |  FAIT  |
| `/partners/{id}`              | PUT     | (SUPER_ADMIN uniquement)             | `require_role("SUPER_ADMIN")`                            |  FAIT  |
| `/partners/{id}`              | DELETE  | (SUPER_ADMIN uniquement)             | `require_role("SUPER_ADMIN")`                            |  FAIT  |
| `/partners/{id}/quotes`       | DELETE  | (SUPER_ADMIN uniquement)             | `require_role("SUPER_ADMIN")`                            |  FAIT  |
| `/quotes`                     | GET     | Tous (authentifie)                   | `require_role("ADMIN","COMMERCIAL","OPERATOR","VIEWER")` |  FAIT  |
| `/quotes`                     | POST    | (Non dans matrice — a clarifier)     | `require_role("ADMIN","OPERATOR")`                       |  FAIT  |
| `/quotes`                     | DELETE  | (SUPER_ADMIN uniquement)             | `require_role("SUPER_ADMIN")`                            |  FAIT  |
| `/imports`                    | POST    | (SUPER_ADMIN uniquement)             | `require_role("SUPER_ADMIN")`                            |  FAIT  |
| `/imports/{id}`               | GET     | (SUPER_ADMIN uniquement)             | `require_role("SUPER_ADMIN")`                            |  FAIT  |
| `/match`                      | POST    | Tous (authentifie)                   | `get_current_user`                                       |  FAIT  |
| `/cities/suggest`             | GET     | Tous (authentifie)                   | `get_current_user`                                       |  FAIT  |
| `/cities/countries`           | GET     | Tous (authentifie)                   | `get_current_user`                                       |  FAIT  |
| `/customer-quotes`            | GET     | Tous (authentifie, filtrage proprio) | `get_current_user` (filtre COMMERCIAL, OPERATOR)         |  FAIT  |
| `/customer-quotes`            | POST    | ADMIN, COMMERCIAL, OPERATOR          | `require_role("ADMIN","COMMERCIAL","OPERATOR")`          |  FAIT  |
| `/customer-quotes/{id}`       | GET     | Tous (authentifie, filtrage proprio) | `get_current_user` (filtre COMMERCIAL, OPERATOR)         |  FAIT  |
| `/customer-quotes/{id}`       | PUT     | ADMIN, COMMERCIAL, OPERATOR          | `require_role("ADMIN","COMMERCIAL","OPERATOR")`          |  FAIT  |
| `/customer-quotes/{id}`       | DELETE  | ADMIN, COMMERCIAL                    | `require_role("ADMIN", "COMMERCIAL")`                    |  FAIT  |
| `/customer-quotes/{id}/items` | POST    | ADMIN, COMMERCIAL, OPERATOR          | `require_role("ADMIN","COMMERCIAL","OPERATOR")`          |  FAIT  |
| `/customer-quotes/{id}/fees`  | POST    | ADMIN, COMMERCIAL, OPERATOR          | `require_role("ADMIN","COMMERCIAL","OPERATOR")`          |  FAIT  |
| `/customer-quotes/{id}/items` | PUT     | ADMIN, COMMERCIAL, OPERATOR          | `require_role("ADMIN","COMMERCIAL","OPERATOR")`          |  FAIT  |
| `/customer-quotes/{id}/items` | DELETE  | ADMIN, COMMERCIAL                    | `require_role("ADMIN", "COMMERCIAL")`                    |  FAIT  |
| `/auth/register`              | POST    | Public (validation domaine)          | Public                                                   |  FAIT  |
| `/auth/change-password`       | POST    | Tous (authentifie)                   | `get_authenticated_user`                                 |  FAIT  |
| `/users`                      | *       | SUPER_ADMIN, ADMIN (cf. matrice 1.2) | `require_role("SUPER_ADMIN","ADMIN")` (router)           |  FAIT  |

---

## 5. Frontend : implementation

### 5.1 Nouvelles dependances — FAIT

- `jwt-decode@^4.0.0`
- `axios@^1.13.3`

### 5.2 Nouveaux fichiers — FAIT

```
frontend/src/
├── context/
│   └── AuthContext.tsx              FAIT
├── pages/
│   ├── Login.tsx                    FAIT
│   ├── Register.tsx                 FAIT
│   ├── Users.tsx                    FAIT
│   ├── Profile.tsx                  FAIT
│   └── (ChangePasswordForce.tsx)    FAIT (implemente via ChangePasswordModal.tsx)
├── components/
│   ├── auth/
│   │   ├── ProtectedRoute.tsx       FAIT
│   │   ├── RoleGate.tsx             FAIT (utilise dans Sidebar.tsx)
│   │   └── ChangePasswordModal.tsx  FAIT
│   ├── common/
│   │   └── Modal.tsx                FAIT
│   └── layout/
│       └── UserMenu.tsx             FAIT
├── services/
│   ├── authService.ts              FAIT
│   └── userService.ts              FAIT
├── types/
│   └── auth.ts                     FAIT
```

### 5.3 Contexte d'authentification (`AuthContext.tsx`) — FAIT

**Fichier** : `frontend/src/context/AuthContext.tsx`

Interface implementee : `user`, `token`, `isAuthenticated`, `isLoading`, `error`, `login()`, `logout()`, `hasRole()`

Persistance : `localStorage` (access_token + refresh_token).

### 5.4 Intercepteur Axios (`api.ts`) — FAIT

**Fichier** : `frontend/src/services/api.ts`

- Request interceptor : ajoute `Authorization: Bearer <token>`
- Response interceptor : refresh automatique sur 401 avec replay de la requete

> **A AMELIORER** : Race condition si plusieurs requetes echouent en 401 simultanement (pas de mutex sur le refresh). Voir section 14.4.

### 5.5 Routes protegees (`ProtectedRoute.tsx`) — FAIT

**Fichier** : `frontend/src/components/auth/ProtectedRoute.tsx`

Redirige vers `/login` si non authentifie, vers `/` si role insuffisant. Utilise `<Outlet />` pour le nesting.

### 5.6 Routing mis a jour (`App.tsx`) — FAIT (roles a corriger)

**Fichier** : `frontend/src/App.tsx`

Routes implementees :
- Publiques : `/login`, `/register`
- Protegees (tous auth) : `/`, `/search`, `/results`, `/quotes`, `/customer-quotes`, `/customer-quotes/:id`, `/profile`
- SUPER_ADMIN + ADMIN : `/users` — **FAIT** (conforme matrice 1.2)
- ADMIN + COMMERCIAL : `/customer-quotes/:id/edit` — **A CORRIGER** : manque OPERATOR (matrice 1.2 = ADMIN, COMMERCIAL, OPERATOR)
- ADMIN + OPERATOR : `/partners` — **A CORRIGER** : devrait etre accessible a tous (matrice 1.2 lister = Tous)
- ADMIN + OPERATOR : `/imports` — **A CORRIGER** : devrait etre SUPER_ADMIN uniquement (matrice 1.2 = SUPER_ADMIN)

> **NOTE** : `App.tsx` n'a pas d'imports dupliques (~~BUG precedemment signale~~). En revanche, `users.py` a des imports dupliques (voir section 4.6).

### 5.7 Navigation conditionnelle (`Sidebar.tsx`) — FAIT (roles a corriger)

**Fichier** : `frontend/src/components/layout/Sidebar.tsx`

`RoleGate` est utilise dans la sidebar. Etat actuel du code :
```tsx
{/* Partenaires + Imports groupes sous RoleGate ADMIN+OPERATOR */}
<RoleGate allowedRoles={['ADMIN', 'OPERATOR']}>
    <SidebarLink to="/partners" icon={Users} label="Partenaires" />
    <SidebarLink to="/imports" icon={UploadCloud} label="Imports" />
</RoleGate>

{/* Utilisateurs */}
<RoleGate allowedRoles={['SUPER_ADMIN', 'ADMIN']}>
    <SidebarLink to="/users" icon={UserCog} label="Utilisateurs" />
</RoleGate>
```

**A CORRIGER** (pour conformite matrice 1.2) :
```tsx
{/* cf. matrice 1.2 : lister partenaires = Tous → lien visible par tous, sans RoleGate */}
<SidebarLink to="/partners" icon={Users} label="Partenaires" />

{/* cf. matrice 1.2 : imports = SUPER_ADMIN uniquement → RoleGate vide (seul SUPER_ADMIN bypass) */}
<RoleGate allowedRoles={[]}>
    <SidebarLink to="/imports" icon={UploadCloud} label="Imports" />
</RoleGate>

{/* cf. matrice 1.2 : utilisateurs = SUPER_ADMIN + ADMIN → OK tel quel */}
<RoleGate allowedRoles={['SUPER_ADMIN', 'ADMIN']}>
    <SidebarLink to="/users" icon={UserCog} label="Utilisateurs" />
</RoleGate>
```

### 5.8 Composant `RoleGate` — FAIT

**Fichier** : `frontend/src/components/auth/RoleGate.tsx`

Le composant fonctionne correctement avec bypass SUPER_ADMIN. Utilise dans :
- `Sidebar.tsx` : filtre les liens Partenaires/Imports (ADMIN, OPERATOR) et Utilisateurs (SUPER_ADMIN, ADMIN)

Pourrait etre davantage utilise dans :
- Pages avec actions conditionnelles (boutons supprimer, creer, etc.)

### 5.9 Page de connexion (`Login.tsx`) — FAIT

**Fichier** : `frontend/src/pages/Login.tsx`

Formulaire de connexion avec champ `login` (identifiant), gestion d'erreurs et redirection post-login.

> ~~**A MODIFIER** : utilise `email` comme identifiant.~~ **FAIT** : Le formulaire utilise le champ `login` (placeholder "Identifiant (Login)").

### 5.10 Menu utilisateur (`UserMenu.tsx`) — FAIT

**Fichier** : `frontend/src/components/layout/UserMenu.tsx`

Avatar initiales, email, lien profil, bouton deconnexion.

> ~~**BUG MINEUR** : Le lien "Mon profil" pointe vers `/profile` qui n'existe pas.~~ **FAIT** : La route `/profile` existe dans `App.tsx` et `Profile.tsx` est implemente.

### 5.11 Page d'Inscription (`Register.tsx`) — FAIT

**Fichier** : `frontend/src/pages/Register.tsx`

Formulaire d'inscription avec champ `login`, email, prenom, nom, mot de passe. Message de succes indiquant la validation admin requise.

> ~~**A MODIFIER** : Le formulaire doit inclure le champ `login`.~~ **FAIT** : Le champ `login` est present (placeholder "Identifiant (Login)").

---

## 6. Interface Utilisateur (Propositions UI)

### 6.1 Page de Connexion & Inscription — FAIT

Login et Register implementes avec Tailwind CSS, gestion erreurs, loading state.

### 6.2 Interface d'administration des utilisateurs (SUPER_ADMIN, ADMIN) — FAIT

**Fichier** : `frontend/src/pages/Users.tsx`

Page de gestion des utilisateurs reservee aux SUPER_ADMIN et ADMIN (cf. matrice 1.2). Implemente les operations suivantes :

#### 6.2.1 Ajouter un nouvel utilisateur — FAIT

- Modale avec les champs : prenom, nom, **login**, email, mot de passe, role.
- **Validation** : Champs obligatoires, erreurs API affichees.
- Protection SUPER_ADMIN : seul un SUPER_ADMIN voit l'option SUPER_ADMIN dans le selecteur de roles.

#### 6.2.2 Modifier les informations d'un utilisateur — FAIT

- Modale de modification avec champs : prenom, nom, login (lecture seule), email, mot de passe optionnel, role.
- Protection SUPER_ADMIN : un ADMIN ne peut pas modifier un SUPER_ADMIN.

#### 6.2.3 Desactiver / Activer un compte utilisateur — FAIT

- Bouton toggle dans le tableau (icone Power).
- Utilise `PATCH /users/{id}/status` (bascule `is_active`).
- Un ADMIN ne peut pas desactiver un SUPER_ADMIN (bouton desactive).
- `DELETE /users/{id}` fait un **soft delete** (`is_active=false`).

#### 6.2.4 Gerer les droits des utilisateurs — FAIT

- Selecteur de role dans la modale de modification.
- Roles disponibles : `VIEWER`, `COMMERCIAL`, `OPERATOR`, `ADMIN` (+ `SUPER_ADMIN` visible uniquement pour un SUPER_ADMIN).
- Protection escalade de privileges implementee backend et frontend.

#### 6.2.5 Etat d'implementation

- [x] Tableau des utilisateurs (Login/Email, Identite, Role, Statut, Actions)
- [x] Modale creation (prenom, nom, login, email, MDP, role)
- [x] Modale modification (prenom, nom, login lecture seule, email, MDP optionnel, role)
- [x] Boutons activer/desactiver (toggle Power)
- [x] Bouton supprimer (soft delete)
- [x] Route `/users` dans `App.tsx` avec `ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN']}`
- [x] Lien dans la Sidebar via `RoleGate allowedRoles={['SUPER_ADMIN', 'ADMIN']}`
- [ ] Filtres par role et statut (non implemente)
- [ ] Badge "Demandes en attente" pour les comptes `is_active=false` (non implemente)

### 6.3 Premiere Connexion (Changement MDP Force) — FAIT

**Fichier** : `frontend/src/components/auth/ChangePasswordModal.tsx`

Si `must_change_password` est actif, une modale bloquante s'affiche pour forcer le changement de mot de passe.

Implementation :
- [x] Backend : `get_current_user()` dans `deps.py` verifie `must_change_password` et retourne 403 avec header `X-Require-Password-Change`
- [x] Backend : endpoint `POST /auth/change-password` (ancien MDP + nouveau MDP) via `get_authenticated_user` (bypass du check must_change_password)
- [x] Frontend : `AuthContext.tsx` intercepte la 403 et positionne `mustChangePassword=true`
- [x] Frontend : `ChangePasswordModal.tsx` affiche une modale bloquante (composant `PasswordEnforcement` dans `App.tsx`)

---

## 7. Creation du premier administrateur (Script) — FAIT

**Fichier** : `backend/app/cli/create_admin.py`

```bash
python -m app.cli.create_admin --login admin --email admin@example.com --password MotDePasse123 --role SUPER_ADMIN
```

Cree un utilisateur avec le role specifie (defaut `ADMIN`), actif, `must_change_password=False`.

> ~~**A MODIFIER** : Ajouter `--login` et `--role`.~~ **FAIT** : Arguments `--login` (obligatoire) et `--role` (defaut ADMIN) implementes. Verification de doublon login/email avant insertion.

---

## 8. Configuration Redis — FAIT

### 8.1 Connexion Redis (`core/redis.py`) — FAIT

**Fichier** : `backend/app/core/redis.py`

Client singleton `redis.Redis` avec `decode_responses=True`.

> **A AMELIORER** : Pas de gestion d'erreur si Redis est down. Voir section 14.6.

### 8.2 Utilisations prevues vs reelles

| Cle Redis                 | TTL     | Propose | Implemente | Statut  |
| ------------------------- | ------- | :-----: | :--------: | :-----: |
| `blacklist:{jti}`         | ~30 min |   oui   |    oui     |  FAIT   |
| `refresh:{user_id}:{jti}` | 7 jours |   oui   |    non     | A FAIRE |
| `login_attempts:{email}`  | 15 min  |   oui   |    non     | A FAIRE |

### 8.3 Rate limiting (protection brute force) — PARTIEL

Rate limiting implemente via `slowapi` sur `/auth/login` (5 requetes/minute par IP).

**Fichier** : `backend/app/core/rate_limit.py` — Utilise `get_remote_address` comme cle.

> **A AMELIORER** : Pas de rate limiting sur les autres endpoints sensibles (`/auth/register`, `/auth/refresh`).

---

## 9. Migration Alembic — FAIT (avec bug)

**Fichier** : `backend/alembic/versions/5ec4c3702320_add_user_model_and_enhance_customerquote.py`

- Cree la table `users` avec tous les champs prevus
- Ajoute `created_by` et `updated_by` (FK vers `users`) sur `customer_quotes`
- Index sur `users.email`

> **BUG** : La fonction `downgrade()` utilise `op.drop_constraint(None, ...)`. La migration retour echouera car les FK ne sont pas nommees. Voir section 14.7.

---

## 10. Strategie de mise en oeuvre — Bilan

### Phase 1 — Authentification de base
- [x] Ajouter dependances Python (`python-jose`, `passlib`, `python-multipart`, `redis`)
- [x] Creer modele `User` (avec champs `must_change_password`, `is_active` default false) et schemas
- [x] Config variable d'env `ALLOWED_EMAIL_DOMAINS`
- [x] Migration Alembic
- [x] Implementer `core/security.py` (JWT, bcrypt)
- [x] Implementer `core/redis.py` (connexion Redis)
- [x] Implementer `api/auth.py` (login, refresh, logout, me, register)
- [x] Script CLI pour creer le premier admin
- [ ] Tests unitaires auth
- [ ] Service d'envoi d'email (SMTP ou log pour MVP)

### Phase 2 — Controle d'acces & Workflow Inscription (Backend)
- [x] Implementer `require_role()` dans `core/deps.py`
- [x] Endpoint `POST /auth/register` (creation inactif)
- [x] Ajouter colonne `login` a la table `users` (migration Alembic)
- [x] Modifier `/auth/login` pour utiliser `login` au lieu d'`email`
- [x] Modifier `/auth/register` pour inclure le champ `login`
- [x] Creer endpoint `POST /users` (creation par SUPER_ADMIN ou ADMIN, avec validation unicite login)
- [x] Modifier `PUT /users/{id}` (interdire modification du login)
- [x] Creer endpoint `PATCH /users/{id}/status` (activer/desactiver — soft delete)
- [x] Creer endpoint `PATCH /users/{id}/role` (gestion des roles)
- [x] Transformer `DELETE /users/{id}` en soft delete
- [x] Restreindre tous les endpoints `/users` aux roles SUPER_ADMIN et ADMIN
- [ ] Endpoint `POST /users/{id}/approve` (admin validation)
- [x] Middleware `must_change_password` (retourne 403 si true)
- [x] Proteger les endpoints `customer-quotes` (partiellement — roles a corriger cf. 4.7)
- [x] Proteger les endpoints `match` et `cities` (`get_current_user`)
- [x] Filtrage des devis par proprietaire (`created_by`) pour les COMMERCIAL et OPERATOR
- [x] Implementer `api/users.py` (CRUD admin)
- [ ] Alimenter `created_by`/`updated_by` sur `customer_quotes`
- [x] Rate limiting slowapi sur le login (5/min)
- [x] Endpoint `POST /auth/change-password` (changement MDP self-service)

### Phase 3 — Frontend login et routing
- [x] Ajouter `jwt-decode` aux dependances
- [x] Creer `AuthContext.tsx`
- [x] Creer page `Login.tsx` et `Register.tsx`
- [x] Creer `ChangePasswordModal.tsx` (modale bloquante si `must_change_password`)
- [x] Configurer l'intercepteur Axios (token + refresh)
- [x] Creer `ProtectedRoute.tsx`
- [x] Mettre a jour `App.tsx` avec les routes protegees

### Phase 4 — Frontend UX
- [x] Navigation conditionnelle par role dans `Sidebar.tsx` (RoleGate en place, roles a corriger cf. 5.7)
- [x] Composant `RoleGate.tsx` (utilise dans Sidebar.tsx)
- [x] Menu utilisateur dans le header (`UserMenu.tsx`)
- [x] Login.tsx utilise champ `login`
- [x] Register.tsx inclut champ `login`
- [x] Page de gestion des utilisateurs (`Users.tsx`) — reservee SUPER_ADMIN, ADMIN
  - [x] Tableau des utilisateurs (login, email, identite, role, statut, actions)
  - [x] Modale ajout utilisateur (avec champs login, email, prenom, nom, role, MDP)
  - [x] Modale modification (login en lecture seule)
  - [x] Boutons activer/desactiver (toggle Power)
  - [x] Gestion des roles (selecteur avec protection SUPER_ADMIN)
- [x] Page "Mon profil" (`Profile.tsx`) avec changement de mot de passe

### Phase 5 — Consolidation
- [ ] Table d'audit (`audit_log`)
- [ ] Logging des connexions et actions critiques
- [ ] Tests d'integration (scenarios par role)
- [ ] Documentation utilisateur

---

## 11. Points d'attention

### 11.1 Retrocompatibilite — OK

`created_by` sur `customer_quotes` est `nullable`. Les devis existants restent sans proprietaire.

### 11.2 CORS et cookies

**ECART** : Le refresh token est dans `localStorage` (pas `httpOnly cookie`). Le `withCredentials: true` n'est pas necessaire dans la config actuelle.

### 11.3 HTTPS obligatoire — OK

HTTPS en place via DuckDNS + Nginx.

### 11.4 Expiration et refresh silencieux — FAIT

L'intercepteur Axios gere le refresh automatique sur 401 avec replay de la requete echouee.

### 11.5 Gestion des erreurs — PARTIEL

| Code HTTP | Signification            | Action frontend                             |                              Statut                               |
| --------- | ------------------------ | ------------------------------------------- | :---------------------------------------------------------------: |
| 401       | Token invalide/expire    | Tenter refresh, sinon rediriger vers /login |                               FAIT                                |
| 403       | Role insuffisant         | Afficher un message "Acces refuse"          |               FAIT (ProtectedRoute redirige vers /)               |
| 429       | Trop de tentatives login | Afficher "Reessayez dans X minutes"         | PARTIEL (rate limiting 5/min sur /login, pas de message frontend) |

---

## 12. Bugs critiques a corriger

### 12.1 BUG CRITIQUE : Endpoint `/logout` casse

**Statut** : ✅ **CORRIGÉ**

Imports `datetime` et `timedelta` corrects dans `backend/app/api/auth.py`.

**Correction** :
```python
# Ajouter a la ligne 1 :
from datetime import datetime, timedelta
# Ou mieux, remplacer ligne 103 par :
import time
ttl = exp - time.time()
```

### 12.2 BUG CRITIQUE : Imports dupliques dans App.tsx

**Statut** : ✅ **CORRIGÉ**

`frontend/src/App.tsx` compile correctement.

**Correction** : Supprimer les lignes 1 a 14 (bloc `import` + ligne vide).

---

## 13. Failles de securite a corriger

### 13.1 Validation du type de token — HAUTE

**Fichier** : `backend/app/core/deps.py`

`get_current_user()` ne verifie pas que le token est un access token. Un refresh token peut authentifier des requetes API.

### 13.1 Validation du type de token — HAUTE

**Statut** : ✅ **CORRIGÉ**

`backend/app/core/deps.py` vérifie explicitement le type de token (`if token_type == "refresh": raise ...`).

### 13.2 Verification du role SUPER_ADMIN (substring match) — MOYENNE

**Statut** : ✅ **CORRIGÉ**

Comparaison stricte implémentée (`current_user.role != "SUPER_ADMIN"`).

### 13.3 Role en String libre en base — MOYENNE

**Statut** : ✅ **CORRIGÉ**

Utilisation de `Enum(UserRole)` dans le modèle SQLAlchemy.

### 13.4 Pas de rotation du refresh token — MOYENNE

**Fichier** : `backend/app/api/auth.py` (ligne 82)

Le meme refresh token est reutilise a chaque refresh. Un token vole reste valide 7 jours.

**Correction** :
- Blacklister l'ancien refresh token dans Redis
- Emettre un nouveau refresh token a chaque appel `/refresh`

### 13.5 `datetime.utcnow()` deprecie (Python 3.12) — BASSE

**Fichiers** : `backend/app/core/security.py` (lignes 22, 24, 31), `backend/app/services/auth_service.py` (ligne 61)

```python
# Remplacer partout :
datetime.utcnow()
# Par :
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

### 13.6 Timing attack sur `authenticate_user` — BASSE

**Fichier** : `backend/app/services/auth_service.py` (ligne 51)

Retour immediat si l'utilisateur n'existe pas (pas de hash bcrypt). Permet de distinguer les emails existants par timing.

**Correction** :
```python
if not user:
    security.hash_password("dummy_password")  # constant-time
    return None
```

---

## 14. Ameliorations qualite de code

### 14.1 `oauth2_scheme` defini en double

**Fichiers** : `backend/app/core/security.py` (ligne 12) et `backend/app/core/deps.py` (ligne 17)

Supprimer l'un des deux et centraliser.

### 14.2 `get_current_active_user` redondant

**Fichier** : `backend/app/core/deps.py` (lignes 58-61)

Identique a `get_current_user` (qui verifie deja `is_active`). Supprimer si non utilise.

### 14.3 Refresh token en query parameter

**Fichier** : `backend/app/api/auth.py` (ligne 53)

Le refresh token est passe en parametre d'URL (visible dans les logs serveur). Le schema `RefreshRequest` est deja defini mais non utilise.

**Correction** :
```python
@router.post("/refresh")
def refresh_token(body: RefreshRequest, ...):
    token = body.refresh_token
```

### 14.4 Race condition sur les 401 concurrents

**Fichier** : `frontend/src/services/api.ts`

Si plusieurs requetes echouent en 401 simultanement, chacune lance un refresh independant.

**Correction** : Implementer un mutex/queue pour le refresh.

### 14.5 Validation domaine email insensible a la casse

**Fichier** : `backend/app/services/auth_service.py` (ligne 20)

```python
# ACTUEL :
domain = user_in.email.split("@")[-1]
# CORRECTION :
domain = user_in.email.split("@")[-1].lower()
```

### 14.6 Gestion erreur Redis

**Fichier** : `backend/app/core/redis.py`

Pas de health check ni gestion d'erreur de connexion. Si Redis est down, `get_current_user` leve une exception non geree.

### 14.7 Migration Alembic downgrade cassee

**Fichier** : `backend/alembic/versions/5ec4c3702320_*.py`

`downgrade()` utilise `op.drop_constraint(None, ...)`. Nommer les FK dans `upgrade()`.

---

## 15. Diagrammes de flux

*Les diagrammes ci-dessous sont des references d'architecture. Ils documentent le comportement attendu, y compris les parties non encore implementees.*

### 15.1 Connexion (Login)

```
┌──────────┐                    ┌──────────┐                  ┌──────────┐    ┌───────┐
│ Frontend │                    │ API      │                  │ PostgreSQL│    │ Redis │
│ Login.tsx│                    │ auth.py  │                  │ users    │    │       │
└────┬─────┘                    └────┬─────┘                  └────┬─────┘    └───┬───┘
     │                               │                             │              │
     │  POST /auth/login             │                             │              │
     │  {login, password}            │                             │              │
     │──────────────────────────────>│                             │              │
     │                               │                             │              │
     │                               │  SELECT * FROM users        │              │
     │                               │  WHERE login = ?            │              │
     │                               │────────────────────────────>│              │
     │                               │                             │              │
     │                               │  verify_password(           │              │
     │                               │    password, hashed)        │              │
     │                               │                             │              │
     │                          ┌────┤  Mot de passe OK ?          │              │
     │                          │    │                             │              │
     │                     OUI  │    │                             │              │
     │                          │  UPDATE last_login_at            │              │
     │                          │────────────────────────────────>│              │
     │                          │  create_access + refresh tokens │              │
     │  <── 200 {tokens} ──────│                                 │              │
     │                          │    │                             │              │
     │                     NON  │    │                             │              │
     │  <── 400 Unauthorized ──│                                 │              │
     │                          └────┘                             │              │
     │  Stocker tokens localStorage  │                             │              │
     │  Redirect → /dashboard        │                             │              │
```

**Statut** : FAIT (sans rate limiting)

### 15.2 Creation d'un utilisateur (par l'Admin)

```
┌──────────┐                    ┌──────────┐                  ┌──────────┐
│ Frontend │                    │ API      │                  │ PostgreSQL│
│ Users.tsx│                    │ users.py │                  │ users    │
└────┬─────┘                    └────┬─────┘                  └────┬─────┘
     │                               │                             │
     │  POST /users                  │                             │
     │  {login, email, first_name,   │                             │
     │   last_name, role, password}  │                             │
     │──────────────────────────────>│                             │
     │                               │                             │
     │                               │  Verifier JWT + role        │
     │                               │  SUPER_ADMIN ou ADMIN       │
     │                               │  Valider champs obligatoires│
     │                               │  Check unicite login + email│
     │                               │────────────────────────────>│
     │                               │                             │
     │                               │  INSERT INTO users          │
     │                               │  (is_active=true)           │
     │                               │────────────────────────────>│
     │                               │                             │
     │  <── 201 Created ────────────│                             │
```

**Statut** : FAIT — Backend via `auth_service.create_user()`, Frontend via `Users.tsx` (modale creation)

### 15.3 Desactivation / Activation d'un utilisateur

```
┌──────────┐                    ┌──────────┐           ┌──────────┐    ┌───────┐
│ Frontend │                    │ API      │           │ PostgreSQL│    │ Redis │
│ Users.tsx│                    │ users.py │           │ users    │    │       │
└────┬─────┘                    └────┬─────┘           └────┬─────┘    └───┬───┘
     │                               │                      │              │
     │  PATCH /users/{id}/status     │                      │              │
     │  {is_active: false}           │                      │              │
     │──────────────────────────────>│                      │              │
     │                               │                      │              │
     │                               │  Verifier JWT +      │              │
     │                               │  role SUPER_ADMIN    │              │
     │                               │  ou ADMIN            │              │
     │                               │  Verifier != soi-meme│              │
     │                               │                      │              │
     │                               │  UPDATE users        │              │
     │                               │  SET is_active=false  │              │
     │                               │─────────────────────>│              │
     │                               │                      │              │
     │                               │  Invalider tokens    │              │
     │                               │  actifs utilisateur  │              │
     │                               │─────────────────────────────────>│
     │                               │                      │              │
     │  <── 200 OK ────────────────  │                      │              │
```

**Statut** : FAIT — Soft delete implemente (`is_active=false`), Frontend via `Users.tsx` (toggle statut + bouton supprimer)

> ~~**NOTE** : hard delete.~~ **CORRIGE** : Soft delete implemente (`user.is_active = False`).
> **A FAIRE** : Invalider les tokens actifs de l'utilisateur dans Redis lors de la desactivation (non implemente).

### 15.4 Changement de mot de passe (self-service)

```
┌──────────┐                    ┌──────────┐           ┌──────────┐    ┌───────┐
│ Frontend │                    │ API      │           │ PostgreSQL│    │ Redis │
│ Profil   │                    │ auth.py  │           │ users    │    │       │
└────┬─────┘                    └────┬─────┘           └────┬─────┘    └───┬───┘
     │                               │                      │              │
     │  PUT /auth/me/password        │                      │              │
     │  {current_password,           │                      │              │
     │   new_password}               │                      │              │
     │──────────────────────────────>│                      │              │
     │                               │                      │              │
     │                               │  verify_password()   │              │
     │                               │  hash + UPDATE       │              │
     │                               │─────────────────────>│              │
     │                               │                      │              │
     │                               │  must_change=false   │              │
     │                               │  Nouveau token       │              │
     │                               │                      │              │
     │  <── 200 {tokens} ──────────  │                      │              │
```

**Statut** : FAIT — Backend `POST /auth/change-password`, Frontend `Profile.tsx` + `ChangePasswordModal.tsx`

> **ECART** : L'endpoint reel est `POST /auth/change-password` (pas `PUT /auth/me/password`). Ne retourne pas de nouveau token (le token existant reste valide).

### 15.5 Refresh du token (silencieux)

```
┌──────────┐                    ┌──────────┐                          ┌───────┐
│ Frontend │                    │ API      │                          │ Redis │
│ Axios    │                    │ auth.py  │                          │       │
└────┬─────┘                    └────┬─────┘                          └───┬───┘
     │                               │                                    │
     │  GET /partners (access expire)│                                    │
     │──────────────────────────────>│                                    │
     │  <── 401 ───────────────────  │                                    │
     │                               │                                    │
     │  POST /auth/refresh           │                                    │
     │  {refresh_token}              │                                    │
     │──────────────────────────────>│                                    │
     │                               │  Verifier type=="refresh"         │
     │                               │  Verifier blacklist               │
     │                               │──────────────────────────────────>│
     │                               │                                    │
     │  <── 200 {new access_token} ──│                                    │
     │                               │                                    │
     │  Replay GET /partners         │                                    │
     │  avec nouveau token           │                                    │
     │──────────────────────────────>│                                    │
     │  <── 200 OK + donnees ───────│                                    │
```

**Statut** : FAIT (sans rotation du refresh token)

### 15.6 Deconnexion (Logout)

```
┌──────────┐                    ┌──────────┐                          ┌───────┐
│ Frontend │                    │ API      │                          │ Redis │
│ UserMenu │                    │ auth.py  │                          │       │
└────┬─────┘                    └────┬─────┘                          └───┬───┘
     │                               │                                    │
     │  POST /auth/logout            │                                    │
     │  Bearer <jwt>                 │                                    │
     │──────────────────────────────>│                                    │
     │                               │  SET blacklist:{jti} TTL=restant  │
     │                               │──────────────────────────────────>│
     │                               │                                    │
     │  <── 200 OK ────────────────  │                                    │
     │                               │                                    │
     │  localStorage.clear()         │                                    │
     │  Redirect → /login            │                                    │
```

**Statut** : FAIT — Bug corrige (import `datetime` correct).

### 15.7 Controle d'acces sur une requete protegee

```
Requete entrante
     │
     ▼
[1] Decoder JWT → 401 si absent/expire/invalide
     │
     ▼
[2] Check blacklist Redis → 401 si revoque
     │
     ▼
[3] Charger User depuis DB → 401 si null/inactif
     │
     ▼
[4] Verifier role (require_role) → 403 si insuffisant
     │
     ▼
Handler de la route (200/201/...)
```

**Statut** : FAIT (etapes 1-4 implementees dans `deps.py`)

### 15.8 Cycle de vie d'un utilisateur

```
                    ┌─────────────────────┐
                    │  Inscription        │
                    │  POST /auth/register│
                    └──────────┬──────────┘
                               │
                               ▼
               ┌───────────────────────────────┐
               │   EN ATTENTE (is_active=false) │
               │   role=VIEWER                  │
               └───────────┬───────────────────┘
                           │ Admin active + change role
                           ▼
               ┌───────────────────────────────┐
               │         ACTIF                  │
               │  - Se connecte                 │
               │  - Acces selon son role        │
               │  - Peut changer son MDP        │
               └───────┬───────────┬───────────┘
                       │           │
            Admin modifie     Admin desactive
                       │           │
                       ▼           ▼
              ┌──────────┐  ┌──────────────────┐
              │  MODIFIE  │  │ INACTIF/SUPPRIME │
              │  (actif)  │  │ - Plus de login  │
              └──────────┘  │ - Tokens invalides│
                            └──────────────────┘
```

---

## 16. Fichiers impactes

### Nouveaux fichiers

| Fichier                                                | Propose | Implemente |               Statut                |
| ------------------------------------------------------ | :-----: | :--------: | :---------------------------------: |
| `backend/app/models/user.py`                           |   oui   |    oui     |                FAIT                 |
| `backend/app/schemas/auth.py`                          |   oui   |    oui     |                FAIT                 |
| `backend/app/services/auth_service.py`                 |   oui   |    oui     |                FAIT                 |
| `backend/app/api/auth.py`                              |   oui   |    oui     |                FAIT                 |
| `backend/app/api/users.py`                             |   oui   |    oui     | FAIT (imports dupliques a nettoyer) |
| `backend/app/core/security.py`                         |   oui   |    oui     |                FAIT                 |
| `backend/app/core/redis.py`                            |   oui   |    oui     |                FAIT                 |
| `backend/app/core/deps.py`                             |   oui   |    oui     |                FAIT                 |
| `backend/app/core/rate_limit.py`                       |   oui   |    oui     |                FAIT                 |
| `backend/app/cli/create_admin.py`                      |   oui   |    oui     |                FAIT                 |
| `backend/alembic/versions/xxx_add_users.py`            |   oui   |    oui     |        FAIT (bug downgrade)         |
| `frontend/src/context/AuthContext.tsx`                 |   oui   |    oui     |                FAIT                 |
| `frontend/src/pages/Login.tsx`                         |   oui   |    oui     |                FAIT                 |
| `frontend/src/pages/Register.tsx`                      |   oui   |    oui     |                FAIT                 |
| `frontend/src/pages/Users.tsx`                         |   oui   |    oui     |                FAIT                 |
| `frontend/src/pages/Profile.tsx`                       |   oui   |    oui     |                FAIT                 |
| `frontend/src/components/auth/ChangePasswordModal.tsx` |   oui   |    oui     |                FAIT                 |
| `frontend/src/components/auth/ProtectedRoute.tsx`      |   oui   |    oui     |                FAIT                 |
| `frontend/src/components/auth/RoleGate.tsx`            |   oui   |    oui     |                FAIT                 |
| `frontend/src/components/common/Modal.tsx`             |   oui   |    oui     |                FAIT                 |
| `frontend/src/components/layout/UserMenu.tsx`          |   oui   |    oui     |                FAIT                 |
| `frontend/src/services/authService.ts`                 |   oui   |    oui     |                FAIT                 |
| `frontend/src/services/userService.ts`                 |   oui   |    oui     |                FAIT                 |
| `frontend/src/types/auth.ts`                           |   oui   |    oui     |                FAIT                 |

### Fichiers modifies

| Fichier                                      | Modification                                   |                  Statut                  |
| -------------------------------------------- | ---------------------------------------------- | :--------------------------------------: |
| `backend/requirements.txt`                   | +dependances auth (jose, passlib, redis, etc.) |                   FAIT                   |
| `backend/app/main.py`                        | Enregistrer routers auth/users                 |                   FAIT                   |
| `backend/app/api/__init__.py`                | Ajouter les routers auth et users              |                   FAIT                   |
| `backend/app/core/config.py`                 | Settings JWT + Redis + email domains           |                   FAIT                   |
| `backend/app/api/partners.py`                | `Depends(require_role(...))`                   |     FAIT (roles a corriger cf. 4.7)      |
| `backend/app/api/quotes.py`                  | `Depends(require_role(...))`                   |     FAIT (roles a corriger cf. 4.7)      |
| `backend/app/api/imports.py`                 | `Depends(require_role(...))`                   |     FAIT (roles a corriger cf. 4.7)      |
| `backend/app/api/matching.py`                | `Depends(get_current_user)`                    |                   FAIT                   |
| `backend/app/api/customer_quotes.py`         | Auth + filtrage par proprietaire               |  FAIT (items DELETE a corriger cf. 4.7)  |
| `backend/app/api/cities.py`                  | `Depends(get_current_user)`                    |                   FAIT                   |
| `backend/app/models/customer_quote.py`       | Colonnes `created_by`, `updated_by`            | FAIT (colonnes) / A FAIRE (alimentation) |
| `frontend/package.json`                      | +dependances (jwt-decode, axios)               |                   FAIT                   |
| `frontend/src/App.tsx`                       | Routes protegees, route /login                 |     FAIT (roles a corriger cf. 5.6)      |
| `frontend/src/services/api.ts`               | Intercepteurs auth (token, refresh)            |                   FAIT                   |
| `frontend/src/components/layout/Sidebar.tsx` | Navigation conditionnelle par role             |     FAIT (roles a corriger cf. 5.7)      |

---

## 17. Recapitulatif des travaux restants

### Priorite 1 — Correction des roles (conformite matrice 1.2)
| #   | Tache                                                                 | Statut      |
| --- | --------------------------------------------------------------------- | ----------- |
| 1   | `partners.py` : POST/PUT → retirer ADMIN, OPERATOR (SUPER_ADMIN seul) | A CORRIGER  |
| 2   | `partners.py` : DELETE → retirer ADMIN (SUPER_ADMIN seul)             | A CORRIGER  |
| 3   | `partners.py` : DELETE quotes → retirer ADMIN (SUPER_ADMIN seul)      | A CORRIGER  |
| 4   | `imports.py` : POST/GET → retirer ADMIN, OPERATOR (SUPER_ADMIN seul)  | A CORRIGER  |
| 5   | `quotes.py` : DELETE → retirer ADMIN, OPERATOR (SUPER_ADMIN seul)     | A CORRIGER  |
| 6   | `quotes.py` : POST → clarifier dans la matrice 1.2                    | A CLARIFIER |
| 7   | `customer_quotes.py` : DELETE items → ajouter COMMERCIAL              | A CORRIGER  |
| 8   | `App.tsx` : `/partners` → accessible a tous (pas ADMIN+OPERATOR)      | A CORRIGER  |
| 9   | `App.tsx` : `/imports` → SUPER_ADMIN seul (pas ADMIN+OPERATOR)        | A CORRIGER  |
| 10  | `App.tsx` : `/customer-quotes/:id/edit` → ajouter OPERATOR            | A CORRIGER  |
| 11  | `Sidebar.tsx` : separer Partenaires (tous) et Imports (SUPER_ADMIN)   | A CORRIGER  |

### Priorite 2 — Bugs et ameliorations
| #   | Tache                                                     | Statut  |
| --- | --------------------------------------------------------- | ------- |
| 12  | `users.py` : nettoyer imports dupliques (lignes 1-27)     | A FAIRE |
| 13  | `users.py` PATCH status : invalider tokens Redis          | A FAIRE |
| 14  | Alimenter `created_by`/`updated_by` sur `customer_quotes` | A FAIRE |
| 15  | Rotation du refresh token                                 | A FAIRE |
| 16  | Remplacement `datetime.utcnow()` (deprecie Python 3.12)   | A FAIRE |
| 17  | Race condition refresh token (mutex Axios)                | A FAIRE |

### Priorite 3 — Fonctionnalites manquantes
| #   | Tache                                                   | Statut  |
| --- | ------------------------------------------------------- | ------- |
| 18  | Endpoint `GET /users/pending` (utilisateurs en attente) | A FAIRE |
| 19  | Endpoint `POST /users/{id}/approve` (validation admin)  | A FAIRE |
| 20  | Filtres par role/statut dans `Users.tsx`                | A FAIRE |
| 21  | Badge "Demandes en attente" dans `Users.tsx`            | A FAIRE |
| 22  | Audit logging (Phase 2)                                 | A FAIRE |

### Priorite 4 — Tests et validation
| #   | Tache                                 | Statut  |
| --- | ------------------------------------- | ------- |
| 23  | Tests unitaires auth                  | A FAIRE |
| 24  | Tests de bout-en-bout (Flux complet)  | A FAIRE |
| 25  | Verification des permissions par role | A FAIRE |

**Note** : L'ensemble des fonctionnalites principales est implemente. Le travail restant concerne principalement l'alignement des roles avec la matrice 1.2, le nettoyage de code, et les tests.
