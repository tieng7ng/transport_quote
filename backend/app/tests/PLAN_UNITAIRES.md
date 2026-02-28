# Plan de tests unitaires — Backend

Les tests unitaires testent chaque fonction/service **en isolation**, avec la base de données mockée ou en mémoire.
Ils s'appuient sur les fixtures de `conftest.py` (session en transaction rollback).

Commande d'exécution :
```bash
docker compose run --rm backend pytest app/tests/unit/ -v
```

---

## 1. `core/security.py`

Fichier cible : `app/tests/unit/test_security.py`

| #   | Test                                              | Comportement attendu                                 |
| --- | ------------------------------------------------- | ---------------------------------------------------- |
| 1.1 | `hash_password("motdepasse")`                     | Retourne un hash bcrypt valide (commence par `$2b$`) |
| 1.2 | `verify_password("motdepasse", hash)`             | Retourne `True` si mot de passe correct              |
| 1.3 | `verify_password("mauvais", hash)`                | Retourne `False`                                     |
| 1.4 | `create_access_token({"sub": user_id})`           | Retourne un JWT décodable contenant `sub` et `exp`   |
| 1.5 | `create_access_token(...)` avec expiration custom | `exp` = now + delta fourni                           |
| 1.6 | `decode_token(token_valide)`                      | Retourne le payload sans erreur                      |
| 1.7 | `decode_token(token_expiré)`                      | Lève une exception                                   |
| 1.8 | `decode_token("token_invalide")`                  | Lève une exception                                   |

---

## 2. `services/auth_service.py`

Fichier cible : `app/tests/unit/test_auth_service.py`

| #   | Test                                         | Comportement attendu                                                                                             |
| --- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 2.1 | `authenticate_user()` — login correct        | Retourne l'objet `User`                                                                                          |
| 2.2 | `authenticate_user()` — mauvais mot de passe | Retourne `None`                                                                                                  |
| 2.3 | `authenticate_user()` — login inexistant     | Retourne `None` (sans timing attack)                                                                             |
| 2.4 | `create_user()` — données valides            | Crée l'utilisateur avec `must_change_password=True` (vérifier si `is_active` est True ou False selon le service) |
| 2.5 | `create_user()` — email déjà utilisé         | Lève `HTTPException(400)`                                                                                        |
| 2.6 | `create_user()` — login déjà utilisé         | Lève `HTTPException(400)`                                                                                        |
| 2.7 | `create_user()` — domaine email non autorisé | Lève `HTTPException(400)` si domaines restreints                                                                 |
| 2.8 | `update_last_login()`                        | Met à jour `last_login_at` en base                                                                               |

---

## 3. `services/activity_service.py`

Fichier cible : `app/tests/unit/test_activity_service.py`

| #   | Test                                                             | Comportement attendu                                          |
| --- | ---------------------------------------------------------------- | ------------------------------------------------------------- |
| 3.1 | `log_activity(db, "search.performed", user=user, details={...})` | Insère 1 ligne dans `user_activity_logs` avec les bons champs |
| 3.2 | `log_activity()` sans utilisateur (login échoué)                 | Insère avec `user_id=None`, `user_login=None`                 |
| 3.3 | `log_activity()` avec `request` contenant `X-Forwarded-For`      | `ip_address` = première IP du header                          |
| 3.4 | `log_activity()` sans `request`                                  | `ip_address = None`                                           |
| 3.5 | `log_activity()` ne commit pas                                   | La session n'est pas commitée dans la fonction                |
| 3.6 | `purge_old_logs(db)`                                             | Supprime les lignes de plus d'1 an, conserve les récentes     |
| 3.7 | `purge_old_logs(db)` — table vide                                | Aucune erreur                                                 |

---

## 4. `services/alert_service.py`

Fichier cible : `app/tests/unit/test_alert_service.py`

> ⚠️ Les fonctions `_process_login_failure_alerts()` et `_process_suspicious_activity_alerts()` sont privées (préfixe `_`).
> Les tester directement via `from app.services.alert_service import _process_login_failure_alerts`.
> Chaque test insère des logs préalables en base (via la session de test rollback), puis appelle la fonction et vérifie les alertes créées.

| #   | Test                                                                              | Comportement attendu                       |
| --- | --------------------------------------------------------------------------------- | ------------------------------------------ |
| 4.1 | `_process_login_failure_alerts()` — 6 échecs en 10 min                            | Crée 1 alerte `severity="medium"`          |
| 4.2 | `_process_login_failure_alerts()` — 11 échecs en 10 min                           | Crée 1 alerte `severity="critical"`        |
| 4.3 | `_process_login_failure_alerts()` — alerte non résolue existante (< 30 min)       | Ne crée pas de doublon                     |
| 4.4 | `_process_login_failure_alerts()` — 3 échecs seulement                            | Ne crée aucune alerte                      |
| 4.5 | `_process_suspicious_activity_alerts()` — 55 actions en 5 min                     | Crée 1 alerte `type="suspicious_activity"` |
| 4.6 | `_process_suspicious_activity_alerts()` — alerte existante non résolue (< 30 min) | Ne crée pas de doublon                     |
| 4.7 | `_process_suspicious_activity_alerts()` — 30 actions seulement                    | Ne crée aucune alerte                      |

---

## 5. `services/matching_service.py`

Fichier cible : `app/tests/unit/test_matching_service.py`

| #   | Test                                        | Comportement attendu                                  |
| --- | ------------------------------------------- | ----------------------------------------------------- |
| 5.1 | Recherche avec origine/destination valides  | Retourne une liste de `PartnerQuote` correspondants   |
| 5.2 | Recherche sans résultat                     | Retourne une liste vide                               |
| 5.3 | Filtre par mode de transport                | Retourne uniquement les quotes du mode demandé        |
| 5.4 | Filtre par poids                            | Retourne uniquement les quotes dans la plage de poids |
| 5.5 | Quote expirée (`valid_until` < aujourd'hui) | Non incluse dans les résultats                        |
| 5.6 | Quote inactive (`is_active=False`)          | Non incluse dans les résultats                        |

---

## 6. `services/import_logic/row_validator.py`

Fichier cible : `app/tests/unit/test_row_validator.py`

| #   | Test                                      | Comportement attendu            |
| --- | ----------------------------------------- | ------------------------------- |
| 6.1 | Ligne valide complète                     | Aucune erreur de validation     |
| 6.2 | Champ obligatoire manquant (ex : origine) | Retourne une erreur descriptive |
| 6.3 | Poids négatif                             | Retourne une erreur             |
| 6.4 | Date de validité au format invalide       | Retourne une erreur             |
| 6.5 | Mode de transport inconnu                 | Retourne une erreur             |
| 6.6 | Prix nul ou négatif                       | Retourne une erreur             |

---

## 7. `services/import_logic/data_normalizer.py`

Fichier cible : `app/tests/unit/test_data_normalizer.py`

> ⚠️ Vérifier que `services/import_logic/data_normalizer.py` existe. Créer les tests uniquement si le fichier est en place.

| #   | Test                                    | Comportement attendu             |
| --- | --------------------------------------- | -------------------------------- |
| 7.1 | Nom de ville en majuscules              | Normalisé en title case          |
| 7.2 | Code pays en minuscules                 | Normalisé en majuscules          |
| 7.3 | Valeur numérique en string `"1 234,56"` | Convertie en float `1234.56`     |
| 7.4 | Date format `DD/MM/YYYY`                | Convertie en objet `date` Python |
| 7.5 | Valeur vide/None                        | Retourne `None` sans erreur      |

---

## 8. `services/customer_quote_service.py`

Fichier cible : `app/tests/unit/test_customer_quote_service.py`

| #   | Test                                                   | Comportement attendu              |
| --- | ------------------------------------------------------ | --------------------------------- |
| 8.1 | `create_quote()` — données valides                     | Crée un devis avec statut `DRAFT` |
| 8.2 | `get_quote()` — ID existant                            | Retourne le devis                 |
| 8.3 | `get_quote()` — ID inexistant                          | Retourne `None`                   |
| 8.4 | `update_quote()` — devis en DRAFT                      | Met à jour les champs fournis     |
| 8.5 | `delete_quote()` — ID existant                         | Supprime et retourne `True`       |
| 8.6 | `delete_quote()` — ID inexistant                       | Retourne `False`                  |
| 8.7 | `add_transport_item()` — `partner_quote_id` valide     | Ajoute une ligne de transport     |
| 8.8 | `add_transport_item()` — `partner_quote_id` inexistant | Lève `ValueError`                 |
