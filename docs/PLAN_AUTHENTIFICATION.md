# Plan d'Implémentation - Authentification JWT (Audit Remédiation)

## Objectif
Implémenter une authentification sécurisée par Tokens JWT (JSON Web Tokens) pour protéger les endpoints de l'API, conformément aux points bloquants de l'audit.

## Changements Requis

### 1. Dépendances `requirements.txt`
- Ajouter `python-jose[cryptography]` : Pour la gestion des JWT.
- Ajouter `passlib[bcrypt]` : Pour le hachage des mots de passe.
- Ajouter `python-multipart` : Pour le support de `OAuth2PasswordRequestForm` (login form-data).

### 2. Modèle de Données (Base de données)
- Création du modèle SQLAlchemy `User` dans `backend/app/models/user.py`.
- Champs : `id`, `email` (unique, index), `hashed_password`, `is_active`, `is_superuser`.
- Migration Alembic pour créer la table `users`.

### 3. Utilitaires de Sécurité
- Création de `backend/app/core/security.py`.
- Fonctions :
    - `verify_password(plain_password, hashed_password)`
    - `get_password_hash(password)`
    - `create_access_token(data: dict, expires_delta)`

### 4. API et Dépendances
- Création de `backend/app/api/deps.py` :
    - Dépendance `get_current_user` qui valide le token dans le header `Authorization: Bearer ...`.
    - Dépendance `get_current_active_user` qui vérifie si l'utilisateur est actif.
- Création de `backend/app/api/auth.py` :
    - Endpoint `POST /login/access-token` : Vérifie email/password et retourne un token d'accès.

### 5. Protection des Routes
- Modification de `backend/app/api/imports.py` (et autres endpoints sensibles).
- Injection de `Depends(get_current_active_user)` dans les fonctions de route pour bloquer l'accès anonyme.

## Plan de Vérification
1.  **Build** : Reconstruire le container backend pour installer les nouvelles libs.
2.  **Migration** : Appliquer la migration `users`.
3.  **Seed** : Créer un utilisateur admin initial (ex: `admin@transport-quote.com`).
4.  **Test API** :
    - Appel non authentifié sur `/api/v1/imports/` -> Doit retourner **401 Unauthorized**.
    - Login sur `/api/v1/login/access-token` -> Doit retourner un **Token JWT**.
    - Appel authentifié sur `/api/v1/imports/` avec le Token -> Doit retourner **200 OK**.
