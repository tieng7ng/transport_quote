# Plan de Finalisation — Module Authentification

> **Date** : 11 Février 2026
> **Statut** : ~95% implémenté. Ce plan remplace l'ancien qui couvrait 8 sprints désormais réalisés.

---

## 1. Contexte et État des Lieux

L'implémentation du module d'authentification a considérablement avancé. Les fonctionnalités suivantes sont **DÉJÀ IMPLÉMENTÉES** :

-   **Backend** : Auth (`login`, `register`, `logout`), Gestion utilisateurs (`CRUD`), Protection des routes (`customer-quotes`, `users`, `match`), Enum `UserRole`.
-   **Frontend** : Pages Login/Register (avec champ `login`), Gestion des utilisateurs (`Users.tsx`), Profil (`Profile.tsx`), Protection des routes (`RoleGate`).
-   **Sécurité** : Fix du `/logout`, validation token, protection contre l'escalade de privilèges.

---

## 2. Reste à Faire : Sprint de Finalisation

### Priorité 1 : Validation & Recette (Validation Fonctionnelle)

L'objectif est de vérifier que le code implémenté se comporte comme attendu dans des scénarios réels.

- [ ] **Flux Nouvel Utilisateur**
    - Créer un compte employé via `/register`.
    - Vérifier qu'il est créé en statut "Inactif" et rôle "VIEWER" (ou standard).
    - Activer le compte via l'interface Admin.
    - Se connecter avec le nouveau compte.
    - Vérifier que le changement de mot de passe est forcé à la première connexion.

- [ ] **Permissions et Cloisonnement des Données**
    - **COMMERCIAL** : Vérifier qu'il ne voit QUE les devis qu'il a créés (`/customer-quotes`).
    - **OPERATOR** : Vérifier qu'il voit tous les devis mais ne peut pas supprimer ceux des autres.
    - **ADMIN** : Vérifier qu'il peut tout gérer mais NE PEUT PAS se donner le rôle `SUPER_ADMIN` ni rétrograder un `SUPER_ADMIN`.

- [ ] **Changement de Mot de Passe**
    - Tester le changement de mot de passe via la page Profil.
    - Vérifier que l'ancien mot de passe n'est plus valide.

### Priorité 2 : Améliorations Techniques (Sprints 8 & Qualité)

Ces tâches techniques sont nécessaires pour la robustesse en production.

- [ ] **Mutex pour le Refresh Token** (Frontend)
    -   *Problème* : Si plusieurs requêtes échouent (401) en même temps, le frontend lance plusieurs appels `/refresh` parallèles.
    -   *Solution* : Implémenter un système de file d'attente (mutex) dans `api.ts` pour ne faire qu'un seul refresh.

- [ ] **Rate Limiting sur Login** (Backend)
    -   *Objectif* : Protéger contre le brute-force.
    -   *Moyen* : Utiliser Redis pour limiter à 5 tentatives échouées par 15 minutes par IP/Login.

- [ ] **Audit Logs** (Backend)
    -   *Objectif* : Traçabilité des actions sensibles.
    -   *Actions à logger* : `USER_CREATE`, `USER_DELETE`, `QUOTE_DELETE`, `ROLE_CHANGE`.

### Priorité 3 : Nettoyage de Code

- [ ] **Vérification des Imports** : S'assurer qu'il n'y a plus d'imports dupliqués (comme celui corrigé dans `App.tsx`).
- [ ] **Suppression de Code Mort** : Nettoyer les anciennes routes ou fonctions non utilisées si identifiées.
