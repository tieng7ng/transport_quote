# Plan de tests fonctionnels — Backend API

Les tests fonctionnels testent les **endpoints HTTP complets** via `TestClient` FastAPI.
Ils utilisent une base de données de test avec rollback entre chaque test (voir `conftest.py`).

Commande d'exécution :
```bash
docker compose run --rm backend pytest app/tests/api/ -v
```

---

## Fixtures communes (`conftest.py`)

Les helpers suivants sont disponibles ou à créer dans `utils.py` :

```python
create_test_user(db, role="COMMERCIAL")  # crée un utilisateur actif
get_token(client, login, password)        # retourne un Bearer token
auth_headers(token)                       # {"Authorization": "Bearer <token>"}
```

---

## 1. Authentification — `api/auth.py`

Fichier cible : `app/tests/api/test_auth.py` *(existant — à compléter)*

| #    | Test                                              | Méthode / URL                    | Attendu                                  |
| ---- | ------------------------------------------------- | -------------------------------- | ---------------------------------------- |
| 1.1  | Login valide                                      | `POST /auth/login`               | `200` + `access_token` + `refresh_token` |
| 1.2  | Login — mauvais mot de passe                      | `POST /auth/login`               | `401`                                    |
| 1.3  | Login — login inexistant                          | `POST /auth/login`               | `401`                                    |
| 1.4  | Login — compte inactif                            | `POST /auth/login`               | `401`                                    |
| 1.5  | Logout avec token valide                          | `POST /auth/logout`              | `200`                                    |
| 1.6  | Logout — token blacklisté ensuite                 | `GET /auth/me` après logout      | `401`                                    |
| 1.7  | Refresh token valide                              | `POST /auth/refresh`             | `200` + nouveau `access_token`           |
| 1.8  | Refresh token invalide                            | `POST /auth/refresh`             | `401`                                    |
| 1.9  | Changement de mot de passe valide                 | `POST /auth/change-password`     | `200`                                    |
| 1.10 | Changement de mot de passe — ancien MDP incorrect | `POST /auth/change-password`     | `400`                                    |
| 1.11 | Route protégée sans token                         | `GET /auth/me`                   | `401`                                    |
| 1.12 | Login crée un log `auth.login_success`            | `POST /auth/login`               | 1 ligne dans `user_activity_logs`        |
| 1.13 | Login échoué crée un log `auth.login_failed`      | `POST /auth/login` (mauvais MDP) | 1 ligne dans `user_activity_logs`        |

---

## 2. Utilisateurs — `api/users.py`

Fichier cible : `app/tests/api/test_users.py`

| #   | Test                                      | Méthode / URL            | Attendu                  |
| --- | ----------------------------------------- | ------------------------ | ------------------------ |
| 2.1 | Liste des utilisateurs — ADMIN            | `GET /users`             | `200` + liste            |
| 2.2 | Liste des utilisateurs — COMMERCIAL       | `GET /users`             | `403`                    |
| 2.3 | Créer un utilisateur — ADMIN              | `POST /users`            | `201` + utilisateur créé |
| 2.4 | Créer un utilisateur — COMMERCIAL         | `POST /users`            | `403`                    |
| 2.5 | Créer avec login existant                 | `POST /users`            | `400`                    |
| 2.6 | Modifier un utilisateur — ADMIN           | `PUT /users/{id}`        | `200`                    |
| 2.7 | Désactiver un utilisateur — ADMIN         | `DELETE /users/{id}`     | `200`                    |
| 2.8 | Se désactiver soi-même                    | `DELETE /users/{own_id}` | `400` (auto-protection)  |
| 2.9 | Création loguée dans `user_activity_logs` | `POST /users`            | action `user.created`    |

---

## 3. Partenaires — `api/partners.py`

Fichier cible : `app/tests/api/test_partners.py` *(existant — à compléter)*

| #   | Test                                      | Méthode / URL                   | Attendu                  |
| --- | ----------------------------------------- | ------------------------------- | ------------------------ |
| 3.1 | Liste des partenaires — authentifié       | `GET /partners`                 | `200` + liste            |
| 3.2 | Liste des partenaires — non authentifié   | `GET /partners`                 | `401`                    |
| 3.3 | Créer un partenaire — ADMIN               | `POST /partners`                | `201`                    |
| 3.4 | Créer un partenaire — OPERATOR            | `POST /partners`                | `403`                    |
| 3.5 | Modifier un partenaire — ADMIN            | `PUT /partners/{id}`            | `200`                    |
| 3.6 | Partenaire inexistant                     | `GET /partners/uuid-inexistant` | `404`                    |
| 3.7 | Création loguée dans `user_activity_logs` | `POST /partners`                | action `partner.created` |

---

## 4. Recherche / Matching — `api/matching.py`

Fichier cible : `app/tests/api/test_matching.py`

| #   | Test                                     | Méthode / URL                                 | Attendu                                |
| --- | ---------------------------------------- | --------------------------------------------- | -------------------------------------- |
| 4.1 | Recherche valide avec résultats          | `POST /matching/search`                       | `200` + liste non vide                 |
| 4.2 | Recherche sans résultat                  | `POST /matching/search` (critères sans match) | `200` + liste vide                     |
| 4.3 | Recherche non authentifiée               | `POST /matching/search`                       | `401`                                  |
| 4.4 | Critères invalides (poids négatif)       | `POST /matching/search`                       | `422`                                  |
| 4.5 | Recherche crée un log `search.performed` | `POST /matching/search`                       | 1 ligne dans `user_activity_logs`      |
| 4.6 | Le log contient `results_count` correct  | `POST /matching/search`                       | `details.results_count` = nb résultats |

---

## 5. Devis clients — `api/customer_quotes.py`

Fichier cible : `app/tests/api/test_customer_quotes.py`

| #    | Test                                          | Méthode / URL                        | Attendu                                                                                                 |
| ---- | --------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| 5.1  | Créer un devis — COMMERCIAL                   | `POST /customer-quotes`              | `201`                                                                                                   |
| 5.2  | Créer un devis — VIEWER                       | `POST /customer-quotes`              | `403`                                                                                                   |
| 5.3  | Lister les devis                              | `GET /customer-quotes`               | `200` + liste paginée                                                                                   |
| 5.4  | Détail d'un devis                             | `GET /customer-quotes/{id}`          | `200`                                                                                                   |
| 5.5  | Devis d'un autre utilisateur — COMMERCIAL     | `GET /customer-quotes/{id}`          | `403` ou filtrage                                                                                       |
| 5.6  | Modifier un devis en DRAFT                    | `PUT /customer-quotes/{id}`          | `200`                                                                                                   |
| 5.7  | Modifier un devis en SENT                     | `PUT /customer-quotes/{id}`          | `400` (statut bloquant) ⚠️ *[Non implémenté — machine à états à coder dans `customer_quote_service.py`]* |
| 5.8  | Changer statut DRAFT → READY                  | `PATCH /customer-quotes/{id}/status` | `200`                                                                                                   |
| 5.9  | Changer statut READY → DRAFT (retour arrière) | `PATCH /customer-quotes/{id}/status` | `400` ⚠️ *[Non implémenté — transitions valides à définir]*                                              |
| 5.10 | Supprimer un devis en DRAFT                   | `DELETE /customer-quotes/{id}`       | `200`                                                                                                   |
| 5.11 | Supprimer un devis en SENT                    | `DELETE /customer-quotes/{id}`       | `400`                                                                                                   |
| 5.12 | Création loguée                               | `POST /customer-quotes`              | action `quote.created`                                                                                  |
| 5.13 | Changement de statut logué                    | `PATCH /customer-quotes/{id}/status` | action `quote.status_changed` avec `previous_status` et `new_status`                                    |

---

## 6. Imports — `api/imports.py`

Fichier cible : `app/tests/api/test_imports.py`

| #   | Test                                | Méthode / URL       | Attendu                 |
| --- | ----------------------------------- | ------------------- | ----------------------- |
| 6.1 | Upload CSV valide — SUPER_ADMIN     | `POST /imports`     | `202` + `import_job_id` |
| 6.2 | Upload CSV valide — COMMERCIAL      | `POST /imports`     | `403`                   |
| 6.3 | Upload extension interdite (`.exe`) | `POST /imports`     | `400`                   |
| 6.4 | Lister les imports                  | `GET /imports`      | `200` + liste           |
| 6.5 | Détail d'un import                  | `GET /imports/{id}` | `200` + statut          |
| 6.6 | Démarrage d'import logué            | `POST /imports`     | action `import.started` |

---

## 7. Historique des activités — `api/activity_logs.py`

Fichier cible : `app/tests/api/test_activity_logs.py`

| #   | Test                        | Méthode / URL                                               | Attendu                                          |
| --- | --------------------------- | ----------------------------------------------------------- | ------------------------------------------------ |
| 7.1 | Liste des logs — ADMIN      | `GET /activity-logs`                                        | `200` + liste paginée                            |
| 7.2 | Liste des logs — COMMERCIAL | `GET /activity-logs`                                        | `403`                                            |
| 7.3 | Filtre par utilisateur      | `GET /activity-logs?user_login=...`                         | Logs de cet utilisateur uniquement               |
| 7.4 | Filtre par action           | `GET /activity-logs?action=search.performed`                | Logs de type recherche uniquement                |
| 7.5 | Filtre par date             | `GET /activity-logs?from=2026-01-01&to=2026-01-31`          | Logs dans la période                             |
| 7.6 | Pagination                  | `GET /activity-logs?page=2&page_size=10`                    | Page 2 des résultats                             |
| 7.7 | Export CSV                  | `GET /activity-logs/export?format=csv`                      | `200` + `Content-Type: text/csv`                 |
| 7.8 | Export PDF                  | ~~`GET /activity-logs/export?format=pdf`~~                  | ⚠️ *[Non implémenté — uniquement CSV disponible]* |
| 7.9 | Export avec filtres         | `GET /activity-logs/export?format=csv&action=quote.created` | CSV filtré                                       |

---

## 8. Statistiques — `api/stats.py`

Fichier cible : `app/tests/api/test_stats.py`

| #   | Test                  | Méthode / URL                                       | Attendu                              |
| --- | --------------------- | --------------------------------------------------- | ------------------------------------ |
| 8.1 | Overview — ADMIN      | `GET /stats/overview`                               | `200` + KPIs avec structure attendue |
| 8.2 | Overview — COMMERCIAL | `GET /stats/overview`                               | `403`                                |
| 8.3 | Overview avec période | `GET /stats/overview?from=2026-01-01&to=2026-01-31` | `200`                                |
| 8.4 | Activité journalière  | `GET /stats/activity`                               | `200` + liste de jours               |
| 8.5 | Stats recherches      | `GET /stats/searches`                               | `200` + top routes                   |
| 8.6 | Stats devis           | `GET /stats/quotes`                                 | `200` + entonnoir de conversion      |
| 8.7 | Stats imports         | `GET /stats/imports`                                | `200`                                |
| 8.8 | Stats sécurité        | `GET /stats/security`                               | `200`                                |

---

## 9. Alertes de sécurité — `api/alerts.py`

Fichier cible : `app/tests/api/test_alerts.py`

| #   | Test                           | Méthode / URL                                                          | Attendu                                   |
| --- | ------------------------------ | ---------------------------------------------------------------------- | ----------------------------------------- |
| 9.1 | Liste des alertes — ADMIN      | `GET /alerts`                                                          | `200` + liste                             |
| 9.2 | Liste des alertes — COMMERCIAL | `GET /alerts`                                                          | `403`                                     |
| 9.3 | Marquer comme lu               | `PATCH /alerts/{id}/seen`                                              | `200` + `seen_at` renseigné               |
| 9.4 | Résoudre — désactivation       | `PATCH /alerts/{id}/resolve` body `{"resolution": "account_disabled"}` | `200` + `resolved_at` + `resolved_by`     |
| 9.5 | Résoudre — ignorer             | `PATCH /alerts/{id}/resolve` body `{"resolution": "ignored"}`          | `200`                                     |
| 9.6 | Alerte inexistante             | `PATCH /alerts/uuid-inexistant/seen`                                   | `404`                                     |
| 9.7 | SSE stream — connexion         | `GET /alerts/stream`                                                   | `200` + `Content-Type: text/event-stream` |
