# Propositions : Module d'Authentification et Gestion des Profils

> **Derniere mise a jour** : 2026-02-09
> **Statut global** : ~65% implemente — bugs critiques a corriger, routes non protegees, pages frontend manquantes

---

## Bilan d'implementation

| Categorie | Statut | Detail |
|-----------|--------|--------|
| Infrastructure (deps, Redis, env) | FAIT | Toutes les deps installees, Redis configure |
| Modele User + migration Alembic | FAIT | Table `users` + colonnes `created_by`/`updated_by` sur `customer_quotes` |
| Securite (JWT, bcrypt, deps) | FAIT (avec bugs) | 2 bugs critiques, 3 failles securite |
| Endpoints auth (login, refresh, logout, me, register) | FAIT (avec bugs) | Logout casse (import manquant) |
| Endpoints users (CRUD admin) | FAIT | GET, PUT, DELETE avec protection escalade |
| Protection routes backend | PARTIEL | `partners`, `quotes`, `imports` proteges — `customer-quotes`, `match`, `cities` NON proteges |
| Frontend auth (context, login, register, interceptor) | FAIT | AuthContext, Login, Register, ProtectedRoute, RoleGate, UserMenu, Axios interceptor |
| Frontend pages admin | NON FAIT | Pas de page Users, pas de page Profile, sidebar non filtree |
| Tracabilite (`created_by`/`updated_by`) | NON FAIT | Colonnes existent mais jamais alimentees |
| Audit logging | NON FAIT | Ni table ni service |
| Rate limiting | NON FAIT | |

---

## Contexte

### Situation actuelle

L'application dispose desormais d'un **mecanisme d'authentification partiel** :
- FAIT : JWT access/refresh tokens avec bcrypt et Redis blacklisting
- FAIT : 5 profils definis (SUPER_ADMIN, ADMIN, COMMERCIAL, OPERATOR, VIEWER)
- FAIT : Frontend avec login, register, routes protegees
- A CORRIGER : 2 bugs critiques bloquants (logout casse, imports dupliques App.tsx)
- A FAIRE : 3 modules API non proteges (customer-quotes, match, cities)
- A FAIRE : Pages admin (gestion utilisateurs, profil)

### Infrastructure disponible

| Composant                | Statut                       | Utilisation                     |
| ------------------------ | ---------------------------- | ------------------------------- |
| PostgreSQL 16            | En service                   | Table `users` creee             |
| Redis 7                  | **En service** (blacklist)   | Blacklist tokens au logout      |
| `SECRET_KEY` dans `.env` | Utilisee pour signer les JWT | Signature HS256                 |
| Nginx reverse proxy      | En service                   | HTTPS                           |
| Alembic                  | Migration effectuee          | Table users + FK customer_quotes |

---

## 1. Modele de profils propose

### 1.1 Profils (roles) — FAIT

Cinq profils implementes :

| Profil                   | Code          | Description                                                                           | Statut |
| ------------------------ | ------------- | ------------------------------------------------------------------------------------- | ------ |
| **Super Administrateur** | `SUPER_ADMIN` | Acces total. Bypass universel dans `require_role()`.                                  | FAIT   |
| **Administrateur**       | `ADMIN`       | Gere les utilisateurs et valide les inscriptions.                                     | FAIT   |
| **Commercial**           | `COMMERCIAL`  | Recherche de tarifs, creation et gestion de devis clients.                            | FAIT   |
| **Operateur**            | `OPERATOR`    | Import de fichiers tarifaires, gestion des partenaires et de leurs tarifs.            | FAIT   |
| **Lecture seule**        | `VIEWER`      | Consultation du dashboard et des devis (pas de modification).                         | FAIT   |

> **BUG** : Le role est stocke en `String` libre en base au lieu d'un `Enum` PostgreSQL. Voir section 13.3.

### 1.2 Matrice des droits par module — PARTIEL

| Module / Action                  | SUPER_ADMIN | ADMIN | COMMERCIAL | OPERATOR | VIEWER | Statut |
| -------------------------------- | :---------: | :---: | :--------: | :------: | :----: | :----: |
| **Dashboard**                    |             |       |            |          |        |        |
| Voir les statistiques            |     oui     |  oui  |    oui     |   oui    |  oui   | FAIT   |
| **Partenaires**                  |             |       |            |          |        |        |
| Lister les partenaires           |     oui     |  oui  |    oui     |   oui    |  oui   | FAIT   |
| Creer / modifier un partenaire   |     oui     |   -   |     -      |   oui    |   -    | FAIT   |
| Supprimer un partenaire          |     oui     |   -   |     -      |    -     |   -    | FAIT   |
| **Tarifs (partner_quotes)**      |             |       |            |          |        |        |
| Consulter les tarifs             |     oui     |  oui  |    oui     |   oui    |  oui   | FAIT   |
| Importer des fichiers tarifaires |     oui     |   -   |     -      |   oui    |   -    | FAIT   |
| Supprimer des tarifs             |     oui     |   -   |     -      |   oui    |   -    | FAIT   |
| **Recherche / Matching**         |             |       |            |          |        |        |
| Rechercher des tarifs            |     oui     |  oui  |    oui     |   oui    |  oui   | **A FAIRE** |
| **Devis client**                 |             |       |            |          |        |        |
| Lister les devis                 |     oui     |  oui  |    oui     |    -     |  oui   | **A FAIRE** |
| Creer un devis                   |     oui     |   -   |    oui     |    -     |   -    | **A FAIRE** |
| Modifier un devis                |     oui     |   -   |    oui     |    -     |   -    | **A FAIRE** |
| Envoyer un devis                 |     oui     |   -   |    oui     |    -     |   -    | **A FAIRE** |
| Supprimer un devis               |     oui     |  oui  |    oui     |    -     |   -    | **A FAIRE** |
| **Utilisateurs**                 |             |       |            |          |        |        |
| Lister les utilisateurs          |     oui     |  oui  |     -      |    -     |   -    | FAIT   |
| Creer / modifier un utilisateur  |     oui     |  oui  |     -      |    -     |   -    | FAIT   |
| Desactiver un utilisateur        |     oui     |  oui  |     -      |    -     |   -    | FAIT   |
| **Mon profil**                   |             |       |            |          |        |        |
| Voir mon profil                  |     oui     |  oui  |    oui     |   oui    |  oui   | **A FAIRE** |
| Modifier mon mot de passe        |     oui     |  oui  |    oui     |   oui    |  oui   | **A FAIRE** |

### 1.3 Propriete des devis — A FAIRE

Le profil `COMMERCIAL` ne voit et ne modifie que **ses propres devis**. Cela implique :
- Un champ `created_by` (FK vers `users`) sur la table `customer_quotes` — **FAIT** (colonne existe)
- Un filtrage systematique cote API : `WHERE created_by = current_user.id` — **A FAIRE** (jamais implemente)
- Le profil `ADMIN` voit tous les devis de tous les commerciaux — **A FAIRE**

**Travail restant** :
- Ajouter `Depends(get_current_user)` a tous les endpoints `customer_quotes`
- Peupler `created_by` a la creation et `updated_by` a la modification
- Ajouter le filtrage par proprietaire pour le role COMMERCIAL

### 1.4 Flux d'Inscription "Self-Service" (VIEWER) — FAIT (partiel)

| Etape | Statut | Detail |
|-------|--------|--------|
| 1. Inscription (formulaire `/register`) | FAIT | `frontend/src/pages/Register.tsx` |
| 2. Validation domaine email | FAIT | `auth_service.py` — `ALLOWED_EMAIL_DOMAINS` |
| 3. Creation en attente (`is_active=False`, role `VIEWER`) | FAIT | |
| 4. Notification admin (email ou dashboard) | **A FAIRE** | Aucune notification |
| 5. Validation admin (dashboard + changement role) | **A FAIRE** | Pas de page admin Users.tsx |
| 6. Premiere connexion (force changement MDP) | **A FAIRE** | Flag `must_change_password` existe mais jamais verifie |

---

## 2. Modele de donnees

### 2.1 Nouvelle table `users` — FAIT

**Fichier** : `backend/app/models/user.py`

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'VIEWER',
    is_active BOOLEAN NOT NULL DEFAULT false,
    must_change_password BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

> **A AMELIORER** : `role` devrait etre un `Enum` PostgreSQL au lieu d'un `String` libre (voir section 13.3).

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

| Token             | Duree de vie | Stockage prevu            | Stockage reel                  | Statut |
| ----------------- | ------------ | ------------------------- | ------------------------------ | ------ |
| **Access token**  | 30 minutes   | `localStorage` (frontend) | `localStorage` (frontend)      | FAIT   |
| **Refresh token** | 7 jours      | `httpOnly cookie` + Redis | **`localStorage`** (pas cookie)| ECART  |

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

| Parametre                      | Propose              | Implemente              | Statut |
| ------------------------------ | -------------------- | ----------------------- | ------ |
| Algorithme de hashage          | bcrypt (passlib)     | bcrypt (passlib)        | FAIT   |
| Cout bcrypt (rounds)           | 12                   | defaut passlib          | FAIT   |
| Longueur minimale mot de passe | 8 caracteres         | **Aucune validation**   | A FAIRE |
| Complexite (maj, min, chiffre) | Oui                  | **Aucune validation**   | A FAIRE |

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

### 4.4 Dependency injection (`core/deps.py`) — FAIT (avec bugs)

**Fichier** : `backend/app/core/deps.py`

Implementes :
- `get_current_user()` : decode JWT + check blacklist Redis + check `is_active`
- `get_current_active_user()` : wrapper redondant (identique a `get_current_user`)
- `require_role(*roles)` : factory avec bypass SUPER_ADMIN

> **BUG SECURITE** : `get_current_user()` ne verifie pas que le token est un **access** token. Un refresh token peut authentifier des requetes. Voir section 13.1.

> **BUG** : Le check SUPER_ADMIN utilise `"SUPER_ADMIN" not in current_user.role` (substring match) au lieu de `current_user.role != "SUPER_ADMIN"`. Voir section 13.2.

### 4.5 Endpoints d'authentification (`api/auth.py`) — FAIT (avec bug)

**Fichier** : `backend/app/api/auth.py`

| Methode | Endpoint                   | Propose | Implemente | Statut |
| ------- | -------------------------- | :-----: | :--------: | :----: |
| `POST`  | `/api/v1/auth/login`       |   oui   |    oui     | FAIT   |
| `POST`  | `/api/v1/auth/refresh`     |   oui   |    oui     | FAIT   |
| `POST`  | `/api/v1/auth/logout`      |   oui   |    oui     | **BUG CRITIQUE** |
| `GET`   | `/api/v1/auth/me`          |   oui   |    oui     | FAIT   |
| `POST`  | `/api/v1/auth/register`    |   oui   |    oui     | FAIT   |
| `PUT`   | `/api/v1/auth/me/password` |   oui   |    non     | **A FAIRE** |

> **BUG CRITIQUE** : Le endpoint `/logout` (ligne 103) appelle `datetime.utcnow()` mais seul `timedelta` est importe. Provoque un `NameError` a chaque appel. Voir section 12.1.

### 4.6 Endpoints de gestion des utilisateurs (`api/users.py`) — FAIT

**Fichier** : `backend/app/api/users.py`

| Methode  | Endpoint              | Propose | Implemente | Statut |
| -------- | --------------------- | :-----: | :--------: | :----: |
| `GET`    | `/api/v1/users`       |   oui   |    oui     | FAIT   |
| `GET`    | `/api/v1/users/{id}`  |   oui   |    oui     | FAIT   |
| `PUT`    | `/api/v1/users/{id}`  |   oui   |    oui     | FAIT   |
| `DELETE` | `/api/v1/users/{id}`  |   oui   |    oui     | FAIT (hard delete) |
| `POST`   | `/api/v1/users`       |   oui   |    non     | **A FAIRE** |
| `GET`    | `/users/pending`      |   oui   |    non     | **A FAIRE** |
| `POST`   | `/users/{id}/approve` |   oui   |    non     | **A FAIRE** |

> **NOTE** : DELETE fait un `db.delete(user)` (hard delete) au lieu d'un soft delete (`is_active=False`). Le choix est acceptable mais les devis de cet utilisateur perdent leur reference `created_by`.

> **FAIT** : Protection contre l'escalade de privileges (un ADMIN ne peut pas attribuer SUPER_ADMIN, ni modifier un autre ADMIN).

### 4.7 Protection des routes existantes — PARTIEL

| Route                          | Methode  | Roles autorises              | Statut |
| ------------------------------ | -------- | ---------------------------- | :----: |
| `/partners`                    | GET      | Tous (authentifie)           | FAIT   |
| `/partners`                    | POST     | ADMIN, OPERATOR              | FAIT   |
| `/partners/{id}`               | PUT      | ADMIN, OPERATOR              | FAIT   |
| `/partners/{id}`               | DELETE   | ADMIN                        | FAIT   |
| `/quotes`                      | GET      | Tous (authentifie)           | FAIT   |
| `/quotes`                      | DELETE   | ADMIN, OPERATOR              | FAIT   |
| `/imports`                     | POST     | ADMIN, OPERATOR              | FAIT   |
| `/imports`                     | GET      | ADMIN, OPERATOR              | FAIT   |
| `/match`                       | POST     | Tous (authentifie)           | **A FAIRE** |
| `/customer-quotes`             | GET      | Tous (filtrage proprietaire) | **A FAIRE** |
| `/customer-quotes`             | POST     | ADMIN, COMMERCIAL            | **A FAIRE** |
| `/customer-quotes/{id}`        | PUT      | ADMIN, COMMERCIAL (proprio)  | **A FAIRE** |
| `/customer-quotes/{id}`        | DELETE   | ADMIN, COMMERCIAL (proprio)  | **A FAIRE** |
| `/customer-quotes/{id}/items`  | POST     | ADMIN, COMMERCIAL            | **A FAIRE** |
| `/customer-quotes/{id}/items`  | PUT      | ADMIN, COMMERCIAL            | **A FAIRE** |
| `/customer-quotes/{id}/items`  | DELETE   | ADMIN                        | **A FAIRE** |
| `/cities/suggest`              | GET      | Tous (authentifie)           | **A FAIRE** |
| `/auth/register`               | POST     | Public (validation domaine)  | FAIT   |
| `/users`                       | *        | ADMIN uniquement             | FAIT   |

---

## 5. Frontend : implementation

### 5.1 Nouvelles dependances — FAIT

- `jwt-decode@^4.0.0`
- `axios@^1.13.3`

### 5.2 Nouveaux fichiers — PARTIEL

```
frontend/src/
├── context/
│   └── AuthContext.tsx              FAIT
├── pages/
│   ├── Login.tsx                    FAIT
│   ├── Register.tsx                 FAIT
│   ├── Users.tsx                    A FAIRE
│   ├── Profile.tsx                  A FAIRE
│   └── ChangePasswordForce.tsx      A FAIRE
├── components/
│   ├── auth/
│   │   ├── ProtectedRoute.tsx       FAIT
│   │   └── RoleGate.tsx             FAIT (sous-utilise)
│   └── layout/
│       └── UserMenu.tsx             FAIT
├── services/
│   └── authService.ts              FAIT
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

### 5.6 Routing mis a jour (`App.tsx`) — FAIT (avec bug)

**Fichier** : `frontend/src/App.tsx`

Routes implementees :
- Publiques : `/login`, `/register`
- Protegees (tous auth) : `/`, `/search`, `/results`, `/quotes`, `/customer-quotes`, `/customer-quotes/:id`
- ADMIN + COMMERCIAL : `/customer-quotes/:id/edit`
- ADMIN + OPERATOR : `/partners`, `/imports`

Routes manquantes :
- `/users` (page admin gestion utilisateurs) — **A FAIRE**
- `/profile` (page profil utilisateur) — **A FAIRE**

> **BUG CRITIQUE** : Les lignes 1-13 dupliquent les imports des lignes 15-30. Erreur de compilation. Voir section 12.2.

### 5.7 Navigation conditionnelle (`Sidebar.tsx`) — A FAIRE

**Fichier** : `frontend/src/components/layout/Sidebar.tsx`

**PROBLEME** : Tous les liens de navigation sont affiches pour tous les utilisateurs, quel que soit leur role. Le composant `RoleGate` existe mais n'est **pas utilise** dans la sidebar.

**Travail restant** :
```tsx
<RoleGate allowedRoles={['ADMIN', 'OPERATOR']}>
    <SidebarLink to="/partners" icon={Users} label="Partenaires" />
    <SidebarLink to="/imports" icon={UploadCloud} label="Imports" />
</RoleGate>
<RoleGate allowedRoles={['ADMIN']}>
    <SidebarLink to="/users" icon={UserCog} label="Utilisateurs" />
</RoleGate>
```

### 5.8 Composant `RoleGate` — FAIT (sous-utilise)

**Fichier** : `frontend/src/components/auth/RoleGate.tsx`

Le composant fonctionne correctement mais n'est utilise **nulle part** dans les pages existantes. Il devrait etre utilise dans :
- `Sidebar.tsx` : filtrer les liens de navigation
- Pages avec actions conditionnelles (boutons supprimer, creer, etc.)

### 5.9 Page de connexion (`Login.tsx`) — FAIT

**Fichier** : `frontend/src/pages/Login.tsx`

Formulaire email/password avec gestion d'erreurs et redirection post-login.

### 5.10 Menu utilisateur (`UserMenu.tsx`) — FAIT

**Fichier** : `frontend/src/components/layout/UserMenu.tsx`

Avatar initiales, email, lien profil, bouton deconnexion.

> **BUG MINEUR** : Le lien "Mon profil" pointe vers `/profile` qui n'existe pas encore dans `App.tsx`.

### 5.11 Page d'Inscription (`Register.tsx`) — FAIT

**Fichier** : `frontend/src/pages/Register.tsx`

Formulaire (email, prenom, nom, mot de passe) avec message de succes indiquant la validation admin requise.

---

## 6. Interface Utilisateur (Propositions UI)

### 6.1 Page de Connexion & Inscription — FAIT

Login et Register implementes avec Tailwind CSS, gestion erreurs, loading state.

### 6.2 Dashboard Admin : Gestion des Utilisateurs — A FAIRE

**Fichier a creer** : `frontend/src/pages/Users.tsx`

Aucune page frontend pour la gestion des utilisateurs. L'API backend existe (`GET/PUT/DELETE /users/`) mais n'est pas exploitee.

**Travail restant** :

1. Creer `pages/Users.tsx` avec :
   - Tableau : Nom, Email, Role, Statut, Actions
   - Filtres par role et statut
   - Boutons : Modifier [M], Desactiver [D], Reactiver [R]
   - Badge "Demandes en attente" pour les comptes `is_active=false`
2. Modale "Nouvel utilisateur" (email, prenom, nom, role, MDP temporaire)
3. Modale "Modifier utilisateur" (infos + reinitialisation MDP)
4. Ajouter la route `/users` dans `App.tsx` avec `ProtectedRoute allowedRoles={['ADMIN']}`
5. Ajouter le lien dans la Sidebar (visible uniquement pour ADMIN)

### 6.3 Premiere Connexion (Changement MDP Force) — A FAIRE

**Fichier a creer** : `frontend/src/pages/ChangePasswordForce.tsx`

Si `must_change_password` est actif, l'utilisateur doit etre redirige vers un formulaire de changement de MDP avant d'acceder a l'application.

**Travail restant** :
- Backend : verifier `must_change_password` dans `get_current_user()` et retourner une 403 specifique
- Backend : creer endpoint `PUT /auth/me/password` (ancien MDP + nouveau MDP)
- Frontend : intercepter la 403 et rediriger vers le formulaire
- Frontend : creer la page `ChangePasswordForce.tsx`

---

## 7. Creation du premier administrateur (Script) — FAIT

**Fichier** : `backend/app/cli/create_admin.py`

```bash
python -m app.cli.create_admin --email admin@example.com --password MotDePasse123
```

Cree un utilisateur `ADMIN` (actif, `must_change_password=False`).

> **A AMELIORER** : Pas de moyen de creer un `SUPER_ADMIN`. Ajouter un argument `--role` au script.

---

## 8. Configuration Redis — FAIT

### 8.1 Connexion Redis (`core/redis.py`) — FAIT

**Fichier** : `backend/app/core/redis.py`

Client singleton `redis.Redis` avec `decode_responses=True`.

> **A AMELIORER** : Pas de gestion d'erreur si Redis est down. Voir section 14.6.

### 8.2 Utilisations prevues vs reelles

| Cle Redis                 | TTL         | Propose | Implemente | Statut |
| ------------------------- | ----------- | :-----: | :--------: | :----: |
| `blacklist:{jti}`         | ~30 min     |   oui   |    oui     | FAIT   |
| `refresh:{user_id}:{jti}` | 7 jours    |   oui   |    non     | A FAIRE |
| `login_attempts:{email}`  | 15 min      |   oui   |    non     | A FAIRE |

### 8.3 Rate limiting (protection brute force) — A FAIRE

Non implemente. Le code propose dans les propositions n'a pas ete integre.

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
- [ ] Endpoint `POST /users/{id}/approve` (admin validation)
- [ ] Middleware `must_change_password` (redirige vers change-password si true)
- [ ] **Proteger les endpoints `customer-quotes` (8 endpoints)**
- [ ] **Proteger les endpoints `match` et `cities`**
- [ ] Filtrage des devis par proprietaire (`created_by`) pour les commerciaux
- [x] Implementer `api/users.py` (CRUD admin)
- [ ] Alimenter `created_by`/`updated_by` sur `customer_quotes`
- [ ] Rate limiting Redis sur le login
- [ ] Endpoint `PUT /auth/me/password` (changement MDP self-service)

### Phase 3 — Frontend login et routing
- [x] Ajouter `jwt-decode` aux dependances
- [x] Creer `AuthContext.tsx`
- [x] Creer page `Login.tsx` et `Register.tsx`
- [ ] Creer page `ChangePasswordForce.tsx`
- [x] Configurer l'intercepteur Axios (token + refresh)
- [x] Creer `ProtectedRoute.tsx`
- [x] Mettre a jour `App.tsx` avec les routes protegees

### Phase 4 — Frontend UX
- [ ] **Navigation conditionnelle par role dans `Sidebar.tsx`**
- [x] Composant `RoleGate.tsx` (cree mais sous-utilise)
- [x] Menu utilisateur dans le header (`UserMenu.tsx`)
- [ ] **Page de gestion des utilisateurs (`Users.tsx`)**
- [ ] **Page "Mon profil" (`Profile.tsx`) avec changement de mot de passe**

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

| Code HTTP | Signification            | Action frontend                             | Statut |
| --------- | ------------------------ | ------------------------------------------- | :----: |
| 401       | Token invalide/expire    | Tenter refresh, sinon rediriger vers /login | FAIT   |
| 403       | Role insuffisant         | Afficher un message "Acces refuse"          | FAIT (ProtectedRoute redirige vers /) |
| 429       | Trop de tentatives login | Afficher "Reessayez dans X minutes"         | A FAIRE (rate limiting non implemente) |

---

## 12. Bugs critiques a corriger

### 12.1 BUG CRITIQUE : Endpoint `/logout` casse

**Fichier** : `backend/app/api/auth.py` (ligne 103)

```python
# ACTUEL (casse) :
from datetime import timedelta  # ligne 1 — seul import
...
ttl = exp - datetime.utcnow().timestamp()  # ligne 103 — NameError!
```

**Correction** :
```python
# Ajouter a la ligne 1 :
from datetime import datetime, timedelta
# Ou mieux, remplacer ligne 103 par :
import time
ttl = exp - time.time()
```

### 12.2 BUG CRITIQUE : Imports dupliques dans App.tsx

**Fichier** : `frontend/src/App.tsx` (lignes 1-13)

Les 13 premieres lignes sont des imports dupliques des lignes 15-30. Le fichier ne compile pas.

**Correction** : Supprimer les lignes 1 a 14 (bloc `import` + ligne vide).

---

## 13. Failles de securite a corriger

### 13.1 Validation du type de token — HAUTE

**Fichier** : `backend/app/core/deps.py`

`get_current_user()` ne verifie pas que le token est un access token. Un refresh token peut authentifier des requetes API.

**Correction** :
```python
# Apres decode du token, ajouter :
if payload.get("type") == "refresh":
    raise credentials_exception
```

### 13.2 Verification du role SUPER_ADMIN (substring match) — MOYENNE

**Fichier** : `backend/app/core/deps.py` (ligne 65)

```python
# ACTUEL (incorrect — substring match) :
if current_user.role not in allowed_roles and "SUPER_ADMIN" not in current_user.role:

# CORRECTION (comparaison stricte) :
if current_user.role not in allowed_roles and current_user.role != "SUPER_ADMIN":
```

### 13.3 Role en String libre en base — MOYENNE

**Fichier** : `backend/app/models/user.py`

Le role est un `String` sans contrainte DB. Toute valeur peut etre stockee.

**Correction recommandee** :
```python
import enum
from sqlalchemy import Enum as SAEnum

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    COMMERCIAL = "COMMERCIAL"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"

role = Column(SAEnum(UserRole), default=UserRole.VIEWER, nullable=False)
```

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
     │  {email, password}            │                             │              │
     │──────────────────────────────>│                             │              │
     │                               │                             │              │
     │                               │  SELECT * FROM users        │              │
     │                               │  WHERE email = ?            │              │
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
     │  {email, first_name,          │                             │
     │   last_name, role, password}  │                             │
     │──────────────────────────────>│                             │
     │                               │                             │
     │                               │  Verifier JWT + role ADMIN  │
     │                               │  Valider email/password     │
     │                               │  Check email doublon        │
     │                               │────────────────────────────>│
     │                               │                             │
     │                               │  INSERT INTO users          │
     │                               │  (is_active=true)           │
     │                               │────────────────────────────>│
     │                               │                             │
     │  <── 201 Created ────────────│                             │
```

**Statut** : Backend FAIT via `auth_service.create_user()` — Frontend Users.tsx A FAIRE

### 15.3 Desactivation d'un utilisateur

```
┌──────────┐                    ┌──────────┐           ┌──────────┐    ┌───────┐
│ Frontend │                    │ API      │           │ PostgreSQL│    │ Redis │
│ Users.tsx│                    │ users.py │           │ users    │    │       │
└────┬─────┘                    └────┬─────┘           └────┬─────┘    └───┬───┘
     │                               │                      │              │
     │  DELETE /users/{user_id}      │                      │              │
     │──────────────────────────────>│                      │              │
     │                               │                      │              │
     │                               │  Verifier != soi-meme│              │
     │                               │  Verifier privileges │              │
     │                               │                      │              │
     │                               │  db.delete(user)     │              │
     │                               │─────────────────────>│              │
     │                               │                      │              │
     │  <── 200 OK ────────────────  │                      │              │
```

**Statut** : Backend FAIT (hard delete) — Frontend Users.tsx A FAIRE

> **NOTE** : L'implementation actuelle fait un hard delete au lieu du soft delete (`is_active=false`) propose dans les diagrammes. L'invalidation des tokens Redis n'est pas faite au delete.

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

**Statut** : A FAIRE (endpoint + page Profile.tsx)

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

**Statut** : BUG CRITIQUE — endpoint casse (import `datetime` manquant). Voir section 12.1.

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

| Fichier                                           | Propose | Implemente | Statut |
| ------------------------------------------------- | :-----: | :--------: | :----: |
| `backend/app/models/user.py`                      |   oui   |    oui     | FAIT   |
| `backend/app/schemas/auth.py`                     |   oui   |    oui     | FAIT   |
| `backend/app/services/auth_service.py`            |   oui   |    oui     | FAIT   |
| `backend/app/api/auth.py`                         |   oui   |    oui     | FAIT (bug logout) |
| `backend/app/api/users.py`                        |   oui   |    oui     | FAIT   |
| `backend/app/core/security.py`                    |   oui   |    oui     | FAIT   |
| `backend/app/core/redis.py`                       |   oui   |    oui     | FAIT   |
| `backend/app/core/deps.py`                        |   oui   |    oui     | FAIT (bugs) |
| `backend/app/cli/create_admin.py`                 |   oui   |    oui     | FAIT   |
| `backend/alembic/versions/xxx_add_users.py`       |   oui   |    oui     | FAIT (bug downgrade) |
| `frontend/src/context/AuthContext.tsx`            |   oui   |    oui     | FAIT   |
| `frontend/src/pages/Login.tsx`                    |   oui   |    oui     | FAIT   |
| `frontend/src/pages/Register.tsx`                 |   oui   |    oui     | FAIT   |
| `frontend/src/pages/Users.tsx`                    |   oui   |    non     | **A FAIRE** |
| `frontend/src/pages/Profile.tsx`                  |   oui   |    non     | **A FAIRE** |
| `frontend/src/pages/ChangePasswordForce.tsx`      |   oui   |    non     | **A FAIRE** |
| `frontend/src/components/auth/ProtectedRoute.tsx` |   oui   |    oui     | FAIT   |
| `frontend/src/components/auth/RoleGate.tsx`       |   oui   |    oui     | FAIT   |
| `frontend/src/components/layout/UserMenu.tsx`     |   oui   |    oui     | FAIT   |
| `frontend/src/services/authService.ts`            |   oui   |    oui     | FAIT   |
| `frontend/src/types/auth.ts`                      |   oui   |    oui     | FAIT   |

### Fichiers modifies

| Fichier                                     | Modification                                 | Statut |
| ------------------------------------------- | -------------------------------------------- | :----: |
| `backend/requirements.txt`                  | +5 dependances auth                          | FAIT   |
| `backend/app/main.py`                       | Enregistrer routers auth/users               | FAIT   |
| `backend/app/api/__init__.py`               | Ajouter les routers auth et users            | FAIT   |
| `backend/app/core/config.py`                | Settings JWT + Redis + email domains         | FAIT   |
| `backend/app/api/partners.py`               | `Depends(require_role(...))`                 | FAIT   |
| `backend/app/api/quotes.py`                 | `Depends(require_role(...))`                 | FAIT   |
| `backend/app/api/imports.py`                | `Depends(require_role(...))`                 | FAIT   |
| `backend/app/api/matching.py`               | `Depends(get_current_user)`                  | **A FAIRE** |
| `backend/app/api/customer_quotes.py`        | Auth + filtrage par proprietaire             | **A FAIRE** |
| `backend/app/api/cities.py`                 | `Depends(get_current_user)`                  | **A FAIRE** |
| `backend/app/models/customer_quote.py`      | Colonnes `created_by`, `updated_by`          | FAIT (colonnes) / A FAIRE (alimentation) |
| `frontend/package.json`                     | +2 dependances (jwt-decode, axios)           | FAIT   |
| `frontend/src/App.tsx`                      | Routes protegees, route /login               | FAIT (bug imports dupliques) |
| `frontend/src/services/api.ts`              | Intercepteurs auth (token, refresh)          | FAIT   |
| `frontend/src/components/layout/Sidebar.tsx`| Navigation conditionnelle par role           | **A FAIRE** |

---

## 17. Recapitulatif des travaux restants par priorite

### Priorite 1 — Bugs critiques (bloquants)

| # | Tache | Fichier | Section |
|---|-------|---------|---------|
| 1 | Corriger import `datetime` dans `/logout` | `backend/app/api/auth.py` | 12.1 |
| 2 | Supprimer imports dupliques dans `App.tsx` | `frontend/src/App.tsx` | 12.2 |

### Priorite 2 — Failles de securite

| # | Tache | Fichier | Section |
|---|-------|---------|---------|
| 3 | Validation type token (access vs refresh) dans `get_current_user` | `backend/app/core/deps.py` | 13.1 |
| 4 | Proteger les 8 endpoints `customer-quotes` | `backend/app/api/customer_quotes.py` | 4.7 |
| 5 | Proteger les endpoints `match` et `cities` | `backend/app/api/matching.py`, `cities.py` | 4.7 |
| 6 | Corriger substring match SUPER_ADMIN | `backend/app/core/deps.py` | 13.2 |
| 7 | Enum DB pour les roles (+ migration) | `backend/app/models/user.py` | 13.3 |
| 8 | Rotation du refresh token | `backend/app/api/auth.py` | 13.4 |

### Priorite 3 — Fonctionnalites manquantes

| # | Tache | Fichier(s) | Section |
|---|-------|------------|---------|
| 9 | Page admin gestion utilisateurs | `frontend/src/pages/Users.tsx` + route App.tsx | 6.2 |
| 10 | Filtrage Sidebar par role avec RoleGate | `frontend/src/components/layout/Sidebar.tsx` | 5.7 |
| 11 | Page profil + endpoint changement MDP | `frontend/src/pages/Profile.tsx` + `PUT /auth/me/password` | 6.3 |
| 12 | Alimenter `created_by`/`updated_by` sur devis | `backend/app/api/customer_quotes.py` | 1.3 |
| 13 | Filtrage devis par proprietaire (COMMERCIAL) | `backend/app/api/customer_quotes.py` | 1.3 |
| 14 | Enforcement `must_change_password` | Backend deps + frontend | 6.3 |
| 15 | CLI creation SUPER_ADMIN (argument `--role`) | `backend/app/cli/create_admin.py` | 7 |

### Priorite 4 — Qualite et Phase 2

| # | Tache | Section |
|---|-------|---------|
| 16 | Remplacement `datetime.utcnow()` partout | 13.5 |
| 17 | Suppression `oauth2_scheme` duplique | 14.1 |
| 18 | Refresh token en body (pas query param) | 14.3 |
| 19 | Mutex refresh dans Axios interceptor | 14.4 |
| 20 | Validation domaine email case-insensitive | 14.5 |
| 21 | Gestion erreur Redis (fallback) | 14.6 |
| 22 | Correction downgrade Alembic (nommer FK) | 14.7 |
| 23 | Validation complexite mot de passe | 3.5 |
| 24 | Rate limiting sur login | 8.3 |
| 25 | Audit logging complet | 2.3 |
| 26 | Tests unitaires + integration auth | 10 Phase 5 |
