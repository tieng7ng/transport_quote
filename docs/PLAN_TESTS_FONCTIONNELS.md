# Plan de Tests Fonctionnels - Transport Quote

## 1. Introduction

### 1.1 Objectifs

Les tests fonctionnels visent à :
- Valider les parcours utilisateur de bout en bout
- Vérifier l'intégration entre les composants
- Tester les scénarios métier complets
- Assurer la non-régression fonctionnelle

### 1.2 Stack de tests

| Type | Framework | Outils |
|------|-----------|--------|
| Tests API | pytest + httpx | TestClient FastAPI |
| Tests E2E | Playwright | @playwright/test |
| Tests d'intégration | pytest | docker-compose test |

### 1.3 Environnement de test

```
┌─────────────────────────────────────────────────────────────┐
│                  ENVIRONNEMENT DE TEST                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   Playwright │    │   Backend    │    │  PostgreSQL  │   │
│  │   Browser    │───▶│   TestClient │───▶│   Test DB    │   │
│  │              │    │              │    │              │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Structure des fichiers

```
tests/
├── functional/
│   ├── api/
│   │   ├── test_partners_api.py
│   │   ├── test_quotes_api.py
│   │   ├── test_imports_api.py
│   │   ├── test_matching_api.py
│   │   └── test_customer_quotes_api.py
│   ├── scenarios/
│   │   ├── test_quote_creation_flow.py
│   │   ├── test_import_flow.py
│   │   └── test_search_flow.py
│   └── e2e/
│       ├── test_dashboard.spec.ts
│       ├── test_partners.spec.ts
│       ├── test_imports.spec.ts
│       ├── test_search.spec.ts
│       └── test_customer_quotes.spec.ts
```

---

## 2. Tests d'intégration API

### 2.1 Module Partenaires

**Fichier** : `tests/functional/api/test_partners_api.py`

#### TF-PART-001 : CRUD Partenaires

| ID | Cas de test | Méthode | Endpoint | Résultat attendu |
|----|-------------|---------|----------|------------------|
| TF-PART-001-01 | Créer partenaire | POST | /partners/ | 201, partenaire créé |
| TF-PART-001-02 | Créer avec code existant | POST | /partners/ | 400, code déjà utilisé |
| TF-PART-001-03 | Lister partenaires | GET | /partners/ | 200, liste paginée |
| TF-PART-001-04 | Détail partenaire | GET | /partners/{id} | 200, données complètes |
| TF-PART-001-05 | Partenaire inexistant | GET | /partners/xxx | 404 |
| TF-PART-001-06 | Modifier partenaire | PUT | /partners/{id} | 200, données mises à jour |
| TF-PART-001-07 | Supprimer partenaire | DELETE | /partners/{id} | 204, partenaire supprimé |
| TF-PART-001-08 | Supprimer tarifs | DELETE | /partners/{id}/quotes | 200, tarifs supprimés |

```python
class TestPartnersAPI:
    def test_create_partner(self, client):
        response = client.post("/api/v1/partners/", json={
            "code": "TEST",
            "name": "Test Partner",
            "email": "test@test.com"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "TEST"
        assert "id" in data

    def test_create_partner_duplicate_code(self, client, existing_partner):
        response = client.post("/api/v1/partners/", json={
            "code": existing_partner.code,  # Code déjà utilisé
            "name": "Another Partner",
            "email": "other@test.com"
        })
        assert response.status_code == 400

    def test_list_partners(self, client, sample_partners):
        response = client.get("/api/v1/partners/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(sample_partners)

    def test_get_partner_not_found(self, client):
        response = client.get("/api/v1/partners/nonexistent-id")
        assert response.status_code == 404

    def test_delete_partner_cascades_quotes(self, client, partner_with_quotes):
        partner_id = partner_with_quotes.id
        # Vérifier qu'il y a des tarifs
        quotes_before = client.get(f"/api/v1/quotes/?partner_id={partner_id}")
        assert len(quotes_before.json()) > 0

        # Supprimer le partenaire
        response = client.delete(f"/api/v1/partners/{partner_id}")
        assert response.status_code == 204

        # Vérifier que les tarifs sont supprimés
        quotes_after = client.get(f"/api/v1/quotes/?partner_id={partner_id}")
        assert len(quotes_after.json()) == 0
```

### 2.2 Module Import

**Fichier** : `tests/functional/api/test_imports_api.py`

#### TF-IMP-001 : Upload et traitement

| ID | Cas de test | Fichier | Résultat attendu |
|----|-------------|---------|------------------|
| TF-IMP-001-01 | Upload CSV valide | test_valid.csv | Job créé, status PENDING |
| TF-IMP-001-02 | Upload Excel valide | test_valid.xlsx | Job créé, status PENDING |
| TF-IMP-001-03 | Format non supporté | test.txt | 400, format non supporté |
| TF-IMP-001-04 | Fichier trop gros | large_file.xlsx | 413, taille dépassée |
| TF-IMP-001-05 | Partenaire inexistant | - | 404 |

```python
class TestImportsAPI:
    def test_upload_csv(self, client, sample_partner, valid_csv_file):
        response = client.post(
            "/api/v1/imports/",
            data={"partner_id": sample_partner.id},
            files={"file": ("test.csv", valid_csv_file, "text/csv")}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "PENDING"
        assert "id" in data

    def test_upload_unsupported_format(self, client, sample_partner):
        response = client.post(
            "/api/v1/imports/",
            data={"partner_id": sample_partner.id},
            files={"file": ("test.txt", b"content", "text/plain")}
        )
        assert response.status_code == 400
```

#### TF-IMP-002 : Traitement asynchrone

| ID | Cas de test | Données | Résultat attendu |
|----|-------------|---------|------------------|
| TF-IMP-002-01 | Import complet succès | 10 lignes valides | status=COMPLETED, success=10 |
| TF-IMP-002-02 | Import partiel | 8 valides, 2 erreurs | status=COMPLETED, success=8, error=2 |
| TF-IMP-002-03 | Import échec total | 10 lignes invalides | status=FAILED, error=10 |
| TF-IMP-002-04 | Suppression anciens tarifs | Tarifs existants | Anciens supprimés, nouveaux créés |

```python
class TestImportProcessing:
    def test_successful_import(self, client, sample_partner, valid_csv_10_rows):
        # Upload
        response = client.post(
            "/api/v1/imports/",
            data={"partner_id": sample_partner.id},
            files={"file": ("test.csv", valid_csv_10_rows, "text/csv")}
        )
        job_id = response.json()["id"]

        # Attendre traitement (polling)
        for _ in range(10):
            status_response = client.get(f"/api/v1/imports/{job_id}")
            if status_response.json()["status"] != "PROCESSING":
                break
            time.sleep(0.5)

        data = status_response.json()
        assert data["status"] == "COMPLETED"
        assert data["success_count"] == 10
        assert data["error_count"] == 0

    def test_import_replaces_old_quotes(self, client, partner_with_quotes):
        partner_id = partner_with_quotes.id
        old_quotes_count = len(client.get(f"/api/v1/quotes/?partner_id={partner_id}").json())

        # Import nouveau fichier
        response = client.post(
            "/api/v1/imports/",
            data={"partner_id": partner_id},
            files={"file": ("new.csv", new_csv_file, "text/csv")}
        )
        job_id = response.json()["id"]

        # Attendre traitement
        wait_for_job_completion(client, job_id)

        # Vérifier que les anciens tarifs sont remplacés
        new_quotes = client.get(f"/api/v1/quotes/?partner_id={partner_id}").json()
        assert len(new_quotes) != old_quotes_count  # Nombre différent
```

#### TF-IMP-003 : Import formats spécifiques

| ID | Cas de test | Partenaire | Fichier | Résultat attendu |
|----|-------------|------------|---------|------------------|
| TF-IMP-003-01 | BESSON grid | BESSON | grille_besson.xlsx | N lignes par dept×poids |
| TF-IMP-003-02 | BIANCHI dual_grid | BIANCHI | bianchi.xlsx | 9 lignes par dept |
| TF-IMP-003-03 | MONACO_LOG dual_grid | MONACO_LOG | monaco.xlsx | 9 lignes par dept |
| TF-IMP-003-04 | Transform postal code | BIANCHI | "20 (1)" | dest_postal_code="2A" |

```python
class TestImportSpecificFormats:
    def test_besson_grid_import(self, client, besson_partner, besson_file):
        response = client.post(
            "/api/v1/imports/",
            data={"partner_id": besson_partner.id},
            files={"file": ("besson.xlsx", besson_file, EXCEL_MIME)}
        )
        job_id = response.json()["id"]
        wait_for_job_completion(client, job_id)

        # Vérifier le pivot des colonnes poids
        quotes = client.get(f"/api/v1/quotes/?partner_id={besson_partner.id}").json()
        # Chaque ligne Excel génère plusieurs lignes (une par colonne poids)
        assert len(quotes) > 0

        # Vérifier les tranches de poids
        weight_ranges = set((q["weight_min"], q["weight_max"]) for q in quotes)
        assert (0, 5) in weight_ranges
        assert (6, 10) in weight_ranges

    def test_bianchi_dual_grid_transforms(self, client, bianchi_partner, bianchi_file):
        response = client.post(
            "/api/v1/imports/",
            data={"partner_id": bianchi_partner.id},
            files={"file": ("bianchi.xlsx", bianchi_file, EXCEL_MIME)}
        )
        job_id = response.json()["id"]
        wait_for_job_completion(client, job_id)

        quotes = client.get(f"/api/v1/quotes/?partner_id={bianchi_partner.id}").json()

        # Vérifier transformation code postal Corse
        corsica_quotes = [q for q in quotes if q["dest_postal_code"] in ["2A", "2B"]]
        assert len(corsica_quotes) > 0

        # Vérifier pricing_type différent selon section
        small_weight_quotes = [q for q in quotes if q["weight_max"] <= 1000]
        large_weight_quotes = [q for q in quotes if q["weight_min"] > 1000]
        assert any(q["pricing_type"] == "PER_100KG" for q in small_weight_quotes)
        assert any(q["pricing_type"] == "LUMPSUM" for q in large_weight_quotes)
```

### 2.3 Module Matching

**Fichier** : `tests/functional/api/test_matching_api.py`

#### TF-MATCH-001 : Recherche de tarifs

| ID | Cas de test | Critères | Résultat attendu |
|----|-------------|----------|------------------|
| TF-MATCH-001-01 | Recherche simple | FR→FR, 500kg | Liste de tarifs |
| TF-MATCH-001-02 | Filtre département | dest=69 | Seulement dept 69 |
| TF-MATCH-001-03 | Filtre poids | 500kg | Tarifs couvrant 500kg |
| TF-MATCH-001-04 | Aucun résultat | dest=99 (inexistant) | Liste vide |
| TF-MATCH-001-05 | Tri par prix | - | Résultats triés croissant |
| TF-MATCH-001-06 | Calcul prix PER_100KG | 250kg | Prix × 3 |
| TF-MATCH-001-07 | Calcul prix LUMPSUM | 250kg | Prix fixe |

```python
class TestMatchingAPI:
    def test_search_returns_matching_quotes(self, client, sample_quotes):
        response = client.post("/api/v1/match/", json={
            "origin_country": "FR",
            "dest_country": "FR",
            "dest_postal_code": "69",
            "weight": 500
        })
        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0
        assert all(r["dest_postal_code"].startswith("69") for r in results)

    def test_search_filters_by_weight_range(self, client, sample_quotes):
        response = client.post("/api/v1/match/", json={
            "origin_country": "FR",
            "dest_country": "FR",
            "weight": 500
        })
        results = response.json()
        for r in results:
            assert r["weight_min"] <= 500 <= r["weight_max"]

    def test_search_calculates_per_100kg_price(self, client, per_100kg_quote):
        # per_100kg_quote: cost=17, pricing_type=PER_100KG
        response = client.post("/api/v1/match/", json={
            "origin_country": "FR",
            "dest_country": "FR",
            "dest_postal_code": per_100kg_quote.dest_postal_code,
            "weight": 250  # Arrondi à 300kg
        })
        results = response.json()
        matching = [r for r in results if r["id"] == per_100kg_quote.id][0]
        assert float(matching["cost"]) == 51.0  # 17 × 3

    def test_search_returns_sorted_by_price(self, client, multiple_quotes):
        response = client.post("/api/v1/match/", json={
            "origin_country": "FR",
            "dest_country": "FR",
            "weight": 500
        })
        results = response.json()
        prices = [float(r["cost"]) for r in results]
        assert prices == sorted(prices)

    def test_search_no_results(self, client):
        response = client.post("/api/v1/match/", json={
            "origin_country": "FR",
            "dest_country": "XX",  # Pays inexistant
            "weight": 500
        })
        assert response.status_code == 200
        assert response.json() == []
```

### 2.4 Module Devis Clients

**Fichier** : `tests/functional/api/test_customer_quotes_api.py`

#### TF-CQ-001 : CRUD Devis

| ID | Cas de test | Méthode | Résultat attendu |
|----|-------------|---------|------------------|
| TF-CQ-001-01 | Créer devis | POST | 201, référence générée |
| TF-CQ-001-02 | Lister devis | GET | 200, liste paginée |
| TF-CQ-001-03 | Détail devis | GET /{id} | 200, avec items |
| TF-CQ-001-04 | Modifier devis | PUT /{id} | 200, données mises à jour |
| TF-CQ-001-05 | Supprimer devis | DELETE /{id} | 204 |

```python
class TestCustomerQuotesAPI:
    def test_create_quote_generates_reference(self, client):
        response = client.post("/api/v1/customer-quotes/")
        assert response.status_code == 201
        data = response.json()
        assert data["reference"].startswith("DEV-")
        assert data["status"] == "DRAFT"

    def test_get_quote_includes_items(self, client, quote_with_items):
        response = client.get(f"/api/v1/customer-quotes/{quote_with_items.id}")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == len(quote_with_items.items)
```

#### TF-CQ-002 : Gestion des lignes

| ID | Cas de test | Action | Résultat attendu |
|----|-------------|--------|------------------|
| TF-CQ-002-01 | Ajouter transport | POST /{id}/items | Ligne créée avec marge |
| TF-CQ-002-02 | Ajouter frais | POST /{id}/fees | Ligne FEE, marge 100% |
| TF-CQ-002-03 | Modifier prix vente | PUT /{id}/items/{item} | Marge recalculée |
| TF-CQ-002-04 | Modifier marge | PUT /{id}/items/{item} | Prix recalculé |
| TF-CQ-002-05 | Supprimer ligne | DELETE /{id}/items/{item} | Totaux recalculés |

```python
class TestCustomerQuoteItems:
    def test_add_transport_item_with_margin(self, client, empty_quote, partner_quote):
        response = client.post(
            f"/api/v1/customer-quotes/{empty_quote.id}/items",
            json={
                "partner_quote_id": partner_quote.id,
                "weight": 500
            }
        )
        assert response.status_code == 201
        item = response.json()
        assert item["type"] == "TRANSPORT"
        assert item["margin_percent"] > 0
        assert item["sell_price"] > item["cost_price"]

    def test_add_fee_has_100_percent_margin(self, client, empty_quote):
        response = client.post(
            f"/api/v1/customer-quotes/{empty_quote.id}/fees",
            json={
                "description": "Manutention",
                "sell_price": 50
            }
        )
        assert response.status_code == 201
        item = response.json()
        assert item["type"] == "FEE"
        assert item["cost_price"] == 0
        assert item["margin_percent"] == 100

    def test_update_sell_price_recalculates_margin(self, client, quote_with_item):
        item = quote_with_item.items[0]
        original_margin = item.margin_percent

        response = client.put(
            f"/api/v1/customer-quotes/{quote_with_item.id}/items/{item.id}",
            json={"sell_price": item.sell_price * 2}
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["margin_percent"] != original_margin

    def test_remove_item_recalculates_totals(self, client, quote_with_multiple_items):
        quote_id = quote_with_multiple_items.id
        item_to_remove = quote_with_multiple_items.items[0]

        # Totaux avant
        before = client.get(f"/api/v1/customer-quotes/{quote_id}").json()
        total_before = before["total"]

        # Supprimer
        client.delete(f"/api/v1/customer-quotes/{quote_id}/items/{item_to_remove.id}")

        # Totaux après
        after = client.get(f"/api/v1/customer-quotes/{quote_id}").json()
        assert after["total"] < total_before
```

#### TF-CQ-003 : Calcul des totaux

| ID | Cas de test | Items | Résultat attendu |
|----|-------------|-------|------------------|
| TF-CQ-003-01 | Total transport | 2 items transport | Somme sell_price |
| TF-CQ-003-02 | Total frais | 2 items frais | Somme sell_price |
| TF-CQ-003-03 | Total général | transport + frais | transport + fees |
| TF-CQ-003-04 | Marge totale | items avec marges | Somme margin_amount |

```python
class TestCustomerQuoteTotals:
    def test_totals_calculation(self, client, empty_quote, partner_quotes):
        quote_id = empty_quote.id

        # Ajouter 2 transports
        for pq in partner_quotes[:2]:
            client.post(f"/api/v1/customer-quotes/{quote_id}/items", json={
                "partner_quote_id": pq.id,
                "weight": 500
            })

        # Ajouter 1 frais
        client.post(f"/api/v1/customer-quotes/{quote_id}/fees", json={
            "description": "Frais",
            "sell_price": 50
        })

        # Vérifier totaux
        quote = client.get(f"/api/v1/customer-quotes/{quote_id}").json()

        transport_items = [i for i in quote["items"] if i["type"] == "TRANSPORT"]
        fee_items = [i for i in quote["items"] if i["type"] == "FEE"]

        expected_transport = sum(i["sell_price"] for i in transport_items)
        expected_fees = sum(i["sell_price"] for i in fee_items)

        assert quote["transport_subtotal"] == expected_transport
        assert quote["fees_total"] == expected_fees
        assert quote["total"] == expected_transport + expected_fees
```

---

## 3. Scénarios de bout en bout

### 3.1 Scénario : Création d'un devis complet

**Fichier** : `tests/functional/scenarios/test_quote_creation_flow.py`

#### TF-SCEN-001 : Parcours création devis

```gherkin
Feature: Création d'un devis client

  Scenario: Créer un devis avec transport et frais
    Given un partenaire "DHL" avec des tarifs Paris→Lyon
    And un utilisateur connecté

    When je crée un nouveau devis
    Then le devis est en statut "DRAFT"
    And une référence est générée

    When je recherche un tarif Paris→Lyon pour 500kg
    Then je vois les tarifs disponibles

    When j'ajoute le tarif DHL au devis
    Then une ligne transport est créée
    And la marge par défaut est appliquée

    When j'ajoute un frais "Manutention" de 50€
    Then une ligne frais est créée

    When je modifie la marge du transport à 25%
    Then le prix de vente est recalculé

    Then le total du devis est correct
    And la marge totale est correcte
```

```python
class TestQuoteCreationScenario:
    def test_complete_quote_creation_flow(self, client, dhl_partner_with_quotes):
        # 1. Créer le devis
        quote_response = client.post("/api/v1/customer-quotes/")
        quote_id = quote_response.json()["id"]
        assert quote_response.json()["status"] == "DRAFT"

        # 2. Rechercher un tarif
        search_response = client.post("/api/v1/match/", json={
            "origin_country": "FR",
            "origin_city": "PARIS",
            "dest_country": "FR",
            "dest_postal_code": "69",
            "weight": 500
        })
        tarifs = search_response.json()
        assert len(tarifs) > 0
        dhl_tarif = next(t for t in tarifs if "DHL" in t["partner"]["name"])

        # 3. Ajouter au devis
        item_response = client.post(
            f"/api/v1/customer-quotes/{quote_id}/items",
            json={"partner_quote_id": dhl_tarif["id"], "weight": 500}
        )
        item_id = item_response.json()["id"]
        assert item_response.json()["type"] == "TRANSPORT"

        # 4. Ajouter un frais
        fee_response = client.post(
            f"/api/v1/customer-quotes/{quote_id}/fees",
            json={"description": "Manutention", "sell_price": 50}
        )
        assert fee_response.json()["type"] == "FEE"

        # 5. Modifier la marge
        update_response = client.put(
            f"/api/v1/customer-quotes/{quote_id}/items/{item_id}",
            json={"margin_percent": 25}
        )
        assert update_response.json()["margin_percent"] == 25

        # 6. Vérifier les totaux
        final_quote = client.get(f"/api/v1/customer-quotes/{quote_id}").json()
        assert final_quote["total"] > 0
        assert final_quote["total_margin"] > 0
        assert final_quote["total"] == (
            final_quote["transport_subtotal"] + final_quote["fees_total"]
        )
```

### 3.2 Scénario : Import et recherche

**Fichier** : `tests/functional/scenarios/test_import_flow.py`

#### TF-SCEN-002 : Import puis recherche

```gherkin
Feature: Import de tarifs puis recherche

  Scenario: Importer des tarifs et les retrouver en recherche
    Given un partenaire "BESSON" configuré pour import grid
    And un fichier Excel avec la grille tarifaire

    When j'uploade le fichier pour BESSON
    Then un job d'import est créé

    When le job est terminé
    Then le statut est "COMPLETED"
    And les tarifs sont créés en base

    When je recherche Nice→01 pour 500kg
    Then je trouve le tarif BESSON
    And le prix est calculé selon PER_100KG
```

```python
class TestImportAndSearchScenario:
    def test_import_then_search(self, client, besson_partner, besson_excel_file):
        # 1. Upload
        upload_response = client.post(
            "/api/v1/imports/",
            data={"partner_id": besson_partner.id},
            files={"file": ("besson.xlsx", besson_excel_file, EXCEL_MIME)}
        )
        job_id = upload_response.json()["id"]

        # 2. Attendre traitement
        job = wait_for_job_completion(client, job_id)
        assert job["status"] == "COMPLETED"
        assert job["success_count"] > 0

        # 3. Rechercher
        search_response = client.post("/api/v1/match/", json={
            "origin_country": "FR",
            "origin_city": "NICE",
            "dest_country": "FR",
            "dest_postal_code": "01",
            "weight": 500
        })
        results = search_response.json()

        # 4. Vérifier résultat BESSON
        besson_results = [r for r in results if r["partner"]["code"] == "BESSON"]
        assert len(besson_results) > 0

        # 5. Vérifier calcul prix (PER_100KG)
        # 500kg → arrondi 500kg, donc × 5
        for r in besson_results:
            if r["pricing_type"] == "PER_100KG":
                base_cost = r["cost"] / 5  # Retrouver le coût unitaire
                assert base_cost > 0
```

---

## 4. Tests E2E (Playwright)

### 4.1 Configuration Playwright

```typescript
// playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:8080',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  },
  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
    { name: 'firefox', use: { browserName: 'firefox' } }
  ]
});
```

### 4.2 Tests Dashboard

**Fichier** : `tests/e2e/test_dashboard.spec.ts`

| ID | Cas de test | Actions | Vérifications |
|----|-------------|---------|---------------|
| TF-E2E-DASH-01 | Affichage stats | Charger page | Stats visibles |
| TF-E2E-DASH-02 | Navigation partenaires | Clic lien | Redirection /partners |
| TF-E2E-DASH-03 | Navigation imports | Clic lien | Redirection /imports |

```typescript
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('displays statistics cards', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('Partenaires')).toBeVisible();
    await expect(page.getByText('Tarifs')).toBeVisible();
  });

  test('navigates to partners page', async ({ page }) => {
    await page.goto('/');
    await page.click('text=Partenaires');

    await expect(page).toHaveURL('/partners');
  });
});
```

### 4.3 Tests Partenaires

**Fichier** : `tests/e2e/test_partners.spec.ts`

| ID | Cas de test | Actions | Vérifications |
|----|-------------|---------|---------------|
| TF-E2E-PART-01 | Créer partenaire | Formulaire | Partenaire dans liste |
| TF-E2E-PART-02 | Modifier partenaire | Édition | Données mises à jour |
| TF-E2E-PART-03 | Supprimer partenaire | Confirmation | Partenaire supprimé |

```typescript
test.describe('Partners Management', () => {
  test('creates a new partner', async ({ page }) => {
    await page.goto('/partners');

    // Ouvrir modal
    await page.click('button:has-text("Nouveau partenaire")');

    // Remplir formulaire
    await page.fill('input[name="code"]', 'TEST_E2E');
    await page.fill('input[name="name"]', 'Test E2E Partner');
    await page.fill('input[name="email"]', 'test@e2e.com');

    // Soumettre
    await page.click('button:has-text("Créer")');

    // Vérifier création
    await expect(page.getByText('TEST_E2E')).toBeVisible();
    await expect(page.getByText('Test E2E Partner')).toBeVisible();
  });

  test('deletes partner with confirmation', async ({ page }) => {
    await page.goto('/partners');

    // Trouver le partenaire
    const row = page.locator('tr:has-text("TEST_E2E")');
    await row.locator('button[aria-label="Supprimer"]').click();

    // Confirmer
    await page.click('button:has-text("Confirmer")');

    // Vérifier suppression
    await expect(page.getByText('TEST_E2E')).not.toBeVisible();
  });
});
```

### 4.4 Tests Import

**Fichier** : `tests/e2e/test_imports.spec.ts`

| ID | Cas de test | Actions | Vérifications |
|----|-------------|---------|---------------|
| TF-E2E-IMP-01 | Upload fichier | Sélection + upload | Job créé |
| TF-E2E-IMP-02 | Suivi statut | Polling | Statut COMPLETED |
| TF-E2E-IMP-03 | Affichage erreurs | Import partiel | Erreurs listées |

```typescript
test.describe('Imports', () => {
  test('uploads file and shows progress', async ({ page }) => {
    await page.goto('/imports');

    // Sélectionner partenaire
    await page.selectOption('select[name="partner"]', 'BESSON');

    // Upload fichier
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./fixtures/besson_test.xlsx');

    // Lancer import
    await page.click('button:has-text("Importer")');

    // Vérifier statut
    await expect(page.getByText('En cours')).toBeVisible();

    // Attendre completion (max 30s)
    await expect(page.getByText('Terminé')).toBeVisible({ timeout: 30000 });

    // Vérifier compteurs
    await expect(page.getByText(/\d+ lignes importées/)).toBeVisible();
  });
});
```

### 4.5 Tests Recherche

**Fichier** : `tests/e2e/test_search.spec.ts`

| ID | Cas de test | Actions | Vérifications |
|----|-------------|---------|---------------|
| TF-E2E-SEARCH-01 | Recherche simple | Formulaire | Résultats affichés |
| TF-E2E-SEARCH-02 | Autocomplete ville | Saisie | Suggestions |
| TF-E2E-SEARCH-03 | Aucun résultat | Critères impossibles | Message vide |

```typescript
test.describe('Search', () => {
  test('searches and displays results', async ({ page }) => {
    await page.goto('/search');

    // Remplir formulaire
    await page.selectOption('select[name="origin_country"]', 'FR');
    await page.fill('input[name="origin_postal_code"]', '75');
    await page.selectOption('select[name="dest_country"]', 'FR');
    await page.fill('input[name="dest_postal_code"]', '69');
    await page.fill('input[name="weight"]', '500');

    // Rechercher
    await page.click('button:has-text("Rechercher")');

    // Vérifier redirection et résultats
    await expect(page).toHaveURL('/results');
    await expect(page.getByText('offre(s) correspondante(s)')).toBeVisible();
  });

  test('shows autocomplete suggestions for city', async ({ page }) => {
    await page.goto('/search');

    // Saisir début de ville
    await page.fill('input[name="origin_city"]', 'Par');

    // Attendre suggestions
    await expect(page.getByText('PARIS')).toBeVisible();
  });
});
```

### 4.6 Tests Devis Client

**Fichier** : `tests/e2e/test_customer_quotes.spec.ts`

| ID | Cas de test | Actions | Vérifications |
|----|-------------|---------|---------------|
| TF-E2E-CQ-01 | Créer devis | Bouton nouveau | Devis créé |
| TF-E2E-CQ-02 | Ajouter transport | Recherche + ajout | Ligne ajoutée |
| TF-E2E-CQ-03 | Modifier marge | Édition inline | Totaux recalculés |
| TF-E2E-CQ-04 | Ajouter frais | Modal frais | Ligne frais ajoutée |

```typescript
test.describe('Customer Quotes', () => {
  test('creates quote and adds transport item', async ({ page }) => {
    // Créer devis
    await page.goto('/customer-quotes');
    await page.click('button:has-text("Nouveau devis")');

    // Vérifier création
    await expect(page).toHaveURL(/\/customer-quotes\/.*\/edit/);
    await expect(page.getByText(/DEV-\d{4}-\d{4}/)).toBeVisible();

    // Ouvrir recherche
    await page.click('button:has-text("Ajouter transport")');

    // Remplir et rechercher
    await page.fill('input[name="dest_postal_code"]', '69');
    await page.fill('input[name="weight"]', '500');
    await page.click('button:has-text("Rechercher")');

    // Ajouter premier résultat
    await page.click('button:has-text("Ajouter au devis")');

    // Vérifier ajout
    await expect(page.locator('.quote-item')).toHaveCount(1);
  });

  test('modifies margin and recalculates total', async ({ page }) => {
    await page.goto('/customer-quotes/test-quote-id/edit');

    // Modifier marge
    const marginInput = page.locator('input[name="margin_percent"]').first();
    await marginInput.fill('30');
    await marginInput.blur();

    // Vérifier recalcul
    await expect(page.getByText('Marge: 30%')).toBeVisible();
  });

  test('adds fee item', async ({ page }) => {
    await page.goto('/customer-quotes/test-quote-id/edit');

    // Ouvrir modal frais
    await page.click('button:has-text("Ajouter frais")');

    // Remplir
    await page.fill('input[name="description"]', 'Manutention spéciale');
    await page.fill('input[name="price"]', '75');

    // Ajouter
    await page.click('button:has-text("Ajouter")');

    // Vérifier
    await expect(page.getByText('Manutention spéciale')).toBeVisible();
    await expect(page.getByText('75,00 €')).toBeVisible();
  });
});
```

---

## 5. Données de test

### 5.1 Fixtures fichiers

```
tests/fixtures/
├── csv/
│   ├── valid_10_rows.csv
│   ├── invalid_missing_cost.csv
│   └── mixed_valid_invalid.csv
├── excel/
│   ├── besson_test.xlsx
│   ├── bianchi_test.xlsx
│   └── monaco_log_test.xlsx
└── screenshots/
    └── (généré par Playwright)
```

### 5.2 Données CSV de test

```csv
# valid_10_rows.csv
transport_mode,origin_city,origin_country,dest_city,dest_country,dest_postal_code,weight_min,weight_max,cost,pricing_type
ROAD,PARIS,FR,LYON,FR,69,0,500,15.00,PER_100KG
ROAD,PARIS,FR,LYON,FR,69,501,1000,12.00,PER_100KG
ROAD,PARIS,FR,MARSEILLE,FR,13,0,500,25.00,PER_100KG
...
```

### 5.3 Seed database

```python
# tests/seed_data.py
def seed_test_data(db: Session):
    # Partenaires
    partners = [
        Partner(code="DHL", name="DHL Express", email="dhl@test.com"),
        Partner(code="BESSON", name="Transport Besson", email="besson@test.com"),
        Partner(code="BIANCHI", name="Bianchi Group", email="bianchi@test.com"),
    ]
    db.add_all(partners)

    # Tarifs
    quotes = [
        PartnerQuote(
            partner_id=partners[0].id,
            transport_mode="ROAD",
            origin_city="PARIS", origin_country="FR",
            dest_city="LYON", dest_country="FR", dest_postal_code="69",
            weight_min=0, weight_max=500,
            cost=15.00, pricing_type="PER_100KG"
        ),
        # ... autres tarifs
    ]
    db.add_all(quotes)
    db.commit()
```

---

## 6. Environnement CI/CD

### 6.1 GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt
      - name: Run tests
        run: pytest backend/tests/ --cov=app

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run tests
        run: cd frontend && npm test

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: sleep 30
      - name: Run Playwright tests
        run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 7. Couverture et rapports

### 7.1 Objectifs de couverture fonctionnelle

| Module | Scénarios couverts |
|--------|-------------------|
| Partenaires | CRUD complet |
| Import | Upload, traitement, erreurs |
| Matching | Recherche, filtres, calculs |
| Devis | CRUD, items, totaux |
| E2E | Parcours principaux |

### 7.2 Métriques de qualité

| Métrique | Cible |
|----------|-------|
| Tests API passants | 100% |
| Tests E2E passants | 95% |
| Temps exécution API | < 5 min |
| Temps exécution E2E | < 10 min |
| Couverture scénarios critiques | 100% |

---

## 8. Matrice de traçabilité

| Exigence fonctionnelle | Tests |
|-----------------------|-------|
| Créer partenaire | TF-PART-001-01, TF-E2E-PART-01 |
| Importer tarifs | TF-IMP-001, TF-IMP-002, TF-E2E-IMP-01 |
| Rechercher tarifs | TF-MATCH-001, TF-E2E-SEARCH-01 |
| Créer devis | TF-CQ-001-01, TF-E2E-CQ-01 |
| Ajouter ligne transport | TF-CQ-002-01, TF-E2E-CQ-02 |
| Modifier marge | TF-CQ-002-03, TF-E2E-CQ-03 |
| Calculer totaux | TF-CQ-003, TF-SCEN-001 |
| Parcours complet devis | TF-SCEN-001 |
