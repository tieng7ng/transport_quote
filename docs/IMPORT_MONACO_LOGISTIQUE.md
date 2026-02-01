# Documentation Import MONACO LOGISTIQUE

## Partie 1 : Documentation Fonctionnelle

---

### 1.1 Contexte et objectif

#### Besoin métier
Monaco Logistique est un partenaire transport qui propose des tarifs de distribution depuis Nice vers différents départements français, ainsi que des tarifs internationaux depuis leur terminal de Melzo (Italie).

#### Objectif
Importer automatiquement les grilles tarifaires du fichier Excel fourni par Monaco Logistique dans l'application de gestion des devis transport.

#### Fichier source
- **Nom** : `PROTOCOLLO NT-MonacoLogistique Ott 2020 - agg.to 01.01.2023.xlsx`
- **Période de validité** : 01/01/2023 - 31/12/2023
- **Devise** : EUR

---

### 1.2 Périmètre fonctionnel

#### Phase 1 (MVP) : Tarifs France
Import des tarifs de distribution France depuis Nice.

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `1-Tarifs MonacoLog` |
| Origine | Nice (06000), France |
| Destinations | 8 départements français |
| Mode transport | Route (ROAD) |

#### Phase 2 (Future) : Tarifs internationaux
Import des tarifs depuis Melzo vers l'Europe.

| Pays | Feuille Excel |
|------|---------------|
| Slovénie | 3.rates SI |
| Serbie | 4.rates XS |
| Croatie | 5.rates HR |
| Portugal | 6.rates PT |
| Grèce | 7-rates GR-ADReNON |

---

### 1.3 Données importées

#### 1.3.1 Départements couverts

| Code Excel | Code normalisé | Département | Délai transit |
|------------|----------------|-------------|---------------|
| 06 | 06 | Alpes-Maritimes | 24h |
| 98 | 98000 | Monaco | 24h |
| 13 | 13 | Bouches-du-Rhône | 24/48h |
| 20 (1) | 2A | Corse-du-Sud (Ajaccio, Bastia) | 72/96h |
| 20 (2) | 2B | Haute-Corse (autres) | 72/96h |
| 30 | 30 | Gard | 48h |
| 34 | 34 | Hérault | 48h |
| 83 | 83 | Var | 24/48h |
| 84 | 84 | Vaucluse | 24/48h |

#### 1.3.2 Grille tarifaire

**Structure à double matrice** : Le fichier contient deux sections côte à côte.

**Section 1 - Petits poids (tarif au 100 kg)**
| Tranche | Poids min | Poids max | Type tarif |
|---------|-----------|-----------|------------|
| Minimum | 0 kg | 99 kg | Prix au 100 kg |
| 100/300 kg | 100 kg | 300 kg | Prix au 100 kg |
| 301/500 kg | 301 kg | 500 kg | Prix au 100 kg |
| 501/1000 kg | 501 kg | 1000 kg | Prix au 100 kg |

**Section 2 - Gros poids (forfait)**
| Tranche | Poids min | Poids max | Type tarif |
|---------|-----------|-----------|------------|
| 1001/1500 kg | 1001 kg | 1500 kg | Forfait |
| 1501/2000 kg | 1501 kg | 2000 kg | Forfait |
| 2001/3000 kg | 2001 kg | 3000 kg | Forfait |
| 3001/4000 kg | 3001 kg | 4000 kg | Forfait |
| 4001/5000 kg | 4001 kg | 5000 kg | Forfait |

#### 1.3.3 Types de tarification

| Type | Code système | Règle de calcul |
|------|--------------|-----------------|
| Prix au 100 kg | `PER_100KG` | Prix × (poids arrondi au 100 kg supérieur / 100) |
| Forfait | `LUMPSUM` | Prix fixe quelle que soit la quantité dans la tranche |

**Exemple de calcul PER_100KG** :
- Envoi de 250 kg vers département 13
- Prix unitaire : 17€/100kg
- Poids arrondi : 300 kg (arrondi au 100 supérieur)
- **Prix final : 17 × 3 = 51€**

---

### 1.4 Règles métier

#### 1.4.1 Calcul du poids taxable
```
Poids taxable = MAX(poids réel, poids volumétrique)

Équivalences :
- 1 m³ = 250 kg
- 1 mètre linéaire (ldm) = 1600 kg
```

#### 1.4.2 Surcharges applicables (hors import)

Ces surcharges ne sont **pas incluses** dans les prix importés et doivent être gérées manuellement :

| Surcharge | Montant | Condition |
|-----------|---------|-----------|
| Fuel surcharge | +8% | Toujours applicable |
| COD | 15€ | Contre-remboursement |
| Dédouanement import | 50€ | Jusqu'à 3 codes HS |
| Booking | 8€ | Par envoi |
| Pick-up/delivery Italie | 60€ | Dans 50km de Melzo |
| Hayon | 35€ | Par envoi (sauf Lombardie) |

#### 1.4.3 Surcharges longueur

| Longueur | Surcharge standard | Surcharge Corse |
|----------|-------------------|-----------------|
| 3 - 5 m | +50% | +200% |
| 5 - 6 m | +100% | +200% |
| > 6 m | Sur demande | Sur demande |

**Exception** : Pas de surcharge longueur pour les départements 06 et 98.

#### 1.4.4 Zones exclues

Les tarifs ne sont **pas valides** pour :
- Zones de montagne
- Stations de ski
- Zones rurales isolées

Majoration possible pour :
- Centres-villes
- Chantiers de construction
- Livraisons aux particuliers

---

### 1.5 Cas d'utilisation

#### UC1 : Recherche de tarif standard

**Acteur** : Utilisateur commercial

**Scénario** :
1. L'utilisateur recherche un tarif Nice → Marseille (13) pour 500 kg
2. Le système trouve le tarif dans la tranche 301-500 kg
3. Le système affiche : 15€/100kg, type PER_100KG, délai 24/48h
4. L'utilisateur peut ajouter ce tarif à un devis

#### UC2 : Recherche tarif Corse

**Acteur** : Utilisateur commercial

**Scénario** :
1. L'utilisateur recherche un tarif Nice → Ajaccio (2A) pour 800 kg
2. Le système trouve le tarif dans la tranche 501-1000 kg
3. Le système affiche : 45€/100kg, type PER_100KG, délai 72/96h
4. Le système peut afficher une alerte : "Zone Corse - vérifier surcharges applicables"

#### UC3 : Aucun tarif trouvé

**Acteur** : Utilisateur commercial

**Scénario** :
1. L'utilisateur recherche un tarif Nice → Toulouse (31) pour 500 kg
2. Le département 31 n'est pas couvert par Monaco Logistique
3. Le système n'affiche pas de résultat pour ce partenaire
4. D'autres partenaires (BIANCHI, etc.) peuvent proposer des tarifs

---

## Partie 2 : Documentation Technique

---

### 2.1 Architecture de l'import

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Import Pipeline                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌────────────┐    ┌─────────┐ │
│  │  Excel   │───▶│ ExcelParser  │───▶│ColumnMapper│───▶│Validator│ │
│  │  File    │    │              │    │ (dual_grid)│    │         │ │
│  └──────────┘    └──────────────┘    └────────────┘    └────┬────┘ │
│                                                              │      │
│                                                              ▼      │
│                                                        ┌─────────┐  │
│                                                        │   DB    │  │
│                                                        │ partner │  │
│                                                        │ _quotes │  │
│                                                        └─────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Configuration YAML

Fichier : `backend/configs/partner_mapping.yaml`

```yaml
MONACO_LOG:
  layout: "dual_grid"
  header_row: 15
  sheet_name: "1-Tarifs MonacoLog"

  columns:
    dest_postal_code: "zip code"
    pricing_type_small: "PRICING"
    delivery_time_small: "T/T from Nice **"
    pricing_type_large: "PRICING.1"
    delivery_time_large: "T/T from Nice **.1"

  defaults:
    transport_mode: "ROAD"
    origin_country: "FR"
    origin_city: "NICE"
    origin_postal_code: "06000"
    dest_country: "FR"
    dest_city: "ALL"
    currency: "EUR"

  transforms:
    dest_postal_code:
      "20 (1)": "2A"
      "20 (2)": "2B"
      "98": "98000"
    pricing_type:
      "PRICE PER 100KGS": "PER_100KG"
      "LUMPSUM FROM NICE": "LUMPSUM"

  dual_grid:
    small_weights:
      columns:
        "Minimum": { weight_min: 0, weight_max: 99 }
        "100/300 kg": { weight_min: 100, weight_max: 300 }
        "301/500kg": { weight_min: 301, weight_max: 500 }
        "501/1000 kg": { weight_min: 501, weight_max: 1000 }
      pricing_col: "pricing_type_small"
      delivery_time_col: "delivery_time_small"

    large_weights:
      columns:
        "1001/1500 kg": { weight_min: 1001, weight_max: 1500 }
        "1501/2000 kg": { weight_min: 1501, weight_max: 2000 }
        "2001/3000 kg": { weight_min: 2001, weight_max: 3000 }
        "3001/4000 kg": { weight_min: 3001, weight_max: 4000 }
        "4001/5000 kg": { weight_min: 4001, weight_max: 5000 }
      pricing_col: "pricing_type_large"
      delivery_time_col: "delivery_time_large"
```

### 2.3 Modèle de données

#### Table `partners`

```sql
INSERT INTO partners (id, code, name, email, is_active)
VALUES (
  uuid_generate_v4(),
  'MONACO_LOG',
  'Monaco Logistique',
  'transports@monacologistique.mc',
  true
);
```

#### Table `partner_quotes`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID | Clé primaire |
| partner_id | UUID | FK vers partners |
| transport_mode | ENUM | ROAD |
| origin_city | VARCHAR | NICE |
| origin_country | VARCHAR(2) | FR |
| origin_postal_code | VARCHAR | 06000 |
| dest_city | VARCHAR | ALL |
| dest_country | VARCHAR(2) | FR |
| dest_postal_code | VARCHAR | Code département |
| weight_min | FLOAT | Poids minimum de la tranche |
| weight_max | FLOAT | Poids maximum de la tranche |
| cost | FLOAT | Prix (au 100kg ou forfait) |
| pricing_type | VARCHAR | PER_100KG ou LUMPSUM |
| currency | VARCHAR(3) | EUR |
| delivery_time | VARCHAR | Ex: "24/48h" |

### 2.4 Flux de données

#### 2.4.1 Parsing Excel

```python
# ExcelParser avec config spécifique
parser_config = {
    "sheet_name": "1-Tarifs MonacoLog",
    "header_row": 15
}
raw_data = parser.parse(file_path, **parser_config)
```

**Sortie** : Liste de dictionnaires (1 par ligne Excel)

```python
[
    {
        "zip code": "06",
        "Minimum": 9.4,
        "100/300 kg": 5.7,
        "301/500kg": 5.5,
        "501/1000 kg": 5.13,
        "PRICING": "PRICE PER 100KGS",
        "T/T from Nice **": "24h",
        "zip code.1": "06",  # Colonne dupliquée
        "1001/1500 kg": 4.95,
        ...
    },
    ...
]
```

#### 2.4.2 Mapping dual_grid

Le `ColumnMapper` transforme chaque ligne en **9 enregistrements** (1 par tranche de poids).

```python
# Entrée : 1 ligne Excel
row = {"zip code": "13", "Minimum": 21, "100/300 kg": 17, ...}

# Sortie : 9 lignes normalisées
[
    {"dest_postal_code": "13", "weight_min": 0, "weight_max": 99, "cost": 21, "pricing_type": "PER_100KG", ...},
    {"dest_postal_code": "13", "weight_min": 100, "weight_max": 300, "cost": 17, "pricing_type": "PER_100KG", ...},
    ...
    {"dest_postal_code": "13", "weight_min": 4001, "weight_max": 5000, "cost": 210, "pricing_type": "LUMPSUM", ...},
]
```

#### 2.4.3 Transformations

```python
# Transformation dest_postal_code
"20 (1)" → "2A"
"20 (2)" → "2B"
"98"     → "98000"

# Transformation pricing_type
"PRICE PER 100KGS"  → "PER_100KG"
"LUMPSUM FROM NICE" → "LUMPSUM"
```

### 2.5 Algorithme de recherche

#### Requête SQL pour recherche de tarif

```sql
SELECT pq.*, p.name as partner_name
FROM partner_quotes pq
JOIN partners p ON pq.partner_id = p.id
WHERE p.code = 'MONACO_LOG'
  AND pq.origin_country = 'FR'
  AND pq.dest_country = 'FR'
  AND pq.dest_postal_code LIKE :dest_dept || '%'  -- Match département
  AND pq.weight_min <= :weight
  AND pq.weight_max >= :weight
ORDER BY pq.cost ASC;
```

#### Calcul du prix final (application)

```python
def calculate_final_price(quote, actual_weight):
    if quote.pricing_type == "LUMPSUM":
        return quote.cost
    elif quote.pricing_type == "PER_100KG":
        # Arrondi au 100 kg supérieur
        rounded_weight = math.ceil(actual_weight / 100) * 100
        return quote.cost * (rounded_weight / 100)
```

### 2.6 Validation des données

#### Schéma Pydantic

```python
class QuoteImportSchema(BaseModel):
    transport_mode: TransportMode
    origin_city: str
    origin_country: str  # 2 caractères
    dest_city: str
    dest_country: str    # 2 caractères
    cost: float          # > 0
    pricing_type: str = "PER_100KG"
    currency: str = "EUR"

    # Optionnels
    origin_postal_code: Optional[str] = None
    dest_postal_code: Optional[str] = None
    weight_min: Optional[float] = None
    weight_max: Optional[float] = None
    delivery_time: Optional[str] = None
```

#### Règles de validation

| Champ | Règle |
|-------|-------|
| cost | Doit être > 0, ignorer les cellules vides/NaN |
| dest_postal_code | Après transformation (2A, 2B, 98000) |
| pricing_type | Doit être PER_100KG ou LUMPSUM |
| weight_min/max | weight_min < weight_max |

### 2.7 Gestion des erreurs

#### Cas d'erreur gérés

| Erreur | Traitement |
|--------|------------|
| Cellule vide (NaN) | Ignorer la ligne pour cette tranche |
| Ligne Monaco (98) vide | Ignorer (pas de tarif disponible) |
| pricing_type inconnu | Erreur de validation, ligne rejetée |
| cost = 0 ou négatif | Erreur de validation, ligne rejetée |

#### Logging

```python
# Log en cas d'erreur
{
    "row": 17,
    "errors": [{"field": "cost", "message": "Value required", "value": null}],
    "raw": {"zip code": "98", "Minimum": NaN, ...}
}
```

### 2.8 Tests

#### Données de test attendues

```python
# Test import Monaco Logistique
def test_monaco_log_import():
    # Après import, vérifier le nombre de lignes
    # 8 départements × 9 tranches = 72 max
    # Moins les cellules vides (Monaco 98)

    quotes = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="MONACO_LOG")
    ).all()

    assert len(quotes) >= 63  # Minimum attendu
    assert len(quotes) <= 72  # Maximum théorique

    # Vérifier un tarif spécifique
    quote_13 = db.query(PartnerQuote).filter(
        PartnerQuote.dest_postal_code == "13",
        PartnerQuote.weight_min == 100,
        PartnerQuote.weight_max == 300
    ).first()

    assert quote_13.cost == 17
    assert quote_13.pricing_type == "PER_100KG"
    assert quote_13.delivery_time == "24/48h"
```

### 2.9 Checklist d'implémentation

#### Backend

- [ ] Créer le partenaire `MONACO_LOG` dans la table `partners`
- [ ] Ajouter la configuration dans `partner_mapping.yaml`
- [ ] Vérifier que `dual_grid` gère le `pricing_type` variable par ligne
- [ ] Ajouter les transformations de codes postaux Corse
- [ ] Tester l'import via l'API

#### Frontend

- [ ] Afficher le `pricing_type` dans les résultats de recherche
- [ ] Implémenter le calcul du prix final selon le `pricing_type`
- [ ] Afficher une note pour les zones Corse (délais plus longs)

#### Tests

- [ ] Test unitaire du mapping dual_grid
- [ ] Test d'intégration de l'import complet
- [ ] Test de recherche avec calcul de prix

---

## Annexes

### A. Mapping visuel du fichier Excel

```
Ligne 15 (header):
┌────────┬─────────┬──────────┬──────────┬───────────┬─────────┬─────────┬───┬────────┬───────────┬───────────┬...
│zip code│ Minimum │100/300 kg│301/500kg │501/1000 kg│ PRICING │T/T Nice │   │zip code│1001/1500kg│1501/2000kg│
└────────┴─────────┴──────────┴──────────┴───────────┴─────────┴─────────┴───┴────────┴───────────┴───────────┴...
   Col 0     Col 1      Col 2      Col 3       Col 4      Col 5     Col 6  Col7  Col 8     Col 9      Col 10

Ligne 16 (données):
┌────────┬─────────┬──────────┬──────────┬───────────┬─────────────────┬─────┬───┬────────┬───────────┬...
│   06   │   9.4   │   5.7    │   5.5    │   5.13    │PRICE PER 100KGS │ 24h │   │   06   │   4.95    │
└────────┴─────────┴──────────┴──────────┴───────────┴─────────────────┴─────┴───┴────────┴───────────┴...
```

### B. Comparaison des partenaires

| Critère | BIANCHI | MONACO_LOG |
|---------|---------|------------|
| Layout | dual_grid | dual_grid |
| Origine | Nice | Nice |
| Départements | ~96 | 8 |
| Tranches poids | 9 | 9 |
| pricing_type | Variable | Variable |
| Zones exclues | Liste détaillée | Mention générique |
| Tarifs internationaux | Non | Oui (Phase 2) |
| Fuel surcharge | Inclus | +8% séparé |

### C. Contacts Monaco Logistique

| Fonction | Contact | Email |
|----------|---------|-------|
| Road Operations Manager | Emma Calestrini | e.calestrini@monacologistique.mc |
| Demandes de prix | Christophe Bayle | c.bayle@monacologistique.mc |
| Opérations | - | transports@monacologistique.mc |
