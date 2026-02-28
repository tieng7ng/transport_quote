# Plan de tests E2E — Frontend (Playwright)

Les tests E2E simulent un utilisateur réel dans un navigateur.
Ils s'appuient sur la configuration existante dans `playwright.config.ts` (base URL : `http://localhost`).

Commande d'exécution :
```bash
cd frontend
npx playwright test           # tous les tests
npx playwright test auth      # un fichier spécifique
npx playwright test --ui      # mode interactif
```

---

## Fixtures communes

À créer dans `e2e/fixtures.ts` :

```typescript
// Connexion rapide sans passer par l'UI (stocke le token en localStorage)
loginAs(page, role: "admin" | "commercial" | "operator" | "viewer")

// Vérifier qu'un élément est visible/absent
expectVisible(page, selector)
expectForbidden(page)   // vérifie redirection ou message 403
```

---

## 1. Authentification — `e2e/auth.spec.ts` *(existant — à compléter)*

| #   | Test                          | Scénario                                                                         |
| --- | ----------------------------- | -------------------------------------------------------------------------------- |
| 1.1 | Login valide                  | Saisir login/MDP → redirect vers Dashboard                                       |
| 1.2 | Login invalide                | Saisir mauvais MDP → message d'erreur visible                                    |
| 1.3 | Login compte inactif          | Message d'erreur approprié                                                       |
| 1.4 | Logout                        | Clic sur Déconnexion → redirect vers `/login`                                    |
| 1.5 | Route protégée sans connexion | Accéder à `/dashboard` → redirect vers `/login`                                  |
| 1.6 | Changement de MDP obligatoire | Connexion avec `must_change_password=true` → modale de changement de MDP s'ouvre |
| 1.7 | Session expirée               | Token expiré → redirect automatique vers `/login`                                |

> 🛠️ **Setup 1.7** : simuler un token expiré en injectant un JWT à `exp = now - 1s` dans `localStorage` via `page.evaluate()` avant de naviguer.

---

## 2. Dashboard — `e2e/dashboard.spec.ts`

| #   | Test                    | Scénario                                                    |
| --- | ----------------------- | ----------------------------------------------------------- |
| 2.1 | Chargement du dashboard | Connexion → dashboard visible avec éléments principaux      |
| 2.2 | Navigation sidebar      | Clic sur chaque lien de la sidebar → bonne page chargée     |
| 2.3 | Menu utilisateur        | Clic sur avatar → menu déroulant avec Profil et Déconnexion |

---

## 3. Recherche & Résultats — `e2e/search.spec.ts`

| #   | Test                          | Scénario                                              |
| --- | ----------------------------- | ----------------------------------------------------- |
| 3.1 | Formulaire de recherche       | Remplir origine, destination, mode, poids → soumettre |
| 3.2 | Affichage des résultats       | Résultats affichés avec partenaire, prix, mode        |
| 3.3 | Recherche sans résultat       | Message "Aucun résultat" visible                      |
| 3.4 | Ajouter un résultat au panier | Clic sur "Ajouter" → confirmation visible             |
| 3.5 | Filtres sur les résultats     | Filtrer par mode de transport → liste mise à jour     |

---

## 4. Devis clients — `e2e/customer-quotes.spec.ts`

| #   | Test                         | Scénario                                                   |
| --- | ---------------------------- | ---------------------------------------------------------- |
| 4.1 | Liste des devis              | Page `/customer-quotes` chargée avec tableau               |
| 4.2 | Créer un devis               | Clic sur Nouveau → formulaire → soumission → devis créé    |
| 4.3 | Détail d'un devis            | Clic sur un devis → page détail avec lignes et totaux      |
| 4.4 | Modifier un devis en DRAFT   | Édition d'une ligne → sauvegarde → valeurs mises à jour    |
| 4.5 | Changer statut vers READY    | Bouton "Marquer comme prêt" → statut mis à jour            |
| 4.6 | Changer statut vers SENT     | Bouton "Envoyer" → statut SENT                             |
| 4.7 | Devis en SENT non modifiable | Champs désactivés, boutons d'édition masqués               |
| 4.8 | Supprimer un devis en DRAFT  | Bouton supprimer → confirmation → devis retiré de la liste |

---

## 5. Imports — `e2e/imports.spec.ts`

| #   | Test                      | Scénario                                                        |
| --- | ------------------------- | --------------------------------------------------------------- |
| 5.1 | Accès réservé SUPER_ADMIN | Connexion COMMERCIAL → menu Imports absent                      |
| 5.2 | Upload d'un fichier CSV   | Sélectionner fichier → uploader → statut PENDING puis COMPLETED |
| 5.3 | Upload extension invalide | Sélectionner `.exe` → message d'erreur                          |
| 5.4 | Liste des imports         | Tableau avec historique des imports et statuts                  |

---

## 6. Gestion des utilisateurs — `e2e/users.spec.ts`

| #   | Test                      | Scénario                                            |
| --- | ------------------------- | --------------------------------------------------- |
| 6.1 | Accès réservé ADMIN+      | Connexion COMMERCIAL → menu Utilisateurs absent     |
| 6.2 | Liste des utilisateurs    | Page `/users` chargée avec tableau                  |
| 6.3 | Créer un utilisateur      | Formulaire → soumission → utilisateur dans la liste |
| 6.4 | Modifier un rôle          | Éditer → changer rôle → sauvegarder                 |
| 6.5 | Désactiver un utilisateur | Bouton désactiver → confirmation → statut inactif   |

---

## 7. Historique des activités — `e2e/activity-logs.spec.ts`

| #   | Test                   | Scénario                                                                                                    |
| --- | ---------------------- | ----------------------------------------------------------------------------------------------------------- |
| 7.1 | Accès réservé ADMIN+   | Connexion COMMERCIAL → lien Historique absent dans sidebar                                                  |
| 7.2 | Chargement de la page  | Page `/admin/activity` → tableau avec actions                                                               |
| 7.3 | Filtre par utilisateur | Sélectionner un utilisateur → tableau filtré                                                                |
| 7.4 | Filtre par action      | Sélectionner "Recherche" → uniquement des `search.performed`                                                |
| 7.5 | Filtre par date        | Sélectionner une période → résultats dans la période                                                        |
| 7.6 | Expand détails         | Clic sur `[+]` → panneau JSON des détails visible                                                           |
| 7.7 | Export CSV             | Clic Exporter → choisir CSV → téléchargement déclenché                                                      |
| 7.8 | Export PDF             | ~~Clic Exporter → choisir PDF → téléchargement déclenché~~ ⚠️ *[Non implémenté — uniquement CSV disponible]* |
| 7.9 | Pagination             | Clic sur page 2 → données différentes                                                                       |

---

## 8. Statistiques — `e2e/statistics.spec.ts`

| #   | Test                    | Scénario                                                                                   |
| --- | ----------------------- | ------------------------------------------------------------------------------------------ |
| 8.1 | Accès réservé ADMIN+    | Connexion COMMERCIAL → lien Statistiques absent                                            |
| 8.2 | Chargement de la page   | Page `/admin/statistics` → KPIs et graphiques visibles                                     |
| 8.3 | Sélecteur de période    | Changer de "Ce mois" à "7 jours" → KPIs mis à jour                                         |
| 8.4 | Top routes              | Section "Routes les plus recherchées" visible                                              |
| 8.5 | Activité par commercial | Section "Activité par commercial" visible avec badges colorés (créés / envoyés / acceptés) |
| 8.6 | Modes de transport      | Répartition visible avec pourcentages                                                      |

---

## 9. Alertes de sécurité — `e2e/alerts.spec.ts`

| #   | Test                         | Scénario                                                   |
| --- | ---------------------------- | ---------------------------------------------------------- |
| 9.1 | Badge absent pour COMMERCIAL | Connexion COMMERCIAL → icône cloche sans badge rouge       |
| 9.2 | Badge visible pour ADMIN     | Présence d'alertes → badge rouge avec compteur             |
| 9.3 | Ouverture du panneau alertes | Clic sur cloche → dropdown listant les alertes             |
| 9.4 | Marquer comme lu             | Clic sur "Marquer comme lu" → alerte disparaît de la liste |
| 9.5 | Résoudre — ignorer           | Clic "Ignorer" → alerte résolue, compteur mis à jour       |
| 9.6 | Résoudre — désactiver compte | Clic "Désactiver le compte" → alerte résolue               |
| 9.7 | Rafraîchissement automatique | Attendre 30s → badge mis à jour sans rechargement de page  |

> 🛠️ **Setup 9.7** : utiliser `await page.clock.install()` + `await page.clock.fastForward('00:31')` (Playwright clock API) plutôt qu'une attente réelle de 30s.

---

## 10. Contrôle d'accès RBAC — `e2e/rbac.spec.ts`

| #    | Test        | Rôle                                               | Page                    | Attendu |
| ---- | ----------- | -------------------------------------------------- | ----------------------- | ------- |
| 10.1 | VIEWER      | `/admin/activity`                                  | Redirect ou 403         |
| 10.2 | VIEWER      | `/admin/statistics`                                | Redirect ou 403         |
| 10.3 | COMMERCIAL  | `/admin/activity`                                  | Redirect ou 403         |
| 10.4 | COMMERCIAL  | `/users`                                           | Redirect ou 403         |
| 10.5 | OPERATOR    | `/imports`                                         | Redirect ou 403         |
| 10.6 | ADMIN       | `/admin/activity`                                  | `200` — page accessible |
| 10.7 | SUPER_ADMIN | Toutes les pages                                   | Toutes accessibles      |
| 10.8 | Navigation  | Sidebar n'affiche que les liens autorisés par rôle |                         |
