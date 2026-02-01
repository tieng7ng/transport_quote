# Plan de Tests Unitaires - Transport Quote

## 1. Introduction

### 1.1 Objectifs

Les tests unitaires visent à :
- Valider le comportement isolé de chaque composant
- Détecter les régressions lors des modifications
- Documenter le comportement attendu du code
- Faciliter le refactoring en toute confiance

### 1.2 Stack de tests

| Composant | Framework | Outils complémentaires |
|-----------|-----------|------------------------|
| Backend Python | pytest | pytest-cov, pytest-asyncio |
| Frontend React | Vitest | @testing-library/react |
| Mocking | unittest.mock | pytest-mock |
| Base de données | SQLite in-memory | pytest fixtures |

### 1.3 Convention de nommage

```
test_<module>_<fonction>_<scenario>_<resultat_attendu>

Exemples:
- test_pricing_service_calculate_sell_price_with_20_percent_margin_returns_correct_value
- test_matching_service_find_quotes_no_results_returns_empty_list
```

### 1.4 Structure des fichiers de tests

```
backend/
├── tests/
│   ├── conftest.py              # Fixtures partagées
│   ├── unit/
│   │   ├── services/
│   │   │   ├── test_pricing_service.py
│   │   │   ├── test_matching_service.py
│   │   │   ├── test_customer_quote_service.py
│   │   │   ├── test_import_service.py
│   │   │   └── test_quote_service.py
│   │   ├── import_logic/
│   │   │   ├── test_column_mapper.py
│   │   │   ├── test_data_normalizer.py
│   │   │   └── test_row_validator.py
│   │   ├── models/
│   │   │   ├── test_partner.py
│   │   │   ├── test_partner_quote.py
│   │   │   └── test_customer_quote.py
│   │   └── schemas/
│   │       └── test_validations.py
│   └── integration/
│       └── ...

frontend/
├── src/
│   ├── __tests__/
│   │   ├── services/
│   │   │   ├── customerQuoteService.test.ts
│   │   │   └── quoteService.test.ts
│   │   ├── context/
│   │   │   └── CustomerQuoteContext.test.tsx
│   │   ├── components/
│   │   │   └── ...
│   │   └── utils/
│   │       └── ...
```

---

## 2. Tests Backend

### 2.1 PricingService

**Fichier** : `tests/unit/services/test_pricing_service.py`

#### TU-PRICING-001 : Calcul du prix de vente

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-PRICING-001-01 | Marge 20% sur coût 100€ | cost=100, margin=20 | sell_price=120.00 |
| TU-PRICING-001-02 | Marge 0% | cost=100, margin=0 | sell_price=100.00 |
| TU-PRICING-001-03 | Marge 100% | cost=50, margin=100 | sell_price=100.00 |
| TU-PRICING-001-04 | Marge négative -10% | cost=100, margin=-10 | sell_price=90.00 |
| TU-PRICING-001-05 | Coût avec décimales | cost=99.99, margin=20 | sell_price=119.99 |
| TU-PRICING-001-06 | Arrondi au centime | cost=33.33, margin=33.33 | sell_price=44.44 |

```python
class TestPricingServiceCalculateSellPrice:
    def test_with_20_percent_margin(self):
        result = PricingService.calculate_sell_price(
            Decimal("100"), Decimal("20")
        )
        assert result == Decimal("120.00")

    def test_with_zero_margin(self):
        result = PricingService.calculate_sell_price(
            Decimal("100"), Decimal("0")
        )
        assert result == Decimal("100.00")

    def test_with_negative_margin(self):
        result = PricingService.calculate_sell_price(
            Decimal("100"), Decimal("-10")
        )
        assert result == Decimal("90.00")

    def test_rounds_to_two_decimals(self):
        result = PricingService.calculate_sell_price(
            Decimal("33.33"), Decimal("33.33")
        )
        assert result == Decimal("44.44")
```

#### TU-PRICING-002 : Calcul du pourcentage de marge

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-PRICING-002-01 | Marge standard | cost=100, sell=120 | margin=20.00% |
| TU-PRICING-002-02 | Coût zéro (frais) | cost=0, sell=50 | margin=100.00% |
| TU-PRICING-002-03 | Prix de vente = coût | cost=100, sell=100 | margin=0.00% |
| TU-PRICING-002-04 | Marge négative | cost=100, sell=90 | margin=-10.00% |

```python
class TestPricingServiceCalculateMarginPercent:
    def test_standard_margin(self):
        result = PricingService.calculate_margin_percent(
            Decimal("100"), Decimal("120")
        )
        assert result == Decimal("20.00")

    def test_zero_cost_returns_100_percent(self):
        result = PricingService.calculate_margin_percent(
            Decimal("0"), Decimal("50")
        )
        assert result == Decimal("100.00")
```

#### TU-PRICING-003 : Calcul du montant de marge

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-PRICING-003-01 | Calcul standard | cost=100, sell=120 | amount=20.00 |
| TU-PRICING-003-02 | Frais (coût 0) | cost=0, sell=50 | amount=50.00 |
| TU-PRICING-003-03 | Marge négative | cost=100, sell=90 | amount=-10.00 |

---

### 2.2 MatchingService

**Fichier** : `tests/unit/services/test_matching_service.py`

#### TU-MATCH-001 : Calcul du prix selon pricing_type

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-MATCH-001-01 | PER_100KG - 250kg | cost=17, weight=250, type=PER_100KG | 51.00 (17×3) |
| TU-MATCH-001-02 | PER_100KG - 100kg exact | cost=17, weight=100, type=PER_100KG | 17.00 |
| TU-MATCH-001-03 | PER_100KG - 101kg | cost=17, weight=101, type=PER_100KG | 34.00 (arrondi 200kg) |
| TU-MATCH-001-04 | PER_KG | cost=0.50, weight=250, type=PER_KG | 125.00 |
| TU-MATCH-001-05 | LUMPSUM | cost=150, weight=500, type=LUMPSUM | 150.00 |
| TU-MATCH-001-06 | PER_PALLET | cost=25, pallets=4, type=PER_PALLET | 100.00 |

```python
class TestMatchingServiceCalculatePrice:
    def test_per_100kg_rounds_up(self):
        quote = PartnerQuote(cost=17, pricing_type="PER_100KG")
        result = MatchingService._calculate_price(quote, weight=250)
        assert result == Decimal("51.00")  # 17 × ceil(250/100) = 17 × 3

    def test_per_100kg_exact_100(self):
        quote = PartnerQuote(cost=17, pricing_type="PER_100KG")
        result = MatchingService._calculate_price(quote, weight=100)
        assert result == Decimal("17.00")

    def test_per_100kg_rounds_101_to_200(self):
        quote = PartnerQuote(cost=17, pricing_type="PER_100KG")
        result = MatchingService._calculate_price(quote, weight=101)
        assert result == Decimal("34.00")

    def test_lumpsum_ignores_weight(self):
        quote = PartnerQuote(cost=150, pricing_type="LUMPSUM")
        result = MatchingService._calculate_price(quote, weight=500)
        assert result == Decimal("150.00")
```

#### TU-MATCH-002 : Filtrage par critères

| ID | Cas de test | Critères | Données | Résultat attendu |
|----|-------------|----------|---------|------------------|
| TU-MATCH-002-01 | Filtre pays | FR→FR | Mix FR/DE | Seulement FR→FR |
| TU-MATCH-002-02 | Filtre département | dest=69 | 69, 75, 13 | Seulement 69 |
| TU-MATCH-002-03 | Filtre poids | weight=500 | 0-300, 300-600 | Seulement 300-600 |
| TU-MATCH-002-04 | Filtre validité | date=today | expired, valid | Seulement valid |
| TU-MATCH-002-05 | Partenaire inactif | - | actif, inactif | Seulement actif |
| TU-MATCH-002-06 | Aucun résultat | dest=99 | 69, 75, 13 | Liste vide |

```python
class TestMatchingServiceFilters:
    def test_filters_by_country(self, db_session, sample_quotes):
        criteria = SearchCriteria(
            origin_country="FR",
            dest_country="FR",
            weight=500
        )
        results = MatchingService.find_quotes(db_session, criteria)
        assert all(q.origin_country == "FR" for q in results)
        assert all(q.dest_country == "FR" for q in results)

    def test_filters_by_postal_code_prefix(self, db_session, sample_quotes):
        criteria = SearchCriteria(
            origin_country="FR",
            dest_country="FR",
            dest_postal_code="69",
            weight=500
        )
        results = MatchingService.find_quotes(db_session, criteria)
        assert all(q.dest_postal_code.startswith("69") for q in results)

    def test_excludes_inactive_partners(self, db_session, inactive_partner_quotes):
        criteria = SearchCriteria(origin_country="FR", dest_country="FR", weight=500)
        results = MatchingService.find_quotes(db_session, criteria)
        assert len(results) == 0
```

#### TU-MATCH-003 : Tri des résultats

| ID | Cas de test | Données | Résultat attendu |
|----|-------------|---------|------------------|
| TU-MATCH-003-01 | Tri par prix croissant | [150, 100, 200] | [100, 150, 200] |

---

### 2.3 CustomerQuoteService

**Fichier** : `tests/unit/services/test_customer_quote_service.py`

#### TU-CQ-001 : Création de devis

| ID | Cas de test | Contexte | Résultat attendu |
|----|-------------|----------|------------------|
| TU-CQ-001-01 | Première création 2024 | Aucun devis 2024 | REF = DEV-2024-0001 |
| TU-CQ-001-02 | Devis suivant | 5 devis existants | REF = DEV-2024-0006 |
| TU-CQ-001-03 | Nouvelle année | 10 devis 2023, 0 en 2024 | REF = DEV-2024-0001 |
| TU-CQ-001-04 | Statut initial | Création | status = DRAFT |

```python
class TestCustomerQuoteServiceCreate:
    def test_generates_reference_with_year(self, db_session):
        quote = CustomerQuoteService.create_quote(db_session)
        year = datetime.now().year
        assert quote.reference.startswith(f"DEV-{year}-")

    def test_increments_sequence(self, db_session, existing_quotes):
        # existing_quotes fixture crée 5 devis
        quote = CustomerQuoteService.create_quote(db_session)
        assert quote.reference.endswith("-0006")

    def test_initial_status_is_draft(self, db_session):
        quote = CustomerQuoteService.create_quote(db_session)
        assert quote.status == QuoteStatus.DRAFT
```

#### TU-CQ-002 : Ajout de ligne transport

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-CQ-002-01 | Ajout standard | partner_quote + weight | Ligne créée avec snapshot |
| TU-CQ-002-02 | Marge par défaut | Partner margin=25% | margin_percent=25 |
| TU-CQ-002-03 | Calcul sell_price | cost=100, margin=20% | sell_price=120 |
| TU-CQ-002-04 | Snapshot origine | origin="Paris, FR" | snapshot_origin="Paris, FR" |
| TU-CQ-002-05 | Recalcul totaux | Ajout 2ème ligne | total = somme lignes |

```python
class TestCustomerQuoteServiceAddTransportItem:
    def test_creates_item_with_snapshot(self, db_session, quote, partner_quote):
        item = CustomerQuoteService.add_transport_item(
            db_session, quote.id, partner_quote.id, weight=500
        )
        assert item.snapshot_transport_mode == partner_quote.transport_mode
        assert item.snapshot_origin == f"{partner_quote.origin_city}, {partner_quote.origin_country}"

    def test_applies_partner_default_margin(self, db_session, quote, partner_quote):
        # partner.default_margin = 25
        item = CustomerQuoteService.add_transport_item(
            db_session, quote.id, partner_quote.id, weight=500
        )
        assert item.margin_percent == Decimal("25.00")

    def test_recalculates_quote_totals(self, db_session, quote, partner_quote):
        CustomerQuoteService.add_transport_item(
            db_session, quote.id, partner_quote.id, weight=500
        )
        db_session.refresh(quote)
        assert quote.transport_subtotal > 0
        assert quote.total == quote.transport_subtotal
```

#### TU-CQ-003 : Ajout de frais

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-CQ-003-01 | Frais standard | description, price=50 | cost=0, sell=50, margin=100% |
| TU-CQ-003-02 | Type FEE | - | type = ItemType.FEE |
| TU-CQ-003-03 | Recalcul fees_total | 2 frais de 50€ | fees_total = 100 |

```python
class TestCustomerQuoteServiceAddFee:
    def test_fee_has_zero_cost_and_100_margin(self, db_session, quote):
        item = CustomerQuoteService.add_fee_item(
            db_session, quote.id, "Manutention", price=50
        )
        assert item.cost_price == Decimal("0")
        assert item.sell_price == Decimal("50.00")
        assert item.margin_percent == Decimal("100.00")
        assert item.margin_amount == Decimal("50.00")

    def test_fee_type_is_fee(self, db_session, quote):
        item = CustomerQuoteService.add_fee_item(
            db_session, quote.id, "Manutention", price=50
        )
        assert item.type == ItemType.FEE
```

#### TU-CQ-004 : Modification de ligne

| ID | Cas de test | Modification | Résultat attendu |
|----|-------------|--------------|------------------|
| TU-CQ-004-01 | Modif sell_price | sell_price=150 | margin recalculée |
| TU-CQ-004-02 | Modif margin | margin=30% | sell_price recalculé |
| TU-CQ-004-03 | Modif les deux | sell+margin | sell_price prioritaire |
| TU-CQ-004-04 | Recalcul totaux | Après modif | Totaux mis à jour |

```python
class TestCustomerQuoteServiceUpdateItem:
    def test_update_sell_price_recalculates_margin(self, db_session, quote_with_item):
        item = quote_with_item.items[0]
        # cost_price = 100
        CustomerQuoteService.update_item(
            db_session, quote_with_item.id, item.id,
            {"sell_price": 150}
        )
        db_session.refresh(item)
        assert item.sell_price == Decimal("150.00")
        assert item.margin_percent == Decimal("50.00")

    def test_update_margin_recalculates_sell_price(self, db_session, quote_with_item):
        item = quote_with_item.items[0]
        # cost_price = 100
        CustomerQuoteService.update_item(
            db_session, quote_with_item.id, item.id,
            {"margin_percent": 30}
        )
        db_session.refresh(item)
        assert item.margin_percent == Decimal("30.00")
        assert item.sell_price == Decimal("130.00")
```

#### TU-CQ-005 : Suppression de ligne

| ID | Cas de test | Contexte | Résultat attendu |
|----|-------------|----------|------------------|
| TU-CQ-005-01 | Suppression | 2 lignes, suppr 1 | 1 ligne restante |
| TU-CQ-005-02 | Recalcul totaux | Après suppression | Totaux mis à jour |
| TU-CQ-005-03 | Position recalculée | Suppr ligne 0 | Ligne 1 devient 0 |

---

### 2.4 Import Logic

#### TU-MAPPER-001 : ColumnMapper - Layout FLAT

**Fichier** : `tests/unit/import_logic/test_column_mapper.py`

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-MAPPER-001-01 | Mapping standard | {"ville_depart": "Paris"} | {"origin_city": "Paris"} |
| TU-MAPPER-001-02 | Alias anglais | {"origin_city": "Paris"} | {"origin_city": "Paris"} |
| TU-MAPPER-001-03 | Colonne inconnue | {"unknown": "value"} | Ignorée |
| TU-MAPPER-001-04 | Valeurs par défaut | Row sans transport_mode | transport_mode = default |

```python
class TestColumnMapperFlat:
    def test_maps_french_aliases(self):
        mapper = ColumnMapper()
        row = {"ville_depart": "Paris", "prix": 100}
        result = mapper.map_row(row, partner_code=None)
        assert result[0]["origin_city"] == "Paris"
        assert result[0]["cost"] == 100

    def test_applies_defaults(self):
        mapper = ColumnMapper()
        row = {"origin_city": "Paris", "cost": 100}
        result = mapper.map_row(row, partner_code="BESSON")
        assert result[0]["transport_mode"] == "ROAD"
        assert result[0]["currency"] == "EUR"
```

#### TU-MAPPER-002 : ColumnMapper - Layout GRID

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-MAPPER-002-01 | Pivot colonnes poids | {"5 KG": 8.5, "10 KG": 12} | 2 lignes |
| TU-MAPPER-002-02 | Extraction weight_max | "5 KG" | weight_max = 5 |
| TU-MAPPER-002-03 | Calcul weight_min | gap=1, prev=5 | weight_min = 6 |
| TU-MAPPER-002-04 | Regex header | "5_kg", "5 KG", "5kg" | Tous reconnus |

```python
class TestColumnMapperGrid:
    def test_pivots_weight_columns(self):
        mapper = ColumnMapper()
        row = {"Agence": "NIC", "Département": "01", "5 KG": 8.5, "10 KG": 12.0}
        results = mapper.map_row(row, partner_code="BESSON")
        assert len(results) == 2
        assert results[0]["weight_max"] == 5
        assert results[0]["cost"] == 8.5
        assert results[1]["weight_max"] == 10
        assert results[1]["cost"] == 12.0

    def test_calculates_weight_min_with_gap(self):
        mapper = ColumnMapper()
        row = {"Agence": "NIC", "Département": "01", "5 KG": 8.5, "10 KG": 12.0}
        results = mapper.map_row(row, partner_code="BESSON")
        # weight_min_gap = 1
        assert results[0]["weight_min"] == 0
        assert results[0]["weight_max"] == 5
        assert results[1]["weight_min"] == 6  # 5 + 1
        assert results[1]["weight_max"] == 10
```

#### TU-MAPPER-003 : ColumnMapper - Layout DUAL_GRID

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-MAPPER-003-01 | Small weights | {"Minimum": 9.4, "100/300 kg": 5.7} | 2 lignes small |
| TU-MAPPER-003-02 | Large weights | {"1001/1500 kg": 4.95} | 1 ligne large |
| TU-MAPPER-003-03 | Pricing par section | small=PER_100KG, large=LUMPSUM | Correct par ligne |
| TU-MAPPER-003-04 | Delivery time | small=24h, large=24h | Correct par ligne |
| TU-MAPPER-003-05 | Cellule vide | {"1001/1500 kg": NaN} | Ligne ignorée |

```python
class TestColumnMapperDualGrid:
    def test_expands_both_sections(self):
        mapper = ColumnMapper()
        row = {
            "zip code": "06",
            "Minimum": 9.4,
            "100/300 kg": 5.7,
            "PRICING": "PRICE PER 100KGS",
            "1001/1500 kg": 4.95,
            "PRICING.1": "LUMPSUM FROM NICE"
        }
        results = mapper.map_row(row, partner_code="BIANCHI")
        assert len(results) == 3

    def test_assigns_correct_pricing_type(self):
        mapper = ColumnMapper()
        row = {
            "zip code": "06",
            "Minimum": 9.4,
            "PRICING": "PRICE PER 100KGS",
            "1001/1500 kg": 4.95,
            "PRICING.1": "LUMPSUM FROM NICE"
        }
        results = mapper.map_row(row, partner_code="BIANCHI")
        small = [r for r in results if r["weight_max"] <= 1000]
        large = [r for r in results if r["weight_min"] > 1000]
        assert all(r["pricing_type"] == "PER_100KG" for r in small)
        assert all(r["pricing_type"] == "LUMPSUM" for r in large)
```

#### TU-NORM-001 : DataNormalizer

**Fichier** : `tests/unit/import_logic/test_data_normalizer.py`

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-NORM-001-01 | Cost string → float | "15.50" | 15.5 |
| TU-NORM-001-02 | Cost avec virgule | "15,50" | 15.5 |
| TU-NORM-001-03 | Transport mode upper | "road" | "ROAD" |
| TU-NORM-001-04 | Postal code trim | "75001" | "75" |
| TU-NORM-001-05 | City uppercase | "paris" | "PARIS" |
| TU-NORM-001-06 | NaN → None | float('nan') | None |
| TU-NORM-001-07 | Whitespace trim | " Paris " | "PARIS" |

```python
class TestDataNormalizer:
    def test_converts_cost_string_to_float(self):
        normalizer = DataNormalizer()
        row = {"cost": "15.50"}
        result = normalizer.normalize_row(row)
        assert result["cost"] == 15.5

    def test_handles_comma_decimal(self):
        normalizer = DataNormalizer()
        row = {"cost": "15,50"}
        result = normalizer.normalize_row(row)
        assert result["cost"] == 15.5

    def test_truncates_postal_code_to_2_chars(self):
        normalizer = DataNormalizer()
        row = {"dest_postal_code": "75001"}
        result = normalizer.normalize_row(row)
        assert result["dest_postal_code"] == "75"
```

#### TU-VALID-001 : RowValidator

**Fichier** : `tests/unit/import_logic/test_row_validator.py`

| ID | Cas de test | Entrée | Résultat attendu |
|----|-------------|--------|------------------|
| TU-VALID-001-01 | Ligne valide | Tous champs requis | is_valid=True |
| TU-VALID-001-02 | Cost manquant | cost=None | is_valid=False |
| TU-VALID-001-03 | Cost négatif | cost=-10 | is_valid=False |
| TU-VALID-001-04 | Cost = 0 | cost=0 | is_valid=False |
| TU-VALID-001-05 | Country code 3 chars | origin_country="FRA" | is_valid=False |
| TU-VALID-001-06 | Transport mode invalide | transport_mode="BOAT" | is_valid=False |

```python
class TestRowValidator:
    def test_valid_row_passes(self):
        validator = RowValidator()
        row = {
            "transport_mode": "ROAD",
            "origin_city": "Paris",
            "origin_country": "FR",
            "dest_city": "Lyon",
            "dest_country": "FR",
            "cost": 100.0
        }
        result = validator.validate(row)
        assert result.is_valid is True

    def test_missing_cost_fails(self):
        validator = RowValidator()
        row = {
            "transport_mode": "ROAD",
            "origin_city": "Paris",
            "origin_country": "FR",
            "dest_city": "Lyon",
            "dest_country": "FR"
        }
        result = validator.validate(row)
        assert result.is_valid is False
        assert any(e.field == "cost" for e in result.errors)

    def test_negative_cost_fails(self):
        validator = RowValidator()
        row = {
            "transport_mode": "ROAD",
            "origin_city": "Paris",
            "origin_country": "FR",
            "dest_city": "Lyon",
            "dest_country": "FR",
            "cost": -10
        }
        result = validator.validate(row)
        assert result.is_valid is False
```

---

## 3. Tests Frontend

### 3.1 CustomerQuoteContext

**Fichier** : `src/__tests__/context/CustomerQuoteContext.test.tsx`

#### TU-CTX-001 : Gestion du state

| ID | Cas de test | Action | Résultat attendu |
|----|-------------|--------|------------------|
| TU-CTX-001-01 | Initial state | Render | currentQuote = null |
| TU-CTX-001-02 | createQuote | Call | currentQuote défini, API appelée |
| TU-CTX-001-03 | loadQuote | Call avec ID | Quote chargé depuis API |
| TU-CTX-001-04 | clearQuote | Call | currentQuote = null |
| TU-CTX-001-05 | Persistence localStorage | createQuote | ID sauvegardé |

```typescript
describe('CustomerQuoteContext', () => {
  it('starts with null quote', () => {
    const { result } = renderHook(() => useCustomerQuote(), {
      wrapper: CustomerQuoteProvider
    });
    expect(result.current.currentQuote).toBeNull();
  });

  it('creates quote and updates state', async () => {
    const mockQuote = { id: '123', reference: 'DEV-2024-0001' };
    vi.mocked(CustomerQuoteService.create).mockResolvedValue({ data: mockQuote });

    const { result } = renderHook(() => useCustomerQuote(), {
      wrapper: CustomerQuoteProvider
    });

    await act(async () => {
      await result.current.createQuote();
    });

    expect(result.current.currentQuote).toEqual(mockQuote);
  });

  it('persists quote ID to localStorage', async () => {
    const mockQuote = { id: '123', reference: 'DEV-2024-0001' };
    vi.mocked(CustomerQuoteService.create).mockResolvedValue({ data: mockQuote });

    const { result } = renderHook(() => useCustomerQuote(), {
      wrapper: CustomerQuoteProvider
    });

    await act(async () => {
      await result.current.createQuote();
    });

    expect(localStorage.getItem('transport_quote_current_quote_id')).toBe('123');
  });
});
```

#### TU-CTX-002 : Calculs computed

| ID | Cas de test | State | Résultat attendu |
|----|-------------|-------|------------------|
| TU-CTX-002-01 | subtotal | 2 items transport | Somme sell_price |
| TU-CTX-002-02 | totalFees | 2 items fee | Somme sell_price fees |
| TU-CTX-002-03 | grandTotal | transport + fees | subtotal + totalFees |
| TU-CTX-002-04 | totalMargin | items avec marges | Somme margin_amount |

```typescript
describe('CustomerQuoteContext computed values', () => {
  it('calculates subtotal from transport items', () => {
    const mockQuote = {
      id: '123',
      items: [
        { type: 'TRANSPORT', sell_price: 100 },
        { type: 'TRANSPORT', sell_price: 150 },
        { type: 'FEE', sell_price: 50 }
      ]
    };

    const { result } = renderHook(() => useCustomerQuote(), {
      wrapper: createWrapperWithQuote(mockQuote)
    });

    expect(result.current.subtotal).toBe(250);
    expect(result.current.totalFees).toBe(50);
    expect(result.current.grandTotal).toBe(300);
  });
});
```

### 3.2 Services API

**Fichier** : `src/__tests__/services/customerQuoteService.test.ts`

#### TU-SVC-001 : CustomerQuoteService

| ID | Cas de test | Méthode | Vérification |
|----|-------------|---------|--------------|
| TU-SVC-001-01 | create | create() | POST /customer-quotes/ |
| TU-SVC-001-02 | getById | getById('123') | GET /customer-quotes/123 |
| TU-SVC-001-03 | addItem | addTransportItem(...) | POST /customer-quotes/{id}/items |
| TU-SVC-001-04 | updateItem | updateItem(...) | PUT /customer-quotes/{id}/items/{itemId} |

```typescript
describe('CustomerQuoteService', () => {
  it('calls correct endpoint for create', async () => {
    const mockResponse = { data: { id: '123' } };
    vi.mocked(api.post).mockResolvedValue(mockResponse);

    await CustomerQuoteService.create();

    expect(api.post).toHaveBeenCalledWith('/customer-quotes/');
  });

  it('calls correct endpoint for addTransportItem', async () => {
    const mockResponse = { data: { id: 'item-1' } };
    vi.mocked(api.post).mockResolvedValue(mockResponse);

    await CustomerQuoteService.addTransportItem('quote-123', 'partner-quote-456', 500);

    expect(api.post).toHaveBeenCalledWith('/customer-quotes/quote-123/items', {
      partner_quote_id: 'partner-quote-456',
      weight: 500
    });
  });
});
```

---

## 4. Fixtures et Mocks

### 4.1 Fixtures Backend (conftest.py)

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

@pytest.fixture
def db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def sample_partner(db_session):
    partner = Partner(
        code="TEST",
        name="Test Partner",
        email="test@test.com",
        default_margin=20.00
    )
    db_session.add(partner)
    db_session.commit()
    return partner

@pytest.fixture
def sample_partner_quote(db_session, sample_partner):
    quote = PartnerQuote(
        partner_id=sample_partner.id,
        transport_mode=TransportMode.ROAD,
        origin_city="PARIS",
        origin_country="FR",
        dest_city="LYON",
        dest_country="FR",
        dest_postal_code="69",
        weight_min=0,
        weight_max=1000,
        cost=100.00,
        pricing_type="PER_100KG"
    )
    db_session.add(quote)
    db_session.commit()
    return quote

@pytest.fixture
def sample_customer_quote(db_session):
    quote = CustomerQuote(reference="DEV-2024-0001")
    db_session.add(quote)
    db_session.commit()
    return quote
```

### 4.2 Mocks Frontend

```typescript
// src/__tests__/mocks/handlers.ts
import { rest } from 'msw';

export const handlers = [
  rest.post('/api/v1/customer-quotes/', (req, res, ctx) => {
    return res(
      ctx.json({
        id: 'mock-id',
        reference: 'DEV-2024-0001',
        status: 'DRAFT',
        items: []
      })
    );
  }),

  rest.get('/api/v1/customer-quotes/:id', (req, res, ctx) => {
    return res(
      ctx.json({
        id: req.params.id,
        reference: 'DEV-2024-0001',
        status: 'DRAFT',
        items: []
      })
    );
  })
];
```

---

## 5. Couverture de code

### 5.1 Objectifs de couverture

| Module | Couverture cible |
|--------|------------------|
| Services métier | 90% |
| Import logic | 85% |
| API routes | 80% |
| Models | 70% |
| Frontend context | 85% |
| Frontend services | 80% |

### 5.2 Configuration pytest-cov

```ini
# pytest.ini
[pytest]
addopts = --cov=app --cov-report=html --cov-report=term-missing
testpaths = tests

[coverage:run]
omit =
    */migrations/*
    */tests/*
    */__init__.py
```

### 5.3 Commandes d'exécution

```bash
# Backend - tous les tests
pytest

# Backend - avec couverture
pytest --cov=app --cov-report=html

# Backend - tests unitaires uniquement
pytest tests/unit/

# Frontend - tous les tests
npm test

# Frontend - avec couverture
npm test -- --coverage

# Frontend - watch mode
npm test -- --watch
```

---

## 6. Matrice de traçabilité

| Exigence | Tests unitaires |
|----------|-----------------|
| Calcul prix PER_100KG | TU-MATCH-001-01 à 03 |
| Calcul prix LUMPSUM | TU-MATCH-001-05 |
| Génération référence devis | TU-CQ-001-01 à 03 |
| Application marge par défaut | TU-CQ-002-02 |
| Recalcul totaux | TU-CQ-002-05, TU-CQ-004-04 |
| Import format GRID | TU-MAPPER-002-01 à 04 |
| Import format DUAL_GRID | TU-MAPPER-003-01 à 05 |
| Validation coût positif | TU-VALID-001-03 à 04 |
