# Règles d'Importation : Grille Tarifaire BESSON 2024

## 1. Informations Générales

| Propriété | Valeur |
|-----------|--------|
| **Fichier** | `grille tarifaire2024 BESSON.xlsx` |
| **Partenaire** | Transport BESSON |
| **Code partenaire** | `BESSON` |
| **Type de grille** | Matrice (Grid) |
| **Mode transport** | Route (ROAD) |

---

## 2. Structure du Fichier Excel

Le fichier contient **3 feuilles** :

### 2.1 Feuille "Conditions de taxation" (Informative)

Contient les conditions générales de taxation (non importée) :

| Information | Valeur |
|-------------|--------|
| Entité | MONACO LOGISTIQUE |
| Adresse | 6 Rue Princesse Florestine, Le Cyrius, 98000 Monaco |
| Échelle de taxation | Messagerie / Colis de messagerie standard |
| Timbre port payé | 1.80 € |
| Timbre port dû | 4.50 € |
| Timbre tiers | 4.50 € |
| Timbre assigné | 7.50 € |
| Contre-remboursement taxe fixe | 11.25 € |
| Contre-remboursement taux | 3.00 ‰ (au-delà de 152 €) |
| Rapport Poids/Volume | 150 kg/m³ |
| Coefficient longueur 3-4m | 1.50 |
| Coefficient longueur >4m | 2.00 |

### 2.2 Feuille "Tarifs" (À importer)

**Dimensions** : 135 lignes de tarifs × 20 colonnes

**Structure des colonnes** :

| Index | Colonne | Type | Description |
|-------|---------|------|-------------|
| 0 | Agence | String | Code agence origine (NIC, MAR) |
| 1 | Département | String | Code département destination (01-95) |
| 2 | Zone | Integer | Zone tarifaire (1, 2, 3) |
| 3 | *(sans nom)* | String | Nom de la zone/localité destination |
| 4-19 | Colonnes poids | Decimal | Prix par tranche de poids |

**Colonnes de poids (pivot)** :

| Colonne | Poids Max |
|---------|-----------|
| 5 KG | 5 kg |
| 10 KG | 10 kg |
| 20 KG | 20 kg |
| 30 KG | 30 kg |
| 40 KG | 40 kg |
| 50 KG | 50 kg |
| 60 KG | 60 kg |
| 70 KG | 70 kg |
| 80 KG | 80 kg |
| 90 KG | 90 kg |
| 100 KG | 100 kg |
| 500 KG | 500 kg |
| 1TONNE | 1000 kg |
| 2TONNE | 2000 kg |
| 3TONNE | 3000 kg |
| 4TONNE | 4000 kg |

### 2.3 Feuille "Localités" (Référence)

**Dimensions** : 13 848 localités

**Structure** :

| Colonne | Description | Exemple |
|---------|-------------|---------|
| Pays | Code pays ISO | FR |
| DPT | Code département | 01 |
| INSEE | Code INSEE commune | 01003 |
| CP | Code postal | 01090 |
| Ville | Nom de la ville | AMAREINS |
| Zone | Zone tarifaire (1-4) | 3 |
| S/Traitant | Sous-traitant de livraison | TRANSPORTS ROUSSET, 01450 PONCIN |

---

## 3. Règles de Mapping

### 3.1 Configuration YAML

```yaml
BESSON:
  layout: "grid"
  header_row: 0
  sheet_name: "Tarifs"

  columns:
    origin_city: "Agence"           # NIC → Nice, MAR → Marseille
    dest_postal_code: "Département" # Code département (01, 06, 13...)
    zone: "Zone"                    # Zone tarifaire (1, 2, 3)
    dest_city: "unnamed:_3"         # Nom de la zone/localité

  defaults:
    transport_mode: "ROAD"
    origin_country: "FR"
    dest_country: "FR"
    currency: "EUR"

  grid:
    pivot_axis: "weight"
    value_column: "cost"
    header_regex: "^(\\d+)[_\\s]*(KG|kg|TONNE|tonne)"
    unit: "KG"
```

### 3.2 Correspondance Agences → Villes

| Code Agence | Ville Origine |
|-------------|---------------|
| NIC | Nice |
| MAR | Marseille |

### 3.3 Correspondance Zones

| Zone | Description |
|------|-------------|
| 1 | Zone principale (ex: ville préfecture) |
| 2 | Autres localités du département |
| 3 | Zones spéciales (ex: Haute Montagne, zones éloignées) |
| 4 | *(Existe dans Localités mais pas dans Tarifs)* |

---

## 4. Transformation des Données

### 4.1 Dépivotage de la Matrice

Une ligne du fichier source génère **16 lignes** dans la base (une par tranche de poids).

**Exemple - Ligne source** :

| Agence | Département | Zone | Localité | 5 KG | 10 KG | ... | 4TONNE |
|--------|-------------|------|----------|------|-------|-----|--------|
| NIC | 01 | 1 | BOURG EN BRESSE | 14.52 | 15.66 | ... | 24.21 |

**Lignes générées** :

| origin_city | dest_postal_code | dest_city | weight_min | weight_max | cost |
|-------------|------------------|-----------|------------|------------|------|
| NIC | 01 | BOURG EN BRESSE | 0 | 5 | 14.52 |
| NIC | 01 | BOURG EN BRESSE | 6 | 10 | 15.66 |
| NIC | 01 | BOURG EN BRESSE | 11 | 20 | 17.66 |
| ... | ... | ... | ... | ... | ... |
| NIC | 01 | BOURG EN BRESSE | 3001 | 4000 | 24.21 |

### 4.2 Règles de Calcul weight_min

Le `weight_min` est déduit de la colonne précédente + 1 (tranches disjointes) :

```
weight_min[n] = weight_max[n-1] + 1
weight_min[0] = 0
```

**Tranches résultantes** :

| weight_min | weight_max |
|------------|------------|
| 0 | 5 |
| 6 | 10 |
| 11 | 20 |
| 21 | 30 |
| 31 | 40 |
| 41 | 50 |
| 51 | 60 |
| 61 | 70 |
| 71 | 80 |
| 81 | 90 |
| 91 | 100 |
| 101 | 500 |
| 501 | 1000 |
| 1001 | 2000 |
| 2001 | 3000 |
| 3001 | 4000 |

### 4.3 Conversion des Tonnages

| Header fichier | weight_max (kg) |
|----------------|-----------------|
| 1TONNE | 1000 |
| 2TONNE | 2000 |
| 3TONNE | 3000 |
| 4TONNE | 4000 |

---

## 5. Valeurs par Défaut

| Champ | Valeur |
|-------|--------|
| `transport_mode` | ROAD |
| `origin_country` | FR |
| `dest_country` | FR |
| `currency` | EUR |
| `valid_until` | NULL (illimité) |
| `delivery_time` | NULL |

---

## 6. Validation des Données

### 6.1 Champs Obligatoires

| Champ | Règle |
|-------|-------|
| `origin_city` | Non vide |
| `dest_postal_code` | 2 caractères minimum, format département |
| `weight_min` | >= 0 |
| `weight_max` | > weight_min |
| `cost` | > 0, numérique |

### 6.2 Normalisation

- **Département** : Toujours 2 caractères (ex: "1" → "01")
- **Code agence** : Uppercase
- **Ville** : `origin_city` et `dest_city` convertis en **MAJUSCULES**.

### 6.3 Erreurs à Gérer

| Erreur | Action |
|--------|--------|
| Prix manquant (cellule vide) | Ignorer cette tranche de poids |
| Prix non numérique | Logger erreur, ignorer la tranche |
| Ligne sans agence | Ignorer la ligne complète |
| Département invalide | Logger erreur, ignorer la ligne |

---

## 7. Schéma Final en Base de Données

Chaque ligne importée devient un enregistrement `partner_quotes` :

```sql
INSERT INTO partner_quotes (
    id,
    partner_id,
    transport_mode,
    origin_country,
    origin_city,
    origin_postal_code,
    dest_country,
    dest_city,
    dest_postal_code,
    weight_min,
    weight_max,
    cost,
    currency,
    valid_until,
    delivery_time,
    created_at
) VALUES (
    uuid_generate_v4(),
    '{partner_id_BESSON}',
    'ROAD',
    'FR',
    'NIC',            -- Code agence
    NULL,
    'FR',
    'BOURG EN BRESSE', -- Nom localité
    '01',             -- Département
    0,
    5,
    14.52,
    'EUR',
    NULL,
    NULL,
    NOW()
);
```

---

## 8. Volume de Données Attendu

| Métrique | Valeur |
|----------|--------|
| Lignes fichier (feuille Tarifs) | 135 |
| Tranches de poids par ligne | 16 |
| **Total lignes importées** | **~2 160** |
| Agences | 2 (NIC, MAR) |
| Départements couverts | 42 |

---

## 9. Utilisation de la Feuille "Localités"

La feuille "Localités" peut être utilisée pour :

1. **Enrichir les données** : Mapper un code postal vers une zone tarifaire
2. **Validation** : Vérifier qu'un CP/Ville existe dans la zone du fichier tarifs
3. **Recherche** : Permettre la recherche par code postal plutôt que par département

### Règle de Correspondance

```
Localité.DPT == Tarif.Département
Localité.Zone == Tarif.Zone
→ La localité utilise le tarif de cette zone
```

**Exemple** :
- Recherche pour CP `01090` (AMAREINS)
- Lookup dans Localités → DPT=`01`, Zone=`3`
- Lookup dans Tarifs → Département=`01`, Zone=`3` → "AUTRES LOCALITES"
- Tarif applicable trouvé

---

## 10. Améliorations Futures

### 10.1 Import de la Feuille "Localités"

Créer une table `localities` pour permettre :
- Recherche par code postal
- Résolution automatique de la zone
- Affichage du sous-traitant de livraison

### 10.2 Gestion des Conditions de Taxation

Créer une table `partner_conditions` pour stocker :
- Timbres (port payé, port dû, tiers, assigné)
- Contre-remboursements
- Coefficients poids/volume
- Coefficients longueur

### 10.3 Regex Amélioré pour Tonnages

```yaml
header_regex: "^(\\d+)[_\\s]*(KG|kg|TONNE|tonne|T)"
```

Avec post-traitement :
```python
if unit in ['TONNE', 'tonne', 'T']:
    weight_max = float(value) * 1000
```

---

## 11. Exemple de Configuration Complète

```yaml
# configs/partner_mapping.yaml

BESSON:
  # Type de layout
  layout: "grid"

  # Configuration du parser Excel
  sheet_name: "Tarifs"
  header_row: 0

  # Mapping des colonnes fixes
  columns:
    origin_city: "Agence"
    dest_postal_code: "Département"
    zone: "Zone"
    dest_city: "unnamed:_3"

  # Valeurs par défaut
  defaults:
    transport_mode: "ROAD"
    origin_country: "FR"
    dest_country: "FR"
    currency: "EUR"

  # Configuration du dépivotage
  grid:
    pivot_axis: "weight"
    value_column: "cost"
    header_regex: "^(\\d+)[_\\s]*(KG|kg)"
    tonnage_regex: "^(\\d+)(TONNE|tonne|T)"
    tonnage_multiplier: 1000
    unit: "KG"

  # Transformation des codes agences
  transforms:
    origin_city:
      NIC: "NICE"
      MAR: "MARSEILLE"

  # Validation spécifique
  validation:
    dest_postal_code:
      min_length: 2
      max_length: 2
      pad_left: "0"
```

---

## 12. Checklist d'Import

- [ ] Vérifier que le partenaire "BESSON" existe en base
- [ ] Vérifier que le fichier contient la feuille "Tarifs"
- [ ] Vérifier que les colonnes de poids sont présentes
- [ ] Exécuter l'import en mode "Replace" (supprime les anciens tarifs)
- [ ] Vérifier le nombre de lignes importées (~2160)
- [ ] Tester une recherche de tarif (ex: Nice → 01, 500kg)
