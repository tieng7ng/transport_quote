# Règles d'Importation : ML BIANCHI GROUP PROTOCOLE

## 1. Informations Générales

| Propriété | Valeur |
|-----------|--------|
| **Fichier** | `ML BIANCHI GROUP PROTOCOLE 01.02.2023 OK FOR 2024 update fuel 1.11.24.xlsx` |
| **Partenaire** | ML BIANCHI GROUP / Monaco Logistique |
| **Code partenaire** | `BIANCHI` |
| **Type de grille** | Double matrice (petits poids / gros poids) |
| **Mode transport** | Route (ROAD) |
| **Origine** | Nice (FR 06) / Casnate (IT) |

---

## 2. Structure du Fichier Excel

Le fichier contient **13 feuilles** :

| Feuille | Description | À importer |
|---------|-------------|------------|
| **PROTOCOLE DISTRIBUTION FRANCE** | Tarifs distribution France depuis Nice | ✅ Oui |
| JIT PROTOCOLE | Tarifs Just-In-Time (express) | ⚠️ Optionnel |
| LIV ID LOG F13 & FERRERO ALBA | Vide | ❌ Non |
| TRAFIC FLOS GEN-5% | Tarifs client FLOS (-5%) | ❌ Client spécifique |
| TRAFIC DECATHLON | Tarifs client Decathlon | ❌ Client spécifique |
| STD DISTRIBUTION ITALY 2023 | Distribution Italie | ⚠️ Optionnel |
| SPECIAL DESTINATIONS IT 2023 | Destinations spéciales Italie | ⚠️ Optionnel |
| MANE 2023 -5% | Tarifs client MANE | ❌ Client spécifique |
| ASSOS TUNISIA | Import textile Tunisie | ❌ Maritime |
| NATIONAL DISTRIBUTION TUNISIA | Distribution Tunisie | ❌ Hors scope |
| STD TARIFS TUNISIA | Tarifs Tunisie | ❌ Hors scope |
| **FRANCE DISADVANTAGES AREAS** | Zones difficiles France | ✅ Référence |
| ITALY DISADVANTAGES AREAS | Zones difficiles Italie (lien) | ❌ Lien externe |

---

## 3. Feuille Principale : PROTOCOLE DISTRIBUTION FRANCE

### 3.1 Structure Générale

La feuille contient **deux sections** côte à côte :

```
┌─────────────────────────────────────────────┬─────────────────────────────────────────────┐
│        SECTION PETITS POIDS                 │         SECTION GROS POIDS                  │
│        (Colonnes 1-7)                       │         (Colonnes 9-16)                     │
├─────────────────────────────────────────────┼─────────────────────────────────────────────┤
│ zip code | Minimum | 100/300 | 301/500 |... │ zip code | 1001/1500 | 1501/2000 | ...      │
│    06    |   9.23  |   5.5   |  5.47   |... │    06    |    4.92   |    4.61   | ...      │
└─────────────────────────────────────────────┴─────────────────────────────────────────────┘
```

### 3.2 Structure des Colonnes

**Section Petits Poids (0-1000 kg)** :

| Index | Colonne | Description |
|-------|---------|-------------|
| 1 | zip code | Code département destination |
| 2 | Minimum | Prix minimum (jusqu'à 99 kg) |
| 3 | 100/300 kg | Prix pour 100-300 kg |
| 4 | 301/500kg | Prix pour 301-500 kg |
| 5 | 501/1000 kg | Prix pour 501-1000 kg |
| 6 | PRICING | Type de tarif (PRICE PER 100KGS) |
| 7 | T/T from Nice ** | Délai de transit |

**Section Gros Poids (1001-5000 kg)** :

| Index | Colonne | Description |
|-------|---------|-------------|
| 9 | zip code | Code département destination |
| 10 | 1001/1500 kg | Prix pour 1001-1500 kg |
| 11 | 1501/2000 kg | Prix pour 1501-2000 kg |
| 12 | 2001/3000 kg | Prix pour 2001-3000 kg |
| 13 | 3001/4000 kg | Prix pour 3001-4000 kg |
| 14 | 4001/5000 kg | Prix pour 4001-5000 kg |
| 15 | PRICING | Type (PRICE PER 100KGS ou LUMPSUM FROM NICE) |
| 16 | T/T from Nice ** | Délai de transit |

### 3.3 Départements Couverts

```
06, 04, 05, 07, 09, 11, 12, 13, 15, 16, 20 (Corse), 24, 26, 30, 31, 32, 33, 34,
46, 47, 48, 64, 65, 66, 81, 82, 83, 84, 98 (Monaco)
```

**Total** : 30 départements (28 + Corse en 2 zones + Monaco)

### 3.4 Types de Tarification

| Type | Description | Calcul |
|------|-------------|--------|
| `PRICE PER 100KGS` | Prix aux 100 kg | `prix × (poids / 100)` |
| `LUMPSUM FROM NICE` | Prix forfaitaire | Prix fixe pour la tranche |

### 3.5 Délais de Transit

| Code | Signification |
|------|---------------|
| 24h | Livraison J+1 |
| 24/48h | Livraison J+1 ou J+2 |
| 48h | Livraison J+2 |
| 48/72h | Livraison J+2 ou J+3 |
| 72h | Livraison J+3 |
| 72/96H | Livraison J+3 ou J+4 (Corse) |

---

## 4. Règles de Transformation

### 4.1 Fusion des Deux Sections

Les deux sections (petits poids et gros poids) doivent être fusionnées en une seule ligne par département.

**Tranches de poids résultantes** :

| weight_min | weight_max | Colonne source |
|------------|------------|----------------|
| 0 | 99 | Minimum (col 2) |
| 100 | 300 | 100/300 kg (col 3) |
| 301 | 500 | 301/500kg (col 4) |
| 501 | 1000 | 501/1000 kg (col 5) |
| 1001 | 1500 | 1001/1500 kg (col 10) |
| 1501 | 2000 | 1501/2000 kg (col 11) |
| 2001 | 3000 | 2001/3000 kg (col 12) |
| 3001 | 4000 | 3001/4000 kg (col 13) |
| 4001 | 5000 | 4001/5000 kg (col 14) |

### 4.2 Exemple de Transformation

**Ligne source (département 06)** :

| Section | Minimum | 100/300 | 301/500 | 501/1000 | 1001/1500 | 1501/2000 | 2001/3000 | 3001/4000 | 4001/5000 |
|---------|---------|---------|---------|----------|-----------|-----------|-----------|-----------|-----------|
| Prix | 9.23 | 5.5 | 5.47 | 5.13 | 4.92 | 4.61 | 4.1 | 98* | 115* |

*Note: Pour le 06, les gros poids sont en LUMPSUM (forfait)

**Lignes générées** :

| dest_postal_code | weight_min | weight_max | cost | pricing_type | delivery_time |
|------------------|------------|------------|------|--------------|---------------|
| 06 | 0 | 99 | 9.23 | PER_100KG | 24h |
| 06 | 100 | 300 | 5.5 | PER_100KG | 24h |
| 06 | 301 | 500 | 5.47 | PER_100KG | 24h |
| 06 | 501 | 1000 | 5.13 | PER_100KG | 24h |
| 06 | 1001 | 1500 | 4.92 | PER_100KG | 24h |
| 06 | 1501 | 2000 | 4.61 | PER_100KG | 24h |
| 06 | 2001 | 3000 | 4.1 | PER_100KG | 24h |
| 06 | 3001 | 4000 | 98 | LUMPSUM | 24h |
| 06 | 4001 | 5000 | 115 | LUMPSUM | 24h |

### 4.3 Gestion de la Corse

Le département 20 a deux zones :

| Code fichier | Description | Traitement |
|--------------|-------------|------------|
| `20 (1)` | Ajaccio & Bastia | dest_postal_code = "2A" ou "20" + zone = 1 |
| `20 (2)` | Autres communes Corse | dest_postal_code = "2B" ou "20" + zone = 2 |

### 4.4 Gestion de Monaco

| Code fichier | Description | Traitement |
|--------------|-------------|------------|
| `98` | Monaco | dest_country = "MC", dest_postal_code = "98000" |

### 4.5 Normalisation

- **Villes** : `origin_city` et `dest_city` sont automatiquement convertis en **MAJUSCULES**.
- **Transport Mode** : Toujours "ROAD".

---

## 5. Conditions Spéciales (Informatives)

### 5.1 Base de Calcul

```
1 M³ = 250 kg (rapport poids/volume)
1 LDM = 1600 kg (mètre linéaire)
```

### 5.2 Surcharges

| Condition | Surcharge |
|-----------|-----------|
| Zones difficiles (montagnes, ski, campagne) | Voir liste FRANCE DISADVANTAGES AREAS |
| Centres-villes, chantiers, particuliers | Majoration possible |
| ADR (matières dangereuses) 04/05 & Corse | Majoration possible |
| Marchandises non gerbables (>2 LDM) | Facturation au LDM |
| Enlèvement hors 06/98 | +15 € fixe |
| Longueurs 3-5m | +100% sur tarifs |
| Longueurs 3-5m Corse | +200% sur tarifs |
| COD (contre-remboursement) | 15 € |
| Taxe gasoil | 5% (depuis nov 2024) |

### 5.3 Tarifs Traction (Terminaux)

| Trajet | Prix |
|--------|------|
| Casnate → Nice | 4,80 € / 100 kg |
| Nice → Casnate | 3,80 € / 100 kg |
| Carpi (Modena) → Nice | 5,60 € / 100 kg |

---

## 6. Feuille Référence : FRANCE DISADVANTAGES AREAS

### 6.1 Structure

| Colonne | Description |
|---------|-------------|
| Dpt | Code département |
| code Insee | Code INSEE commune |
| Localités | Nom de la commune |
| code postaux | Code postal |

### 6.2 Statistiques

- **Nombre de localités** : 1098
- **Départements concernés** : 04, 05, 06, 09, 11, 12, 15, 31, 32, 38, 46, 48, 64, 65, 66, 73, 74, 81, 82, 83, 84, 09, etc.

### 6.3 Utilisation (MVP)

**Approche MVP** : Pas d'automatisation pour l'instant.

La feuille "FRANCE DISADVANTAGES AREAS" sert de **référence manuelle** pour le commercial :
- Le fichier Excel est conservé en local ou partagé
- Le commercial vérifie manuellement si un code postal est en zone difficile
- Si oui, il contacte BIANCHI pour obtenir le tarif réel

**Note affichée sur les tarifs BIANCHI** :

```
ℹ️ Tarifs non applicables aux zones montagnes, stations de ski et zones isolées.
   Liste disponible : FRANCE DISADVANTAGES AREAS (1098 localités)
   → Tarif sur demande pour ces destinations.
```

### Évolution future

Si le volume de devis vers zones difficiles devient important, une table `disadvantage_areas` pourra être créée pour automatiser la détection. Voir section 12 (Questions ouvertes).

---

## 7. Configuration YAML Proposée

```yaml
BIANCHI:
  layout: "dual_grid"  # Nouveau type pour double matrice
  header_row: 6
  data_start_row: 7
  data_end_row: 36  # Ligne 36 = département 84
  sheet_name: "PROTOCOLE DISTRIBUTION FRANCE"

  # Colonnes fixes
  columns:
    dest_postal_code: 1          # zip code (section 1)
    pricing_type_small: 6        # PRICING (section 1)
    delivery_time_small: 7       # T/T (section 1)
    pricing_type_large: 15       # PRICING (section 2)
    delivery_time_large: 16      # T/T (section 2)

  # Valeurs par défaut
  defaults:
    transport_mode: "ROAD"
    origin_country: "FR"
    origin_city: "NICE"
    origin_postal_code: "06000"
    dest_country: "FR"
    currency: "EUR"

  # Configuration double grille
  dual_grid:
    # Section petits poids
    small_weights:
      columns:
        Minimum: { weight_min: 0, weight_max: 99, col_index: 2 }
        "100/300 kg": { weight_min: 100, weight_max: 300, col_index: 3 }
        "301/500kg": { weight_min: 301, weight_max: 500, col_index: 4 }
        "501/1000 kg": { weight_min: 501, weight_max: 1000, col_index: 5 }
      pricing_col: 6
      delivery_time_col: 7

    # Section gros poids
    large_weights:
      columns:
        "1001/1500 kg": { weight_min: 1001, weight_max: 1500, col_index: 10 }
        "1501/2000 kg": { weight_min: 1501, weight_max: 2000, col_index: 11 }
        "2001/3000 kg": { weight_min: 2001, weight_max: 3000, col_index: 12 }
        "3001/4000 kg": { weight_min: 3001, weight_max: 4000, col_index: 13 }
        "4001/5000 kg": { weight_min: 4001, weight_max: 5000, col_index: 14 }
      pricing_col: 15
      delivery_time_col: 16

  # Transformations spéciales
  transforms:
    dest_postal_code:
      "20 (1)": "2A"  # Corse Ajaccio/Bastia
      "20 (2)": "2B"  # Corse autres
      "98": "98000"   # Monaco

    pricing_type:
      "PRICE PER 100KGS": "PER_100KG"
      "LUMPSUM FROM NICE": "LUMPSUM"

  # Validation
  validation:
    skip_rows_with:
      - "Calculation basis"
      - "**"
      - "Other Costs"
```

---

## 8. Schéma de Données Étendu

Pour supporter les deux types de tarification, le schéma `partner_quotes` pourrait être étendu :

```sql
ALTER TABLE partner_quotes ADD COLUMN pricing_type VARCHAR(20) DEFAULT 'PER_100KG';
-- Valeurs: 'PER_100KG', 'LUMPSUM', 'PER_KG', 'PER_PALLET'

-- La colonne cost contient:
-- - Si PER_100KG: prix aux 100 kg
-- - Si LUMPSUM: prix forfaitaire total
```

### Calcul du prix final

```python
def calculate_price(cost: float, weight: float, pricing_type: str) -> float:
    if pricing_type == 'PER_100KG':
        # Arrondi à la centaine supérieure
        billable_weight = math.ceil(weight / 100) * 100
        return cost * (billable_weight / 100)
    elif pricing_type == 'LUMPSUM':
        return cost  # Prix fixe
    elif pricing_type == 'PER_KG':
        return cost * weight
    else:
        return cost
```

---

## 9. Volume de Données Attendu

| Métrique | Valeur |
|----------|--------|
| Départements | 30 |
| Tranches de poids par département | 9 |
| **Total lignes importées** | **~270** |
| Zones difficiles (référence) | 1098 |

---

## 10. Complexités Spécifiques

### 10.1 Double Matrice

Contrairement à BESSON (matrice simple), BIANCHI utilise une **double matrice** avec :
- Deux colonnes `zip code` (col 1 et col 9)
- Deux colonnes `PRICING` (col 6 et col 15)
- Deux colonnes `T/T` (col 7 et col 16)

**Impact** : Le parser doit fusionner les deux sections.

### 10.2 Types de Tarification Mixtes

Un même département peut avoir :
- `PRICE PER 100KGS` pour les petits poids
- `LUMPSUM FROM NICE` pour les gros poids

**Exemple (département 06)** :
- 0-3000 kg : PRICE PER 100KGS
- 3001-5000 kg : LUMPSUM FROM NICE

### 10.3 Valeurs Manquantes

Certains départements n'ont pas toutes les tranches de poids renseignées.

**Exemple (département 09)** :
- 3001/4000 kg : NaN (vide)
- 4001/5000 kg : NaN (vide)

**Traitement** : Ignorer les tranches sans prix.

---

## 11. Estimation d'Implémentation (MVP)

| Tâche | Durée | Statut |
|-------|-------|--------|
| Créer nouveau layout `dual_grid` dans ColumnMapper | 3h | ✅ Fait |
| Champ `pricing_type` au schéma | 1h | ✅ Existait déjà |
| Configuration YAML BIANCHI | 1h | ✅ Fait |
| Modifier calcul prix dans QuoteService | 1h | À faire |
| Ajouter note zones difficiles sur tarifs BIANCHI | 0.5h | À faire |
| Tests et validation | 1.5h | À faire |
| **Total restant** | **~3h** | |

*Note : La gestion automatisée des zones difficiles (table `disadvantage_areas`) n'est pas incluse dans le MVP.*

---

## 12. Questions Ouvertes

1. ~~**Pricing type**~~ : ✅ **Résolu** → Le champ `pricing_type` existe déjà en base.
   - Valeurs : `PER_100KG` (défaut), `LUMPSUM`, `PER_KG`, `PER_PALLET`
   - Mapping configuré dans YAML : `PRICE PER 100KGS` → `PER_100KG`, `LUMPSUM FROM NICE` → `LUMPSUM`

2. ~~**Zones difficiles**~~ : ✅ **Résolu** → MVP sans table, traitement manuel avec note informative.
   - Évolution future possible : table `disadvantage_areas` si le volume le justifie

3. **Monaco** : Créer une entrée séparée avec `dest_country = MC` ou garder `FR` + `dest_postal_code = 98` ?
   - Actuellement configuré : `98` → `98000` (reste en FR)

4. **Surcharges** : Stocker les surcharges (gasoil 5%, COD 15€, etc.) dans une table séparée `partner_surcharges` ?
   - MVP : Non implémenté, à gérer manuellement

5. **Clients spécifiques** : Ignorer les feuilles client (FLOS, DECATHLON, MANE) ou les importer comme variantes ?
   - MVP : Ignorées (tarifs spécifiques clients)

---

## 13. Checklist d'Import

- [ ] Créer le partenaire "BIANCHI" en base
- [x] Implémenter le parser `dual_grid` dans `column_mapper.py`
- [x] Champ `pricing_type` existe en base (PER_100KG, LUMPSUM, etc.)
- [x] Configuration YAML BIANCHI (`partner_mapping.yaml`)
- [x] Transforms configurés (Corse 2A/2B, Monaco 98000, pricing types)
- [ ] Exécuter l'import réel
- [ ] Vérifier le nombre de lignes (~270)
- [ ] Tester les calculs de prix (PER_100KG vs LUMPSUM)
- [ ] Ajouter note informative zones difficiles sur les tarifs BIANCHI
- [ ] Conserver fichier Excel en référence pour consultation manuelle des zones difficiles
