# Documentation Import ML BIANCHI GROUP

## Vue d'ensemble

### Contexte et objectif

#### Besoin métier
ML Bianchi Group est un partenaire transport qui propose :
- Des tarifs de distribution depuis Nice vers différents départements français (30 départements)
- Des tarifs express JIT (Just-In-Time) en 24h, 48h et 72h
- Des tarifs de distribution Italie depuis leur terminal de Casnate (18 zones)
- Une liste de zones difficiles (montagnes, ski, campagne) non desservies aux tarifs standard

#### Objectif
Importer automatiquement les grilles tarifaires du fichier Excel fourni par ML Bianchi Group dans l'application de gestion des devis transport.

#### Fichier source
- **Nom** : `ML BIANCHI GROUP PROTOCOLE 01.02.2023 OK FOR 2024 update fuel 1.11.24.xlsx`
- **Période de validité** : 01/02/2023 - mise à jour fuel 01/11/2024
- **Devise** : EUR

### Structure du fichier Excel

| # | Feuille | Description | Statut |
|---|---------|-------------|--------|
| 1 | **PROTOCOLE DISTRIBUTION FRANCE** | Tarifs distribution France depuis Nice | ✅ Phase 1 |
| 2 | JIT PROTOCOLE | Tarifs express (24h, 48h, 72h) | 📋 Phase 2 |
| 3 | LIV ID LOG F13 & FERRERO ALBA | Vide | ❌ Non importée |
| 4 | TRAFIC FLOS GEN-5% | Tarifs client FLOS (-5%) | ❌ Client spécifique |
| 5 | TRAFIC DECATHLON | Tarifs client Decathlon | ❌ Client spécifique |
| 6 | STD DISTRIBUTION ITALY 2023 | Distribution Italie depuis Casnate | 📋 Phase 2 |
| 7 | SPECIAL DESTINATIONS IT 2023 | Destinations spéciales Italie | ❌ Hors scope |
| 8 | MANE 2023 -5% | Tarifs client MANE | ❌ Client spécifique |
| 9 | ASSOS TUNISIA | Import textile Tunisie | ❌ Maritime |
| 10 | NATIONAL DISTRIBUTION TUNISIA | Distribution Tunisie | ❌ Hors scope |
| 11 | STD TARIFS TUNISIA | Tarifs Tunisie | ❌ Hors scope |
| 12 | **FRANCE DISADVANTAGES AREAS** | Zones difficiles France (1098 localités) | ✅ Référence |
| 13 | ITALY DISADVANTAGES AREAS | Zones difficiles Italie (lien externe) | ❌ Lien externe |

**Import Phase 1** : Un seul upload avec `partner_id = BIANCHI` traite la feuille "PROTOCOLE DISTRIBUTION FRANCE" grâce au layout `dual_grid`.

---

## Feuille 1 : PROTOCOLE DISTRIBUTION FRANCE

### 1.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `PROTOCOLE DISTRIBUTION FRANCE` |
| Origine | Nice (06000), France |
| Destinations | 30 départements français (28 + Corse en 2 zones + Monaco) |
| Mode transport | Route (ROAD) |

### 1.2 Départements couverts

| Code Excel | Code normalisé | Département | Délai transit |
|------------|----------------|-------------|---------------|
| 06 | 06 | Alpes-Maritimes | 24h |
| 98 | 98000 | Monaco | 24h |
| 04 | 04 | Alpes-de-Haute-Provence | 48/72h |
| 05 | 05 | Hautes-Alpes | 48/72h |
| 07 | 07 | Ardèche | 48h |
| 09 | 09 | Ariège | 72h |
| 11 | 11 | Aude | 72h |
| 12 | 12 | Aveyron | 72h |
| 13 | 13 | Bouches-du-Rhône | 24/48h |
| 15 | 15 | Cantal | 48/72h |
| 16 | 16 | Charente | 48/72h |
| 20 (1) | 2A | Corse-du-Sud (Ajaccio & Bastia) | 72/96H |
| 20 (2) | 2B | Haute-Corse (autres communes) | 72/96H |
| 24 | 24 | Dordogne | 72h |
| 26 | 26 | Drôme | 48h |
| 30 | 30 | Gard | 48h |
| 31 | 31 | Haute-Garonne | 48h |
| 32 | 32 | Gers | 72h |
| 33 | 33 | Gironde | 72h |
| 34 | 34 | Hérault | 48h |
| 46 | 46 | Lot | 72h |
| 47 | 47 | Lot-et-Garonne | 72h |
| 48 | 48 | Lozère | 72h |
| 64 | 64 | Pyrénées-Atlantiques | 72h |
| 65 | 65 | Hautes-Pyrénées | 72h |
| 66 | 66 | Pyrénées-Orientales | 72h |
| 81 | 81 | Tarn | 48/72h |
| 82 | 82 | Tarn-et-Garonne | 48/72h |
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

**Section 2 - Gros poids (PER_100KG ou LUMPSUM selon département)**
| Tranche | Poids min | Poids max | Type tarif |
|---------|-----------|-----------|------------|
| 1001/1500 kg | 1001 kg | 1500 kg | PER_100KG ou LUMPSUM |
| 1501/2000 kg | 1501 kg | 2000 kg | PER_100KG ou LUMPSUM |
| 2001/3000 kg | 2001 kg | 3000 kg | PER_100KG ou LUMPSUM |
| 3001/4000 kg | 3001 kg | 4000 kg | PER_100KG ou LUMPSUM |
| 4001/5000 kg | 4001 kg | 5000 kg | PER_100KG ou LUMPSUM |

### 1.4 Types de tarification

| Type | Code système | Règle de calcul |
|------|--------------|-----------------|
| Prix au 100 kg | `PER_100KG` | Prix × (poids arrondi au 100 kg supérieur / 100) |
| Forfait | `LUMPSUM` | Prix fixe quelle que soit la quantité dans la tranche |

**Exemple de calcul PER_100KG** :
- Envoi de 250 kg vers département 13
- Prix unitaire : 16€/100kg (tranche 100/300 kg)
- Poids arrondi : 300 kg (arrondi au 100 supérieur)
- **Prix final : 16 × 3 = 48€**

**Exemple de calcul LUMPSUM** :
- Envoi de 3500 kg vers département 06
- Tranche 3001/4000 kg : forfait = 98€
- **Prix final : 98€** (prix fixe)

### 1.5 Tarification mixte par département

Un même département peut avoir un type de tarification différent entre petits et gros poids :

| Département | Petits poids (0-1000 kg) | Gros poids (1001-5000 kg) |
|-------------|--------------------------|---------------------------|
| 06 (Nice) | PER_100KG | PER_100KG (1001-3000) puis LUMPSUM (3001-5000) |
| 13 (Marseille) | PER_100KG | LUMPSUM |
| 04, 05 (Alpes) | PER_100KG | LUMPSUM |
| 30, 34, 83, 84 | PER_100KG | LUMPSUM |
| 07, 09, 11, 26, 31... | PER_100KG | PER_100KG |
| 20 (Corse) | PER_100KG | Pas de gros poids (NaN) |

### 1.6 Règles métier spécifiques

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
| 3 - 5 m | +100% | +200% |
| > 5 m | Sur demande | Sur demande |

#### Marchandises non gerbables
- Au-delà de 2 LDM : facturation au LDM (1 LDM = 1600 kg)

#### Enlèvement hors zone Nice/Monaco
- **+15€ fixe** pour tout enlèvement hors départements 06 et 98

#### Zones exclues

Les tarifs ne sont **pas valides** pour :
- Zones de montagne
- Stations de ski
- Zones rurales isolées (campagne)

Majoration possible pour :
- Centres-villes
- Chantiers de construction
- Livraisons aux particuliers

**Note affichée sur les tarifs BIANCHI** :
```
Tarifs non applicables aux zones montagnes, stations de ski et zones isolées.
Liste disponible : FRANCE DISADVANTAGES AREAS (1098 localités, 27 départements)
→ Tarif sur demande pour ces destinations.
```

### 1.7 Configuration technique

Voir la [configuration YAML](#configuration-yaml) dans la section Documentation Technique.

### 1.8 Mapping visuel

```
Ligne 7 (header, 0-indexed: 6):
┌────────┬─────────┬──────────┬──────────┬───────────┬─────────┬─────────┬───┬────────┬───────────┬───────────┬───────────┬───────────┬───────────┬─────────┬─────────┐
│zip code│ Minimum │100/300 kg│301/500kg │501/1000 kg│ PRICING │T/T Nice │   │zip code│1001/1500kg│1501/2000kg│2001/3000kg│3001/4000kg│4001/5000kg│ PRICING │T/T Nice │
└────────┴─────────┴──────────┴──────────┴───────────┴─────────┴─────────┴───┴────────┴───────────┴───────────┴───────────┴───────────┴───────────┴─────────┴─────────┘
   Col 1     Col 2      Col 3      Col 4       Col 5      Col 6     Col 7  Col8  Col 9     Col 10     Col 11     Col 12     Col 13     Col 14     Col 15    Col 16

Ligne 8 (données) :
┌────────┬─────────┬──────────┬──────────┬───────────┬─────────────────┬─────┬───┬────────┬───────────┬───────────┬───────────┬───────────┬───────────┬─────────────────┬─────┐
│   06   │   9.23  │   5.50   │   5.47   │   5.13    │PRICE PER 100KGS │ 24h │   │   06   │   4.92    │   4.61    │   4.10    │   98*     │   115*    │PRICE PER 100KGS │ 24h │
└────────┴─────────┴──────────┴──────────┴───────────┴─────────────────┴─────┴───┴────────┴───────────┴───────────┴───────────┴───────────┴───────────┴─────────────────┴─────┘
* Les tranches 3001/4000 et 4001/5000 du département 06 sont en LUMPSUM (les valeurs 98 et 115 sont des forfaits)
```

### 1.9 Exemples de tarifs complets

#### Petits poids (€/100 kg)

| Dpt | Minimum | 100/300 | 301/500 | 501/1000 | T/T |
|-----|---------|---------|---------|----------|-----|
| 06 (Nice) | 9,23 | 5,50 | 5,47 | 5,13 | 24h |
| 13 (Marseille) | 21,00 | 16,00 | 14,00 | 12,00 | 24/48h |
| 83 (Var) | 22,00 | 18,00 | 16,00 | 14,00 | 24/48h |
| 34 (Hérault) | 30,00 | 21,00 | 18,00 | 16,00 | 48h |
| 04 (Alpes-HP) | 38,00 | 33,88 | 33,88 | 31,37 | 48/72h |
| 2A (Corse Sud) | 85,00 | 65,00 | 55,00 | 45,00 | 72/96H |
| 2B (Haute-Corse) | 90,00 | 68,00 | 58,00 | 50,00 | 72/96H |
| 12 (Aveyron) | 40,00 | 40,00 | 40,00 | 35,00 | 72h |

#### Gros poids (€/100 kg ou forfait €)

| Dpt | 1001/1500 | 1501/2000 | 2001/3000 | 3001/4000 | 4001/5000 | Type | T/T |
|-----|-----------|-----------|-----------|-----------|-----------|------|-----|
| 06 (Nice) | 4,92 | 4,61 | 4,10 | 98* | 115* | Mixte | 24h |
| 13 (Marseille) | 190 | 220 | 330 | 440 | 550 | LUMPSUM | 24/48h |
| 83 (Var) | 210 | 250 | 390 | 520 | 650 | LUMPSUM | 24/48h |
| 04 (Alpes-HP) | 500 | 550 | NaN | NaN | NaN | LUMPSUM | 48/72h |
| 07 (Ardèche) | 20,00 | 18,00 | 16,00 | NaN | NaN | PER_100KG | 48h |

*Département 06 : PER_100KG pour 1001-3000 kg, LUMPSUM pour 3001-5000 kg.

---

## Feuille 2 : JIT PROTOCOLE - Phase 2

### 2.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `JIT PROTOCOLE` |
| Origine | Nice (06000), France |
| Description | Tarifs express Just-In-Time (livraison accélérée) |
| Mode transport | Route (ROAD) |
| Statut | 📋 Phase 2 |

### 2.2 Trois niveaux de service JIT

#### JIT 24 - Same Day (jour même)
| Élément | Valeur |
|---------|--------|
| Départements | 06 (Nice) et 98 (Monaco) uniquement |
| Calcul | Prix protocole standard + **40€ fixe** |

#### JIT 48 - Next Day (J+1)
| Élément | Valeur |
|---------|--------|
| Départements | 13, 83, 84, 30, 34 |
| Calcul ≤ 1000 kg | Prix protocole + **40%** (minimum 60€) |
| Calcul > 1000 kg | Prix protocole + **35%** (minimum 60€) |

#### JIT 72 - Livraison J+3

Grille tarifaire dédiée pour 7 départements :

| Dpt | Minimum | 100/500 kg | 501/1000 kg | 1001/2000 kg | 2001/3000 kg |
|-----|---------|------------|-------------|--------------|--------------|
| 04 | 165,00 | 45,00 | 40,00 | 30,00 | 20,00 |
| 05 | 170,00 | 48,00 | 40,00 | 30,00 | 20,00 |
| 07 | 175,00 | 38,00 | 35,00 | 25,00 | 18,00 |
| 11 | 140,00 | 40,00 | 25,00 | 20,00 | 20,00 |
| 26 | 175,00 | 38,00 | 35,00 | 25,00 | 18,00 |
| 31 | 210,00 | 45,00 | 30,00 | 22,00 | 20,00 |
| 66 | 175,00 | 45,00 | 32,00 | 25,00 | 22,00 |

**Note** : Le Minimum est un forfait (LUMPSUM), les autres tranches sont en PER_100KG.

### 2.3 Structure attendue pour l'import

L'import JIT pourrait utiliser le même layout `dual_grid` ou un nouveau layout `jit` dédié. La grille JIT 72 a des tranches de poids différentes du protocole standard (100/500 au lieu de 100/300, et pas de tranche 301/500).

---

## Feuille 6 : STD DISTRIBUTION ITALY 2023 - Phase 2

### 3.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `STD DISTRIBUTION ITALY 2023` |
| Origine | Casnate (Terminal), Italie |
| Destinations | 18 zones tarifaires italiennes (par préfixe code postal) |
| Mode transport | Route (ROAD) |
| Statut | 📋 Phase 2 |

### 3.2 Zones tarifaires couvertes

| Zone (Code postal) | Région / Provinces | Minimum €/100kg |
|---------------------|-------------------|------------------|
| 22 | Como (Lombardie) | 7,33 |
| 20/21 | Milano, Varese (Lombardie) | 10,15 |
| 24/25 | Bergamo, Brescia (Lombardie) | 10,82 |
| 238-239/26/27/28/29 | Lecco, Sondrio, Piémont Est | 15,05 |
| 10/13/14/15/230-231 | Turin, Biella, Asti, Alessandria | 16,49 |
| 11/12/16/17/18/19 | Aoste, Cuneo, Gênes, Ligurie | 21,54 |
| 30-39** | Vénétie, Trentin (hors lagune Venise) | 20,30 |
| 42/43 | Reggio Emilia, Parma | 20,30 |
| 40/41/46 | Bologna, Modena, Mantova | 20,30 |
| 44/45/47/48 | Ferrara, Rovigo, Ravenna | 20,30 |
| 50-59 | Toscane | 20,30 |
| 00-06 | Rome, Latium, Ombrie | 22,33 |
| 60-69 | Marche, Abruzzes | 20,30 |
| 70-79 | Pouilles | 24,35 |
| 80-86 | Campanie, Molise | 23,34 |
| 87/88/89 | Calabre | 28,41 |
| 90-99 | Sicile | 30,45 |
| 07/08/09 | Sardaigne | 40,14 |

**Note** : La zone 30-39 exclut la lagune de Venise.

### 3.3 Grille tarifaire

**Structure à matrice simple** : 7 tranches de poids + forfait maximum.

| Tranche | Poids min | Poids max | Type tarif |
|---------|-----------|-----------|------------|
| Minimum | 0 kg | 99 kg | Forfait (€) |
| <500 kgs | 100 kg | 500 kg | Prix au 100 kg |
| <1000 | 501 kg | 1000 kg | Prix au 100 kg |
| <1500 | 1001 kg | 1500 kg | Prix au 100 kg |
| <2000 | 1501 kg | 2000 kg | Prix au 100 kg |
| <2500 | 2001 kg | 2500 kg | Prix au 100 kg |
| <3000 | 2501 kg | 3000 kg | Prix au 100 kg |
| MAX Forfait | - | - | Forfait plafond (si applicable) |

### 3.4 Règles métier spécifiques Italie

#### Calcul du poids taxable
```
Poids taxable = MAX(poids réel, poids volumétrique)

Équivalences :
- 1 m³ = 250 kg
- 1 mètre linéaire (ldm) = 1650 kg
```

**Attention** : L'équivalence LDM (1650 kg) est différente de la France (1600 kg).

#### Surcharges et frais Italie

| Surcharge | Montant | Condition |
|-----------|---------|-----------|
| COD (contre-remboursement) | 15,00 € | Par envoi |
| Fuel surcharge | +5% | Depuis nov 2024 |
| MAX Forfait | Variable | Plafond pour zones 22, 20/21, 24/25 uniquement |

#### Forfait maximum (zones proches uniquement)

| Zone | MAX Forfait |
|------|-------------|
| 22 (Como) | 101,48 € |
| 20/21 (Milano/Varese) | 101,48 € |
| 24/25 (Bergamo/Brescia) | 118,39 € |
| Toutes les autres zones | Sur demande |

### 3.5 Configuration technique (future)

```yaml
# Phase 2 - à implémenter
- name: "italy"
  sheet_name: "STD DISTRIBUTION ITALY 2023"
  layout: "single_grid"  # ou zone_grid
  defaults:
    transport_mode: "ROAD"
    origin_country: "IT"
    origin_city: "CASNATE"
    dest_country: "IT"
    currency: "EUR"
```

---

## Feuille 12 : FRANCE DISADVANTAGES AREAS

### 4.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `FRANCE DISADVANTAGES AREAS` |
| Nombre de localités | 1 098 |
| Départements concernés | 27 |
| Usage | Référence manuelle (pas d'import automatique) |

### 4.2 Structure

| Colonne | Description | Exemple |
|---------|-------------|---------|
| Dpt | Code département | 06 |
| code INSEE | Code INSEE commune | 06003 |
| Localités | Nom de la commune | AIGLUN |
| code postaux | Code postal | 06910 |

### 4.3 Répartition par département

| Département | Nombre de localités |
|-------------|---------------------|
| 09 (Ariège) | 138 |
| 73 (Savoie) | 132 |
| 06 (Alpes-Maritimes) | 103 |
| 38 (Isère) | 94 |
| 65 (Hautes-Pyrénées) | 91 |
| 66 (Pyrénées-Orientales) | 74 |
| 74 (Haute-Savoie) | 69 |
| 05 (Hautes-Alpes) | 65 |
| 64 (Pyrénées-Atlantiques) | 52 |
| 04 (Alpes-de-Haute-Provence) | 49 |
| Autres (17 dpts) | 231 |

### 4.4 Utilisation (MVP)

**Approche MVP** : Pas d'automatisation pour l'instant.

La feuille sert de **référence manuelle** pour le commercial :
- Le fichier Excel est conservé en local ou partagé
- Le commercial vérifie manuellement si un code postal est en zone difficile
- Si oui, il contacte BIANCHI pour obtenir le tarif réel

#### Evolution future

Si le volume de devis vers zones difficiles devient important, une table `disadvantage_areas` pourra être créée pour automatiser la détection :

```sql
CREATE TABLE disadvantage_areas (
    id UUID PRIMARY KEY,
    partner_id UUID REFERENCES partners(id),
    department VARCHAR(3),
    insee_code VARCHAR(5),
    locality VARCHAR(100),
    postal_code VARCHAR(5)
);
-- 1098 lignes pour BIANCHI
```

---

## Surcharges communes (hors import)

Ces surcharges ne sont **pas incluses** dans les prix importés et doivent être gérées séparément :

| Surcharge | Montant | Condition |
|-----------|---------|-----------|
| Taxe gasoil (fuel surcharge) | +5% | Depuis nov 2024 (mise à jour trimestrielle) |
| COD (contre-remboursement) | 15,00 € | Par envoi |
| Enlèvement hors 06/98 | +15,00 € | Fixe par enlèvement |
| ADR (matières dangereuses) 04/05 & Corse | Majoration | Sur demande |
| Longueurs 3-5 m | +100% sur tarifs | Standard |
| Longueurs 3-5 m Corse | +200% sur tarifs | Corse uniquement |
| Longueurs > 5 m | Sur demande | |
| Non gerbable > 2 LDM | Facturation au LDM | 1 LDM = 1600 kg |

### Tarifs traction (terminaux)

| Trajet | Prix |
|--------|------|
| Casnate → Nice | 4,80 € / 100 kg |
| Nice → Casnate | 3,80 € / 100 kg |
| Carpi (Modena) → Nice | 5,60 € / 100 kg |

---

## Documentation Technique

### Configuration YAML

Le partenaire `BIANCHI` utilise un layout `dual_grid` qui traite une feuille avec deux sections de poids côte à côte :

```yaml
BIANCHI:
  layout: "dual_grid"
  header_row: 6
  sheet_name: "PROTOCOLE DISTRIBUTION FRANCE"

  columns:
    dest_postal_code: "zip_code"
    pricing_type_small: "pricing"
    delivery_time_small: "t/t_from_nice_**"
    pricing_type_large: "pricing.1"        # Pandas suffix .1 pour le doublon
    delivery_time_large: "t/t_from_nice_**.1"

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
      "20 (1)": "2A"     # Corse Ajaccio/Bastia
      "20 (2)": "2B"     # Corse autres communes
      "98": "98000"       # Monaco
    pricing_type:
      "PRICE PER 100KGS": "PER_100KG"
      "PRICE PER 100KGS ": "PER_100KG"   # Avec espace trailing
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

  validation:
    skip_rows_with:
      - "Calculation basis"
      - "**"
      - "Other Costs"
```

### Modèle de données

#### Table `partners`

```sql
INSERT INTO partners (id, code, name, email, is_active, default_margin)
VALUES (
  uuid_generate_v4(),
  'BIANCHI',
  'ML Bianchi Group',
  NULL,
  true,
  20
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
| dest_postal_code | VARCHAR | Code département (06, 13, 2A, 2B, 98000...) |
| weight_min | FLOAT | Poids minimum de la tranche |
| weight_max | FLOAT | Poids maximum de la tranche |
| cost | FLOAT | Prix (au 100kg ou forfait) |
| pricing_type | VARCHAR | PER_100KG ou LUMPSUM |
| currency | VARCHAR(3) | EUR |
| delivery_time | VARCHAR | Ex: "24h", "24/48h", "72/96H" |

### Algorithme de recherche

#### Requête SQL pour recherche de tarif

```sql
SELECT pq.*, p.name as partner_name
FROM partner_quotes pq
JOIN partners p ON pq.partner_id = p.id
WHERE p.code = 'BIANCHI'
  AND pq.origin_country = :origin_country
  AND pq.dest_country = :dest_country
  AND (
    -- Prefix matching bidirectionnel
    pq.dest_postal_code LIKE :dest_code || '%'
    OR :dest_code LIKE pq.dest_postal_code || '%'
  )
  AND pq.weight_min <= :weight
  AND pq.weight_max >= :weight
ORDER BY pq.cost ASC;
```

#### Calcul du prix final

```python
def calculate_final_price(quote, actual_weight):
    base_price = 0

    if quote.pricing_type == "LUMPSUM":
        base_price = quote.cost
    elif quote.pricing_type == "PER_100KG":
        # Arrondi au 100 kg supérieur
        rounded_weight = math.ceil(actual_weight / 100) * 100
        base_price = quote.cost * (rounded_weight / 100)

    # Appliquer fuel surcharge (5% depuis nov 2024)
    fuel_surcharge = base_price * 0.05

    return base_price + fuel_surcharge
```

### Validation des données

#### Schéma Pydantic

```python
class QuoteImportSchema(BaseModel):
    transport_mode: TransportMode
    origin_city: str
    origin_country: str       # 2 caractères
    dest_city: str
    dest_country: str          # 2 caractères
    cost: float                # > 0
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
| dest_postal_code | Non vide, après transformation (2A, 2B, 98000) |
| pricing_type | Doit être PER_100KG ou LUMPSUM |
| weight_min/max | weight_min < weight_max |

---

## Exemples de Calculs Détaillés

Cette section illustre le calcul du prix final (surcharges incluses) pour différents scénarios.

### Scénario 1 : Envoi standard vers Marseille (13)

**Données** : 2 palettes, Poids réel 250 kg, Volume 1,2 m³.

- **1. Poids Taxable** :
  - Règle : **1 m³ = 250 kg**.
  - Poids volume : 1,2 × 250 = 300 kg.
  - Poids retenu : **300 kg** (MAX(250, 300)).
- **2. Tranche applicable** : 100/300 kg
- **3. Prix de base (PER_100KG)** :
  - Tarif dpt 13 : **16,00 €** / 100 kg.
  - Poids arrondi au 100 supérieur : 300 kg → 3 unités.
  - Calcul : 16,00 × 3 = **48,00 €**.
- **4. Surcharges** :
  - Fuel Surcharge (+5%) : 48,00 × 0,05 = 2,40 €.
- **PRIX TOTAL : 50,40 €**

### Scénario 2 : Gros envoi vers Marseille (13) en LUMPSUM

**Données** : Poids réel 1 800 kg.

- **1. Tranche applicable** : 1501/2000 kg
- **2. Prix de base (LUMPSUM)** :
  - Type : **Forfait** (LUMPSUM).
  - Tarif dpt 13 : **220,00 €**.
- **3. Surcharges** :
  - Fuel Surcharge (+5%) : 220,00 × 0,05 = 11,00 €.
- **PRIX TOTAL : 231,00 €**

### Scénario 3 : Envoi vers Nice (06) - mixte PER_100KG/LUMPSUM

**Données** : Poids réel 3 500 kg.

- **1. Tranche applicable** : 3001/4000 kg
- **2. Prix de base (LUMPSUM)** :
  - Pour le dpt 06, les tranches 3001+ sont en LUMPSUM.
  - Tarif : **98,00 €**.
- **3. Surcharges** :
  - Fuel Surcharge (+5%) : 98,00 × 0,05 = 4,90 €.
- **PRIX TOTAL : 102,90 €**

### Scénario 4 : Envoi vers Corse (2A) - Ajaccio

**Données** : 1 palette, Poids réel 80 kg, longueur 2 m.

- **1. Poids Taxable** :
  - Poids retenu : **80 kg** (pas de poids volumétrique supérieur).
- **2. Tranche applicable** : Minimum (0-99 kg)
- **3. Prix de base (PER_100KG)** :
  - Tarif dpt 2A : **85,00 €** / 100 kg.
  - Poids arrondi : 100 kg → 1 unité.
  - Calcul : 85,00 × 1 = **85,00 €**.
- **4. Surcharges** :
  - Fuel Surcharge (+5%) : 85,00 × 0,05 = 4,25 €.
- **PRIX TOTAL : 89,25 €**

### Scénario 5 : Envoi avec surcharge longueur

**Données** : 1 palette de 400 kg, longueur 4 m, vers département 34 (Hérault).

- **1. Prix de base (PER_100KG)** :
  - Tranche : 301/500 kg.
  - Tarif dpt 34 : **18,00 €** / 100 kg.
  - Poids arrondi : 400 kg → 4 unités.
  - Calcul : 18,00 × 4 = **72,00 €**.
- **2. Surcharge longueur (3-5 m)** :
  - +100% : 72,00 × 1,00 = 72,00 €.
- **3. Fuel Surcharge (+5%)** :
  - Base : 72,00 + 72,00 = 144,00 €.
  - Fuel : 144,00 × 0,05 = 7,20 €.
- **PRIX TOTAL : 151,20 €**

---

## Tests

### Test d'import complet

```python
def test_bianchi_full_import():
    """Test import de la feuille PROTOCOLE DISTRIBUTION FRANCE."""

    # Upload du fichier avec partner_id = BIANCHI
    all_quotes = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="BIANCHI")
    ).all()

    # 30 départements × 9 tranches max = 270 max
    # Mais certains départements n'ont pas toutes les tranches (NaN)
    assert len(all_quotes) >= 220   # Minimum attendu (Corse sans gros poids, etc.)
    assert len(all_quotes) <= 270   # Maximum théorique
```

### Test - Vérification origine Nice

```python
def test_bianchi_origin_nice():
    """Vérifier que toutes les quotes ont Nice comme origine."""

    quotes = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="BIANCHI")
    ).all()

    for q in quotes:
        assert q.origin_city == "NICE"
        assert q.origin_postal_code == "06000"
        assert q.origin_country == "FR"
        assert q.dest_country == "FR"
```

### Test - Tarif spécifique PER_100KG

```python
def test_bianchi_per_100kg():
    """Vérifier un tarif PER_100KG spécifique - dpt 13, tranche 100/300."""

    quote_13 = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="BIANCHI"),
        PartnerQuote.dest_postal_code == "13",
        PartnerQuote.weight_min == 100,
        PartnerQuote.weight_max == 300
    ).first()

    assert quote_13 is not None
    assert quote_13.cost == 16.0
    assert quote_13.pricing_type == "PER_100KG"
    assert quote_13.delivery_time == "24/48h"
```

### Test - Tarif spécifique LUMPSUM

```python
def test_bianchi_lumpsum():
    """Vérifier un tarif LUMPSUM spécifique - dpt 13, tranche 1501/2000."""

    quote_13_lump = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="BIANCHI"),
        PartnerQuote.dest_postal_code == "13",
        PartnerQuote.weight_min == 1501,
        PartnerQuote.weight_max == 2000
    ).first()

    assert quote_13_lump is not None
    assert quote_13_lump.cost == 220.0
    assert quote_13_lump.pricing_type == "LUMPSUM"
```

### Test - Transformation Corse

```python
def test_bianchi_corse_transform():
    """Vérifier la transformation des codes Corse (2A, 2B)."""

    quotes_2a = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="BIANCHI"),
        PartnerQuote.dest_postal_code == "2A"
    ).all()

    quotes_2b = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="BIANCHI"),
        PartnerQuote.dest_postal_code == "2B"
    ).all()

    assert len(quotes_2a) >= 4  # Au moins petits poids (pas de gros poids)
    assert len(quotes_2b) >= 4
    # Corse = tarifs les plus chers
    for q in quotes_2a:
        assert q.delivery_time == "72/96H"
```

### Test - Valeurs manquantes ignorées

```python
def test_bianchi_nan_ignored():
    """Vérifier que les tranches sans prix (NaN) ne sont pas importées."""

    # Dpt 09 n'a pas de tranches 3001/4000 et 4001/5000
    quotes_09_heavy = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="BIANCHI"),
        PartnerQuote.dest_postal_code == "09",
        PartnerQuote.weight_min >= 3001
    ).all()

    assert len(quotes_09_heavy) == 0
```

### Test - Monaco (98000)

```python
def test_bianchi_monaco():
    """Vérifier la transformation Monaco (98 → 98000)."""

    quotes_monaco = db.query(PartnerQuote).filter(
        PartnerQuote.partner.has(code="BIANCHI"),
        PartnerQuote.dest_postal_code == "98000"
    ).all()

    assert len(quotes_monaco) >= 4
    for q in quotes_monaco:
        assert q.delivery_time == "24h"
```

---

## Checklist d'implémentation

### Backend - Partenaire et configuration

- [ ] Créer le partenaire `BIANCHI` dans la table `partners`
- [x] Ajouter la configuration `BIANCHI` dans `partner_mapping.yaml`
- [x] Implémenter le layout `dual_grid` dans `column_mapper.py`
  - [x] Parser les deux sections (petits poids + gros poids)
  - [x] Gérer les deux types de tarification par section
  - [x] Fusionner les résultats des deux sections
- [x] Champ `pricing_type` existe en base (PER_100KG, LUMPSUM, etc.)
- [x] Transforms configurés (Corse 2A/2B, Monaco 98000, pricing types)

### Backend - Import et validation

- [ ] Exécuter l'import réel du fichier Excel
- [ ] Vérifier le nombre de lignes (~220-270)
- [ ] Vérifier les tarifs PER_100KG (petits poids)
- [ ] Vérifier les tarifs LUMPSUM (gros poids)
- [ ] Vérifier les transformations (Corse, Monaco)
- [ ] Vérifier que les cellules NaN sont ignorées

### Frontend

- [ ] Afficher le `pricing_type` dans les résultats de recherche
- [ ] Implémenter le calcul du prix final selon le `pricing_type`
- [ ] Afficher une note pour les zones Corse (délais plus longs)
- [ ] Ajouter note informative zones difficiles sur les tarifs BIANCHI
- [ ] Conserver fichier Excel en référence pour consultation manuelle des zones difficiles

### Phase 2 (future)

- [ ] Import feuille JIT PROTOCOLE (tarifs express)
- [ ] Import feuille STD DISTRIBUTION ITALY 2023 (distribution Italie)
- [ ] Table `disadvantage_areas` si volume de devis le justifie
- [ ] Gestion des surcharges (fuel, COD, longueur) dans une table `partner_surcharges`
- [ ] Import clients spécifiques (FLOS, DECATHLON, MANE) comme variantes

---

## Annexes

### A. Comparaison BIANCHI vs MONACO LOGISTIQUE (France)

| Paramètre | BIANCHI | MONACO LOGISTIQUE |
|-----------|---------|-------------------|
| Origine | Nice | Nice |
| Nombre de départements | 30 | 8 |
| Tranches de poids | 9 (0-5000 kg) | 9 (0-5000 kg) |
| Équivalence m³ | 250 kg | 250 kg |
| Équivalence ldm | 1600 kg | 1600 kg |
| Handling | Non | Non (France) |
| Fuel surcharge | +5% | +8% |
| Tarifs express (JIT) | Oui (3 niveaux) | Non |
| Zones difficiles | 1098 localités | Liste similaire |
| Tarification gros poids | Mixte (PER_100KG/LUMPSUM) | Identique (mixte) |
| Layout Excel | `dual_grid` | `dual_grid` |

### B. Comparaison BIANCHI France vs BIANCHI Italie

| Paramètre | France | Italie |
|-----------|--------|--------|
| Origine | Nice | Casnate |
| Nombre de zones | 30 départements | 18 zones postales |
| Équivalence m³ | 250 kg | 250 kg |
| Équivalence ldm | 1600 kg | 1650 kg |
| Poids max | 5000 kg | 3000 kg |
| Handling | Non | Non |
| COD | 15€ | 15€ |
| Fuel surcharge | +5% | +5% |
| MAX Forfait | Non | Oui (3 zones proches) |

### C. Volume de données attendu

| Métrique | Valeur |
|----------|--------|
| Départements (France) | 30 |
| Tranches de poids par département | 9 max |
| Lignes importées (France) | ~220-270 |
| Zones difficiles (référence) | 1098 localités |
| Zones Italie (Phase 2) | 18 |
| Lignes importées (Italie, Phase 2) | ~126 |
| Départements JIT 72 (Phase 2) | 7 |
| Lignes JIT 72 (Phase 2) | ~35 |
| **Total estimé (toutes phases)** | **~430** |

### D. Questions ouvertes

1. ~~**Pricing type**~~ : **Résolu** - Le champ `pricing_type` existe déjà en base. Mapping : `PRICE PER 100KGS` → `PER_100KG`, `LUMPSUM FROM NICE` → `LUMPSUM`.

2. ~~**Zones difficiles**~~ : **Résolu** - MVP sans table, traitement manuel avec note informative.

3. **Monaco** : Actuellement configuré `98` → `98000` (reste en `dest_country = FR`). Faut-il créer une entrée séparée avec `dest_country = MC` ?

4. **Surcharges** : Stocker les surcharges (gasoil 5%, COD 15€, longueur, etc.) dans une table séparée `partner_surcharges` ? MVP : Non implémenté, gestion manuelle.

5. **Clients spécifiques** : Les feuilles client (FLOS -5%, DECATHLON, MANE -5%) sont ignorées au MVP. Pourraient être importées comme variantes tarifaires avec un champ `customer_code`.

6. **Fuel surcharge variable** : Le taux fuel est passé de 5% (2024) à potentiellement un autre taux. Faut-il le stocker en config dynamique plutôt qu'en dur ?
