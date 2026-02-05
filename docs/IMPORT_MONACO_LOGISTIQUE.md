# Documentation Import MONACO LOGISTIQUE

## Vue d'ensemble

### Contexte et objectif

#### Besoin métier
Monaco Logistique est un partenaire transport qui propose :
- Des tarifs de distribution depuis Nice vers différents départements français
- Des tarifs de distribution Italie depuis leur terminal de Melzo
- Des tarifs internationaux depuis Melzo vers l'Europe

#### Objectif
Importer automatiquement les grilles tarifaires du fichier Excel fourni par Monaco Logistique dans l'application de gestion des devis transport.

#### Fichier source
- **Nom** : `PROTOCOLLO NT-MonacoLogistique Ott 2020 - agg.to 01.01.2023.xlsx`
- **Période de validité** : 01/01/2023 - 31/12/2023
- **Devise** : EUR

### Structure du fichier Excel

| # | Feuille | Description | Statut |
|---|---------|-------------|--------|
| 1 | COVER SHEET | Page de garde | Non importée |
| 2 | 1-Tarifs MonacoLog | Tarifs France depuis Nice | ✅ Phase 1 |
| 3 | 2.TARIFS NT | Tarifs Italie depuis Melzo | ✅ Phase 1 |
| 4 | 3.rates SI | Tarifs Slovénie | 📋 Phase 2 |
| 5 | 4.rates XS | Tarifs Serbie | 📋 Phase 2 |
| 6 | 5.rates HR | Tarifs Croatie | 📋 Phase 2 |
| 7 | 6.rates PT | Tarifs Portugal | 📋 Phase 2 |
| 8 | 7-rates GR-ADReNON | Tarifs Grèce | 📋 Phase 2 |
| 9 | 8.Contacts | Contacts Monaco Logistique | Non importée |

**Import unifié** : Un seul upload avec `partner_id = MONACO_LOG` traite automatiquement les feuilles 2 et 3 (France + Italie) grâce au layout `multi_sheet`.

---

## Feuille 1 : Tarifs France (1-Tarifs MonacoLog)

### 1.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `1-Tarifs MonacoLog` |
| Origine | Nice (06000), France |
| Destinations | 8 départements français |
| Mode transport | Route (ROAD) |

### 1.2 Départements couverts

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

### 1.3 Grille tarifaire

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

### 1.4 Types de tarification

| Type | Code système | Règle de calcul |
|------|--------------|-----------------|
| Prix au 100 kg | `PER_100KG` | Prix × (poids arrondi au 100 kg supérieur / 100) |
| Forfait | `LUMPSUM` | Prix fixe quelle que soit la quantité dans la tranche |

**Exemple de calcul PER_100KG** :
- Envoi de 250 kg vers département 13
- Prix unitaire : 17€/100kg
- Poids arrondi : 300 kg (arrondi au 100 supérieur)
- **Prix final : 17 × 3 = 51€**

### 1.5 Règles métier spécifiques

#### Calcul du poids taxable
```
Poids taxable = MAX(poids réel, poids volumétrique)

Équivalences :
- 1 m³ = 250 kg
- 1 mètre linéaire (ldm) = 1600 kg
```

#### Surcharges longueur

| Longueur | Surcharge standard | Surcharge Corse |
|----------|-------------------|-----------------|
| 3 - 5 m | +50% | +200% |
| 5 - 6 m | +100% | +200% |
| > 6 m | Sur demande | Sur demande |

**Exception** : Pas de surcharge longueur pour les départements 06 et 98.

#### Zones exclues

Les tarifs ne sont **pas valides** pour :
- Zones de montagne
- Stations de ski
- Zones rurales isolées

Majoration possible pour :
- Centres-villes
- Chantiers de construction
- Livraisons aux particuliers

### 1.6 Configuration technique

Voir la [configuration unifiée multi_sheet](#configuration-yaml-unifiée) dans la section Documentation Technique.

### 1.7 Mapping visuel

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

---

## Feuille 2 : Tarifs Italie (2.TARIFS NT)

### 2.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `2.TARIFS NT` |
| Origine | Melzo (Terminal), Italie |
| Destinations | 107 provinces italiennes |
| Mode transport | Route (ROAD) |

### 2.2 Provinces couvertes

Les tarifs couvrent **toutes les provinces italiennes**, organisées par région :

| Région | Provinces (codes) |
|--------|-------------------|
| Lazio | 00 Roma, 01 Viterbo, 02 Rieti, 03 Frosinone, 04 Latina |
| Umbria | 05 Terni, 06 Perugia |
| Sardegna | 07 Sassari, 08 Nuoro, 08 Olbia, 08 Ogliastra, 09 Oristano, 09 Cagliari, 09 Carbonia Iglesias, 09 Medio Campidano |
| Piemonte | 10 Torino, 11 Aosta, 12 Cuneo, 13 Biella, 13 Vercelli, 14 Asti, 15 Alessandria |
| Liguria | 16 Genova, 17 Savona, 18 Imperia, 19 La Spezia |
| Lombardia | 20 Milano/Monza Brianza, 21 Varese, 22 Como, 23 Lecco, 23 Sondrio, 24 Bergamo, 25 Brescia, 26 Cremona/Lodi, 27 Pavia, 28 Novara/Verbania, 29 Piacenza |
| Veneto | 30 Venezia, 31 Treviso, 32 Belluno, 35 Padova, 36 Vicenza, 37 Verona |
| Friuli-Venezia Giulia | 33 Udine, 33 Pordenone, 34 Trieste, 34 Gorizia |
| Trentino-Alto Adige | 38 Trento, 39 Bolzano |
| Emilia-Romagna | 40 Bologna, 41 Modena, 42 Reggio Emilia, 43 Parma, 44 Ferrara, 45 Rovigo, 46 Mantova, 47 Rimini, 47 Forlì Cesena, 48 Ravenna |
| Toscana | 50 Firenze, 51 Pistoia, 52 Arezzo, 53 Siena, 54 Carrara, 55 Lucca, 56 Pisa, 57 Livorno, 58 Grosseto, 59 Prato |
| Marche | 60 Ancona, 61 Pesaro Urbino, 62 Macerata, 63 Ascoli Piceno, 63 Fermo |
| Abruzzo | 64 Teramo, 65 Pescara, 66 Chieti, 67 L'Aquila |
| Puglia | 70 Bari, 71 Foggia, 72 Brindisi, 73 Lecce, 74 Taranto, 74 Barletta Andria Trani |
| Basilicata | 75 Matera, 85 Potenza |
| Campania | 80 Napoli, 81 Caserta, 82 Benevento, 83 Avellino, 84 Salerno |
| Molise | 86 Isernia, 86 Campobasso |
| Calabria | 87 Cosenza, 88 Catanzaro, 88 Crotone, 89 Reggio Calabria, 89 Vibo Valentia |
| Sicilia | 90 Palermo, 91 Trapani, 92 Agrigento, 93 Caltanissetta, 94 Enna, 95 Catania, 96 Siracusa, 97 Ragusa, 98 Messina |

**Note** : Venezia exclut les îles (no islands).

### 2.3 Grille tarifaire

**Structure à matrice simple** : 6 tranches de poids.

| Colonne | Tranche | Poids min | Poids max | Type tarif |
|---------|---------|-----------|-----------|------------|
| Minimum | Minimum | 0 kg | 99 kg | Forfait (€) |
| Till 500 kgs | 100-500 | 100 kg | 500 kg | Prix au 100 kg |
| 501 – 1000 | 501-1000 | 501 kg | 1000 kg | Prix au 100 kg |
| 1001 – 2000 | 1001-2000 | 1001 kg | 2000 kg | Prix au 100 kg |
| 2001 – 2500 | 2001-2500 | 2001 kg | 2500 kg | Prix au 100 kg |
| 2501 – 3000 | 2501-3000 | 2501 kg | 3000 kg | Prix au 100 kg |

**Note importante** : "Le minimum d'une tranche est le maximum de la tranche précédente" (THE MINIMUM OF ONE BRACKET IS THE MAXIMUM OF THE PREVIOUS ONE).

### 2.4 Règles métier spécifiques

#### Calcul du poids taxable
```
Poids taxable = MAX(poids réel, poids volumétrique)

Équivalences :
- 1 m³ = 300 kg
- 1 mètre linéaire (ldm) = 1650 kg
```

**Attention** : Les équivalences sont différentes de la feuille France !

#### Arrondi
- Arrondi au 100 kg supérieur (up to next 100 kgs)

#### Frais de manutention (Handling)
- **1,00 € / 100 kg** de poids réel
- Appliqué en plus du tarif de transport

#### Surcharges longueur

| Longueur | Surcharge |
|----------|-----------|
| 3 m à 5 m | +50% |
| 5,01 m à 6 m | +100% |
| > 6 m | Sur demande |

#### Hayon (Tail-lift)
- **35,00 € / envoi**
- **Lombardie** : inclus dans le tarif

#### Zones spéciales
Majoration à définir pour :
- Ports
- Aéroports
- Expositions
- Centres-villes
- Zones difficiles d'accès
- Grande distribution

#### ADR (matières dangereuses)
- **Inclus** dans les tarifs

#### Fuel surcharge
- **+8%** depuis le 01/12/2022

#### Conditions de paiement
- 60 jours fin de mois (facture mensuelle)

### 2.5 Exemples de tarifs

| Province | Minimum | Till 500 | 501-1000 | 1001-2000 | 2001-2500 | 2501-3000 |
|----------|---------|----------|----------|-----------|-----------|-----------|
| 20 Milano | 13€ | 7€ | 7€ | 6,50€ | 5€ | 5€ |
| 00 Roma | 19,50€ | 14,50€ | 14€ | 14€ | 13,50€ | 13€ |
| 90 Palermo | 19,50€ | 19€ | 18,50€ | 18€ | 17,50€ | 16,50€ |
| 95 Catania | 19€ | 18,50€ | 18€ | 18€ | 17€ | 16,50€ |

### 2.6 Configuration technique

Voir la [configuration unifiée multi_sheet](#configuration-yaml-unifiée) dans la section Documentation Technique.

### 2.7 Mapping visuel

```
Ligne 20-21 (headers):
┌──────────┬──────────────┬───────────┬──────────────────┬────────────┬─────────────┬─────────────┬─────────────┐
│PROVINCES │              │€ / forfait│€ / 100 kg taxable│            │             │             │             │
├──────────┼──────────────┼───────────┼──────────────────┼────────────┼─────────────┼─────────────┼─────────────┤
│          │              │  Minimum  │   Till 500 kgs   │ 501 – 1000 │ 1001 – 2000 │ 2001 – 2500 │ 2501 – 3000 │
└──────────┴──────────────┴───────────┴──────────────────┴────────────┴─────────────┴─────────────┴─────────────┘
   Col 0        Col 1         Col 2          Col 3           Col 4         Col 5         Col 6         Col 7

Ligne 22 (données):
┌──────────┬──────────────┬───────────┬──────────────────┬────────────┬─────────────┬─────────────┬─────────────┐
│          │   00 ROMA    │   19.5    │       14.5       │     14     │     14      │    13.5     │     13      │
└──────────┴──────────────┴───────────┴──────────────────┴────────────┴─────────────┴─────────────┴─────────────┘
```

---

## Feuilles 3-7 : Tarifs Internationaux (Phase 2)

### 3.1 Vue d'ensemble

Ces feuilles seront implémentées dans une phase ultérieure.

| Feuille | Pays | Origine | Statut |
|---------|------|---------|--------|
| 3.rates SI | Slovénie | Melzo | 📋 À faire |
| 4.rates XS | Serbie | Melzo | 📋 À faire |
| 5.rates HR | Croatie | Melzo | 📋 À faire |
| 6.rates PT | Portugal | Melzo | 📋 À faire |
| 7-rates GR-ADReNON | Grèce | Melzo | 📋 À faire |

### 3.2 Structure attendue

Les feuilles internationales suivent probablement une structure similaire à la feuille 2.TARIFS NT avec des destinations par ville/région du pays cible.

---

## Surcharges communes (hors import)

Ces surcharges ne sont **pas incluses** dans les prix importés et doivent être gérées séparément :

| Surcharge | Montant | Condition |
|-----------|---------|-----------|
| Fuel surcharge | +8% | Toujours applicable |
| COD (contre-remboursement) | 15€ | Si applicable |
| Dédouanement import | 50€ | Jusqu'à 3 codes HS |
| Booking | 8€ | Par envoi |
| Pick-up/delivery Italie | 60€ | Dans 50km de Melzo |
| Hayon | 35€ | Par envoi (Lombardie: inclus) |
| Handling | 1€/100kg | Poids réel (Italie uniquement) |

---

## Documentation Technique Commune

### Configuration YAML unifiée

Le partenaire `MONACO_LOG` utilise un layout `multi_sheet` qui traite plusieurs feuilles du même fichier Excel en un seul import :

```yaml
MONACO_LOG:
  layout: "multi_sheet"

  sheets:
    # ══════════════════════════════════════════════════════════════
    # Feuille 1 : Tarifs France (Nice → Départements FR)
    # ══════════════════════════════════════════════════════════════
    - name: "france"
      sheet_name: "1-Tarifs MonacoLog"
      header_row: 15
      layout: "dual_grid"

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

    # ══════════════════════════════════════════════════════════════
    # Feuille 2 : Tarifs Italie (Melzo → Provinces IT)
    # ══════════════════════════════════════════════════════════════
    - name: "italy"
      sheet_name: "2.TARIFS NT"
      header_row: 21
      layout: "single_grid"

      columns:
        dest_province: 1  # Colonne B (Province)
        minimum: 2        # Colonne C (Minimum - forfait)
        till_500: 3       # Colonne D (Till 500 kgs)
        w_501_1000: 4     # Colonne E (501-1000)
        w_1001_2000: 5    # Colonne F (1001-2000)
        w_2001_2500: 6    # Colonne G (2001-2500)
        w_2501_3000: 7    # Colonne H (2501-3000)

      defaults:
        transport_mode: "ROAD"
        origin_country: "IT"
        origin_city: "MELZO"
        origin_postal_code: "20066"
        dest_country: "IT"
        currency: "EUR"
        handling_per_100kg: 1.00
        fuel_surcharge_pct: 8

      transforms:
        dest_province:
          # Extraction du code postal depuis "XX PROVINCE_NAME"
          regex: "^(\\d+)\\s+(.+)$"
          postal_code: "$1"
          city: "$2"

      weight_brackets:
        - column: "minimum"
          weight_min: 0
          weight_max: 99
          pricing_type: "LUMPSUM"
        - column: "till_500"
          weight_min: 100
          weight_max: 500
          pricing_type: "PER_100KG"
        - column: "w_501_1000"
          weight_min: 501
          weight_max: 1000
          pricing_type: "PER_100KG"
        - column: "w_1001_2000"
          weight_min: 1001
          weight_max: 2000
          pricing_type: "PER_100KG"
        - column: "w_2001_2500"
          weight_min: 2001
          weight_max: 2500
          pricing_type: "PER_100KG"
        - column: "w_2501_3000"
          weight_min: 2501
          weight_max: 3000
          pricing_type: "PER_100KG"
```

### Modèle de données

#### Table `partners`

Un seul partenaire pour les deux feuilles (France et Italie) :

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

**Note** : Le même fichier Excel contient les tarifs France (feuille 1) et Italie (feuille 2). Un seul upload avec `partner_id = MONACO_LOG` traite les deux feuilles automatiquement.

#### Table `partner_quotes`

| Colonne | Type | Description |
|---------|------|-------------|
| id | UUID | Clé primaire |
| partner_id | UUID | FK vers partners |
| transport_mode | ENUM | ROAD |
| origin_city | VARCHAR | NICE ou MELZO |
| origin_country | VARCHAR(2) | FR ou IT |
| origin_postal_code | VARCHAR | 06000 ou 20066 |
| dest_city | VARCHAR | ALL ou nom de province |
| dest_country | VARCHAR(2) | FR ou IT |
| dest_postal_code | VARCHAR | Code département/province |
| weight_min | FLOAT | Poids minimum de la tranche |
| weight_max | FLOAT | Poids maximum de la tranche |
| cost | FLOAT | Prix (au 100kg ou forfait) |
| pricing_type | VARCHAR | PER_100KG ou LUMPSUM |
| currency | VARCHAR(3) | EUR |
| delivery_time | VARCHAR | Ex: "24/48h" |

### Algorithme de recherche

#### Requête SQL pour recherche de tarif

```sql
SELECT pq.*, p.name as partner_name
FROM partner_quotes pq
JOIN partners p ON pq.partner_id = p.id
WHERE p.code = 'MONACO_LOG'
  AND pq.origin_country = :origin_country
  AND pq.dest_country = :dest_country
  AND pq.dest_postal_code LIKE :dest_code || '%'
  AND pq.weight_min <= :weight
  AND pq.weight_max >= :weight
ORDER BY pq.cost ASC;
```

#### Calcul du prix final

```python
def calculate_final_price(quote, actual_weight, origin_country):
    base_price = 0

    if quote.pricing_type == "LUMPSUM":
        base_price = quote.cost
    elif quote.pricing_type == "PER_100KG":
        # Arrondi au 100 kg supérieur
        rounded_weight = math.ceil(actual_weight / 100) * 100
        base_price = quote.cost * (rounded_weight / 100)

    # Ajouter handling pour Italie
    if origin_country == "IT":
        handling = 1.00 * (rounded_weight / 100)
        base_price += handling

    # Appliquer fuel surcharge
    fuel_surcharge = base_price * 0.08

    return base_price + fuel_surcharge
```

### Validation des données

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
| dest_postal_code | Après transformation |
| pricing_type | Doit être PER_100KG ou LUMPSUM |
| weight_min/max | weight_min < weight_max |

### Tests

#### Test d'import complet (multi_sheet)

```python
def test_monaco_log_full_import():
    """Test import des deux feuilles en un seul upload."""

    # Upload du fichier avec partner_id = MONACO_LOG
    # Le système traite automatiquement les 2 feuilles

    all_quotes = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="MONACO_LOG")
    ).all()

    # France: 8 depts × 9 tranches = 72 max
    # Italie: 107 provinces × 6 tranches = 642 max
    # Total: ~714 quotes max
    assert len(all_quotes) >= 663  # Minimum attendu
    assert len(all_quotes) <= 714  # Maximum théorique
```

#### Test - Feuille France

```python
def test_monaco_log_france_quotes():
    """Vérifier les quotes France (origin_country = FR)."""

    quotes_fr = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="MONACO_LOG"),
        PartnerQuote.origin_country == "FR"
    ).all()

    assert len(quotes_fr) >= 63
    assert len(quotes_fr) <= 72

    # Vérifier origine Nice
    for q in quotes_fr:
        assert q.origin_city == "NICE"
        assert q.origin_postal_code == "06000"

    # Vérifier un tarif spécifique
    quote_13 = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="MONACO_LOG"),
        PartnerQuote.dest_postal_code == "13",
        PartnerQuote.weight_min == 100,
        PartnerQuote.weight_max == 300
    ).first()

    assert quote_13.cost == 17
    assert quote_13.pricing_type == "PER_100KG"
```

#### Test - Feuille Italie

```python
def test_monaco_log_italy_quotes():
    """Vérifier les quotes Italie (origin_country = IT)."""

    quotes_it = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="MONACO_LOG"),
        PartnerQuote.origin_country == "IT"
    ).all()

    assert len(quotes_it) >= 600
    assert len(quotes_it) <= 642

    # Vérifier origine Melzo
    for q in quotes_it:
        assert q.origin_city == "MELZO"
        assert q.origin_postal_code == "20066"

    # Vérifier un tarif spécifique - Milano
    quote_milano = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="MONACO_LOG"),
        PartnerQuote.dest_postal_code == "20",
        PartnerQuote.weight_min == 100,
        PartnerQuote.weight_max == 500
    ).first()

    assert quote_milano.cost == 7
    assert quote_milano.pricing_type == "PER_100KG"
```

---

## Checklist d'implémentation

### Backend - Partenaire et configuration

- [ ] Créer le partenaire `MONACO_LOG` dans la table `partners`
- [ ] Ajouter la configuration `MONACO_LOG` dans `partner_mapping.yaml`
- [ ] Implémenter le layout `multi_sheet` dans `column_mapper.py`
  - [ ] Itérer sur chaque feuille définie dans `sheets`
  - [ ] Appliquer le layout spécifique de chaque feuille (`dual_grid`, `single_grid`)
  - [ ] Fusionner les résultats de toutes les feuilles

### Backend - Feuille France

- [ ] Implémenter le layout `dual_grid` (si pas déjà fait)
- [ ] Ajouter les transformations de codes postaux Corse (2A, 2B, 98000)
- [ ] Tester l'import de la feuille "1-Tarifs MonacoLog"

### Backend - Feuille Italie

- [ ] Implémenter le layout `single_grid` avec parsing de province (regex)
- [ ] Gérer le handling de 1€/100kg dans les defaults
- [ ] Gérer l'exception Lombardie pour le hayon
- [ ] Tester l'import de la feuille "2.TARIFS NT"

### Frontend

- [ ] Afficher le `pricing_type` dans les résultats de recherche
- [ ] Implémenter le calcul du prix final selon le `pricing_type`
- [ ] Afficher le handling pour les tarifs Italie (origin_country = IT)
- [ ] Afficher une note pour les zones Corse (délais plus longs)
- [ ] Afficher une note pour Venezia (exclut îles)
- [ ] Différencier visuellement les tarifs France vs Italie (origin_country)

---

## Annexes

### A. Comparaison des paramètres France vs Italie

| Paramètre | France (Feuille 1) | Italie (Feuille 2) |
|-----------|-------------------|-------------------|
| Origine | Nice | Melzo |
| Équivalence m³ | 250 kg | 300 kg |
| Équivalence ldm | 1600 kg | 1650 kg |
| Handling | Non | 1€/100kg |
| Hayon | 35€ | 35€ (Lombardie: inclus) |
| ADR | Non mentionné | Inclus |
| Nombre destinations | 8 | 107 |
| Tranches poids | 9 | 6 |

### B. Contacts Monaco Logistique

| Fonction | Contact | Email |
|----------|---------|-------|
| Road Operations Manager | Emma Calestrini | e.calestrini@monacologistique.mc |
| Demandes de prix | Christophe Bayle | c.bayle@monacologistique.mc |
| Opérations | - | transports@monacologistique.mc |
