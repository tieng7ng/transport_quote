# Plan d'Implémentation - Évolutions Authentification (Matrice 1.2 & Correctifs)

> **Source** : Basé sur la section 17 de `PROPOSITIONS_MODULE_AUTHENTIFICATION.md`.
> **Objectif** : Aligner strictement les rôles sur la Matrice 1.2 et corriger les bugs techniques.

## 1. Priorité 1 : Alignement des Rôles (Backend & Frontend)

L'objectif est de restreindre ou d'ouvrir les accès conformément à la matrice de sécurité validée.

### 1.1 Backend : Restrictions API (`require_role`)

#### [MODIFY] `backend/app/api/partners.py`
- [x] **POST /** et **PUT /{id}** : Restreindre à `SUPER_ADMIN` uniquement (Retirer `ADMIN`, `OPERATOR`).
- [x] **DELETE /{id}** : Restreindre à `SUPER_ADMIN` uniquement (Retirer `ADMIN`).
- [x] **DELETE /{id}/quotes** : Restreindre à `SUPER_ADMIN` uniquement (Retirer `ADMIN`).

#### [MODIFY] `backend/app/api/imports.py`
- [x] **POST /** et **GET /{id}** : Restreindre à `SUPER_ADMIN` uniquement (Retirer `ADMIN`, `OPERATOR`).

#### [MODIFY] `backend/app/api/quotes.py`
- [x] **DELETE /** : Restreindre à `SUPER_ADMIN` uniquement (Retirer `ADMIN`, `OPERATOR`).
- [x] **POST /** : Admin/Operator (Status Quo).

#### [MODIFY] `backend/app/api/customer_quotes.py`
- [x] **DELETE /{id}/items** : Ajouter `COMMERCIAL` aux rôles autorisés (Actuellement `ADMIN` uniquement).

### 1.2 Frontend : Routing et Navigation

#### [MODIFY] `frontend/src/App.tsx`
- [x] **Route `/partners`** : Ouvrir à tous les utilisateurs authentifiés (Retirer restriction `ADMIN`, `OPERATOR`).
- [x] **Route `/imports`** : Restreindre à `SUPER_ADMIN` uniquement.
- [x] **Route `/customer-quotes/:id/edit`** : Ajouter `OPERATOR` aux rôles autorisés.

#### [MODIFY] `frontend/src/components/layout/Sidebar.tsx`
- [x] **Menu Partenaires** : Sortir du `RoleGate` (visible pour tous).
- [x] **Menu Imports** : Mettre dans un `RoleGate` exclusif `SUPER_ADMIN`.

## 2. Priorité 2 : Améliorations Techniques & Bugs

### 2.1 Backend

#### [MODIFY] `backend/app/api/users.py`
- [x] **Nettoyage** : Supprimer les imports dupliqués et la double déclaration de `router`.
- [x] **Sécurité** : Lors du `PATCH /status` (désactivation), invalider les tokens via Redis.

#### [MODIFY] `backend/app/core/security.py` & `auth_service.py`
- [x] **Datetime** : Remplacer `datetime.utcnow()` (déprécié) par `datetime.now(timezone.utc)`.

### 2.2 Frontend

#### [MODIFY] `frontend/src/services/api.ts`
- [x] **Mutex Refresh** : Implémenter un système de verrou pour éviter les appels multiples à `/refresh` lors de 401 simultanés.

## 3. Plan de Vérification

### 3.1 Script de Vérification Automatisé (`verify_role_alignment.py`)
Un nouveau script Python sera créé pour tester spécifiquement les restrictions modifiées :
1.  Vérifier qu'un `ADMIN` obtient **403 Forbidden** sur `DELETE /partners/{id}`.
2.  Vérifier qu'un `ADMIN` obtient **403 Forbidden** sur `POST /imports`.
3.  Vérifier qu'un `COMMERCIAL` obtient **200 OK** sur `DELETE /customer-quotes/{id}/items`.
4.  Vérifier qu'un `VIEWER` obtient **200 OK** sur `GET /partners`.

### 3.2 Vérification Manuelle Frontend
1.  Se connecter en `VIEWER` : Vérifier accès à la page Partenaires (Lecture seule).
2.  Se connecter en `ADMIN` : Vérifier *absence* du menu Imports.
3.  Se connecter en `SUPER_ADMIN` : Vérifier présence du menu Imports et accès complet.
