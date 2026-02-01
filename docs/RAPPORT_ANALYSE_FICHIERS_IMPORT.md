# Rapport d'Analyse des Fichiers d'Import
## Analyse des fichiers partenaires pour l'application de devis transport

**Date d'analyse** : Janvier 2025
**Répertoire analysé** : `file_import/`
**Nombre de fichiers** : 12

---

## 1. Synthèse exécutive

### Vue d'ensemble

| Type | Nombre | Utilisable directement | Action requise |
|------|--------|------------------------|----------------|
| **Grilles tarifaires Excel** | 9 | Non | Mapping spécifique par partenaire |
| **Données d'exploitation CSV** | 2 | Non | Exclus (historique, pas tarifs) |
| **Référentiels Excel** | 1 | Oui | Import comme données de référence |

### Constat principal

**Les fichiers ont des formats très hétérogènes.** Chaque partenaire utilise sa propre structure :
- Tarifs par **tranches de poids** (BESSON, BIANCHI)
- Tarifs par **nombre de palettes** (XPO)
- Tarifs par **zones géographiques** (SOGEDIM)
- Combinaisons **origine/destination** avec codes postaux

**Recommandation** : Créer un **mapping de configuration par partenaire** plutôt qu'un parser universel.

---

## 2. Analyse détaillée par fichier

### 2.1 Fichiers CSV - Données d'exploitation (NON utilisables comme tarifs)

#### `extract_377_71_260114_1428 - 2025 ROUTE IMPORT.csv`

| Attribut | Valeur |
|----------|--------|
| **Type** | Historique de transports (récépissés) |
| **Lignes** | 109 543 |
| **Encodage** | UTF-8 avec BOM |
| **Séparateur** | Point-virgule (;) |
| **Utilisation** | Statistiques, analyse - PAS de tarifs |

**Structure des colonnes :**
```
Date de récépissé | Date d'exploitation | Récépissé | Libellé produit vendu |
Ligne départ code | Expéditeur Pays | Pays destinataire | Nombre d'UM |
Poids | Montant Net HT | Montant achat sous-traitance | Incoterm | ...
```

**Exemple de données :**
```
07/08/2024 | INTER IMPORT | BIANCHI TRASPORTI | IT → FR | 568 kg | 86,94 € | DAP
```

**Verdict** : Ce sont des **transactions passées**, pas des grilles tarifaires. Utile pour analyse statistique mais pas pour l'import de tarifs.

---

#### `extract_377_72_260114_1438 - 2025 ROUTE EXPORT.csv`

| Attribut | Valeur |
|----------|--------|
| **Type** | Historique de transports (récépissés) |
| **Lignes** | 105 388 |
| **Structure** | Identique au fichier IMPORT |
| **Utilisation** | Statistiques - PAS de tarifs |

---

### 2.2 Grilles tarifaires Excel - Partenaire BESSON

#### `grille tarifaire2024 BESSON.xlsx`

| Attribut | Valeur |
|----------|--------|
| **Partenaire** | BESSON |
| **Type** | Grille par département et tranches de poids |
| **Feuilles** | 3 (Conditions, Tarifs, Localités) |
| **Utilisable** | Oui avec mapping |

**Structure de la feuille "Tarifs" :**
```
┌─────────┬─────────────┬──────┬───────────────────┬────────┬────────┬────────┬─────────┐
│ Agence  │ Département │ Zone │ Localité          │ 5 KG   │ 10 KG  │ 20 KG  │ 30 KG...│
├─────────┼─────────────┼──────┼───────────────────┼────────┼────────┼────────┼─────────┤
│ NIC     │ 01          │ 1    │ BOURG EN BRESSE   │ 14.52  │ 15.66  │ 17.66  │ 20.23   │
│ NIC     │ 06          │ 1    │ NICE              │ 12.53  │ 13.67  │ 15.38  │ 16.53   │
│ NIC     │ 13          │ 1    │ MARSEILLE         │ 11.97  │ 12.82  │ 13.37  │ 20.88   │
└─────────┴─────────────┴──────┴───────────────────┴────────┴────────┴────────┴─────────┘
```

**Mapping requis :**
```yaml
partenaire: BESSON
format: poids_colonnes
origine_fixe: Monaco/Nice (06)
mapping:
  destination_departement: colonne B
  destination_zone: colonne C
  destination_ville: colonne D
  tranches_poids:
    - colonne: E, poids_max: 5
    - colonne: F, poids_max: 10
    - colonne: G, poids_max: 20
    - colonne: H, poids_max: 30
    # ... etc
```

---

### 2.3 Grilles tarifaires Excel - Partenaire BIANCHI GROUP

#### `ML BIANCHI GROUP PROTOCOLE 01.02.2023 OK FOR 2024 update fuel 1.11.24.xlsx`

| Attribut | Valeur |
|----------|--------|
| **Partenaire** | BIANCHI GROUP |
| **Type** | Multi-feuilles, tarifs par code postal |
| **Feuilles** | 13 (France, Italie, Tunisie, etc.) |
| **Complexité** | Élevée |

**Feuilles disponibles :**
1. PROTOCOLE DISTRIBUTION FRANCE
2. JIT PROTOCOLE
3. LIV ID LOG F13 & FERRERO ALBA
4. TRAFIC FLOS GEN-5%
5. TRAFIC DECATHLON
6. STD DISTRIBUTION ITALY 2023
7. SPECIAL DESTINATIONS IT 2023
8. MANE 2023 -5%
9. ASSOS TUNISIA
10. NATIONAL DISTRIBUTION TUNISIA
11. STD TARIFS TUNISIA
12. FRANCE DISADVANTAGES AREAS
13. ITALY DISADVANTAGES AREAS

**Structure "PROTOCOLE DISTRIBUTION FRANCE" :**
```
┌──────────┬─────────┬─────────────┬─────────────┬──────────────┬──────────┬──────────┐
│ Zip code │ Minimum │ 100/300 kg  │ 301/500 kg  │ 501/1000 kg  │ PRICING  │ T/T      │
├──────────┼─────────┼─────────────┼─────────────┼──────────────┼──────────┼──────────┤
│ 06       │ 9.23    │ 5.5         │ 5.47        │ 5.13         │ €/100kg  │ 24h      │
│ 04       │ 38      │ 33.88       │ 33.88       │ 31.37        │ €/100kg  │ 48/72h   │
│ 13       │ 21      │ 16          │ 14          │ 12           │ €/100kg  │ 24/48h   │
└──────────┴─────────┴─────────────┴─────────────┴──────────────┴──────────┴──────────┘
```

**Particularités :**
- Prix au **100 kg** (pas au kg)
- Délais de livraison inclus
- Tarifs spéciaux par client (MANE, DECATHLON, FERRERO)
- Zones difficiles séparées

---

### 2.4 Grilles tarifaires Excel - Partenaire XPO

#### `XPO 2026.xlsx`

| Attribut | Valeur |
|----------|--------|
| **Partenaire** | XPO |
| **Type** | Tarifs par palette |
| **Origine** | Nice / Monaco (06510 CARROS) |
| **Feuilles** | 6 |

**Structure "TARIFS 2026" :**
```
┌───────────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│ DESTINATION           │ 1 pal.   │ 2 pal.   │ 3 pal.   │ 4 pal.   │ 5 pal.   │ 6 pal.   │
├───────────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ 01 - Ain              │ 67.62    │ 106.22   │ 139.08   │ 185.46   │ 207.65   │ 249.11   │
│ 02 - Aisne            │ 99.79    │ 169.18   │ 229.60   │ 306.14   │ 360.42   │ 429.30   │
└───────────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

**Feuilles supplémentaires :**
- Prestations complémentaires
- Taxe grandes villes
- Taxe localités et accès difficiles
- Carte de délais

**Particularités :**
- Tarifs au **forfait par palette** (pas au poids)
- Taxes supplémentaires en feuilles séparées
- Palettes standard 80x120

---

### 2.5 Grilles tarifaires Excel - Partenaire SOGEDIM

#### `Tarif ML - SOGEDIM 2025.xlsx`

| Attribut | Valeur |
|----------|--------|
| **Partenaire** | SOGEDIM |
| **Type** | Bilatéral France ↔ Italie par zones |
| **Feuilles** | 22 |
| **Complexité** | Très élevée |

**Feuilles principales :**
- TARIFF BILATERAL FR.IT
- TRANSIT TIMES FR/IT
- BILATERAL CUSTOMS CLEARANCE
- TARIFF TUNISIA MONACO
- Zones difficiles FR/IT
- Export vers TR, UK, CH, CY, GR, DK, SE, FI, PL
- Import depuis NL, BE

**Structure "TARIFF BILATERAL FR.IT" :**
```
Matrice zones FR (colonnes) × zones IT (lignes) × tranches poids

ZONES FR:
- 98-06 (Monaco/Nice)
- 13, 34, 30 (Marseille, Montpellier, Nîmes)
- 83, 84, 26 (Var, Vaucluse, Drôme)
- 20 (Corse)

ZONES IT:
- 20, 21, 28 (Milan, Côme, Novare)
- 10, 13 (Turin, Alexandrie)
- 30-31-35-37 (Vénétie)
- 00-06 (Rome, Latium)
- 70-76, 80-86 (Sud)
- 07-09, 90-98 (Sardaigne, Sicile)

TRANCHES POIDS:
Min.Charge | 101-200 KG | 201-300 KG | ... | 901-1000 KG | 1001-1100 KG
```

**Complexité** : Chaque cellule = prix pour (zone FR, zone IT, tranche poids)

---

### 2.6 Autres fichiers Excel

#### `PROVENCE 2026.xlsx`

| Attribut | Valeur |
|----------|--------|
| **Partenaire** | PROVENCE DISTRIBUTION LOGISTIQUE |
| **Feuilles** | DEPART 83-06, RETOUR 83-06, ADR, CGV, Délais |
| **Type** | Tarifs aller/retour avec ADR (matières dangereuses) |

#### `ALBINI VIGNATE 2023.xlsx`

| Attribut | Valeur |
|----------|--------|
| **Partenaire** | ALBINI & PITIGLIANI SPA |
| **Type** | Enlèvement/distribution Italie |
| **Structure** | Simple |

#### `PROTOCOLLO NT-MonacoLogistique Ott 2020 - agg.to 01.01.2023.xlsx`

| Attribut | Valeur |
|----------|--------|
| **Partenaire** | NUOVA TRASPORTI SPA |
| **Type** | Protocole bilatéral Monaco ↔ Italie |
| **Feuilles** | 8 (Tarifs Monaco, NT, SI, XS, HR, PT, GR) |

#### `Liste localites haute Montagne 06.2016.xlsx`

| Attribut | Valeur |
|----------|--------|
| **Type** | Référentiel des communes difficiles d'accès |
| **Utilisation** | Données de référence pour surcharges |
| **Structure** | Département, Code, Commune, Type (Montagnes/Iles) |

---

## 3. Analyse des formats

### 3.1 Types de structures tarifaires identifiées

| Type | Partenaires | Description |
|------|-------------|-------------|
| **Poids en colonnes** | BESSON | Prix fixe par tranche de poids (5kg, 10kg, 20kg...) |
| **Poids en lignes** | SOGEDIM, BIANCHI | Tranches de poids en lignes (101-200kg, 201-300kg...) |
| **Palettes** | XPO | Forfait par nombre de palettes |
| **Prix au 100kg** | BIANCHI | Prix × (poids/100) |
| **Matrice zones** | SOGEDIM | Zone origine × Zone destination |

### 3.2 Variables tarifaires identifiées

| Variable | Présence | Exemples |
|----------|----------|----------|
| **Code postal origine** | Fréquent | 06, 98, 13, 83 |
| **Code postal destination** | Toujours | Département ou CP complet |
| **Poids** | Très fréquent | Tranches ou au kg |
| **Volume** | Rare | XPO (palettes) |
| **Délai** | Parfois | 24h, 48h, 72h |
| **Type marchandise** | Rare | ADR (matières dangereuses) |
| **Zone difficile** | Souvent | Montagne, îles, surcharges |

### 3.3 Complexités identifiées

| Complexité | Description | Impact |
|------------|-------------|--------|
| **Multi-feuilles** | Tarifs répartis sur plusieurs onglets | Parser toutes les feuilles |
| **En-têtes multiples** | Plusieurs lignes d'en-tête | Détecter la ligne de données |
| **Cellules fusionnées** | Headers sur plusieurs colonnes | Gérer les merges |
| **Formules** | Prix calculés | Utiliser data_only=True |
| **Zones codées** | 20(1), 20(2) pour Corse | Mapping personnalisé |
| **Surcharges séparées** | Taxes en feuilles différentes | Jointure des données |

---

## 4. Recommandations techniques

### 4.1 Architecture d'import proposée

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SYSTÈME D'IMPORT                                      │
│                                                                              │
│  ┌─────────────────┐                                                        │
│  │ Fichier Excel   │                                                        │
│  │ du partenaire   │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐     ┌─────────────────────────────────────────────┐   │
│  │  Détection      │     │         CONFIGURATIONS PARTENAIRES          │   │
│  │  partenaire     │────▶│                                             │   │
│  └────────┬────────┘     │  besson.yaml    bianchi.yaml    xpo.yaml   │   │
│           │              │  sogedim.yaml   provence.yaml   albini.yaml│   │
│           │              │                                             │   │
│           │              └─────────────────────────────────────────────┘   │
│           │                              │                                  │
│           ▼                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PARSER CONFIGURABLE                               │   │
│  │                                                                      │   │
│  │  • Lecture feuille(s) spécifiée(s)                                  │   │
│  │  • Détection ligne d'en-tête                                        │   │
│  │  • Mapping colonnes selon config                                    │   │
│  │  • Transformation des données                                       │   │
│  │  • Expansion des tranches de poids                                  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│           │                                                                  │
│           ▼                                                                  │
│  ┌─────────────────┐                                                        │
│  │  Format normalisé│                                                       │
│  │  (JSON/DB)       │                                                       │
│  └─────────────────┘                                                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Configuration partenaire (exemple BESSON)

```yaml
# config/partners/besson.yaml
partner:
  id: besson
  name: BESSON
  code: BESS

file_detection:
  patterns:
    - "*BESSON*.xlsx"
    - "*besson*.xlsx"

import:
  sheet: "Tarifs"
  header_row: 1
  data_start_row: 2

  origin:
    fixed: true
    city: "Nice"
    country: "FR"
    postal_code: "06"

  mapping:
    destination_department:
      column: "B"
      type: "department_code"
    destination_zone:
      column: "C"
    destination_city:
      column: "D"

  pricing:
    type: "weight_columns"
    currency: "EUR"
    columns:
      - column: "E", weight_max: 5, label: "5 KG"
      - column: "F", weight_max: 10, label: "10 KG"
      - column: "G", weight_max: 20, label: "20 KG"
      - column: "H", weight_max: 30, label: "30 KG"
      - column: "I", weight_max: 40, label: "40 KG"
      - column: "J", weight_max: 50, label: "50 KG"
      # ... etc

  transport_mode: "road"
```

### 4.3 Configuration partenaire (exemple XPO - palettes)

```yaml
# config/partners/xpo.yaml
partner:
  id: xpo
  name: XPO
  code: XPO

file_detection:
  patterns:
    - "*XPO*.xlsx"

import:
  sheet: "42545 - TARIFS 2026"
  header_row: 17
  data_start_row: 19

  origin:
    fixed: true
    city: "Carros"
    country: "FR"
    postal_code: "06510"

  mapping:
    destination:
      column: "A"
      type: "department_with_name"  # "01 - Ain"

  pricing:
    type: "pallet_columns"
    currency: "EUR"
    pallet_size: "80x120"
    columns:
      - column: "B", pallets: 1
      - column: "C", pallets: 2
      - column: "D", pallets: 3
      - column: "E", pallets: 4
      - column: "F", pallets: 5
      - column: "G", pallets: 6

  transport_mode: "road"

  supplements:
    - sheet: "Taxe grandes villes"
      type: "city_surcharge"
    - sheet: "Taxe localités et accès difficiles"
      type: "difficult_access_surcharge"
```

### 4.4 Format de données normalisé (cible)

```typescript
interface NormalizedQuote {
  partner_id: string;
  transport_mode: 'road' | 'rail' | 'sea' | 'air';

  origin: {
    postal_code?: string;
    department?: string;
    city?: string;
    country: string;
    zone?: string;
  };

  destination: {
    postal_code?: string;
    department?: string;
    city?: string;
    country: string;
    zone?: string;
  };

  // Critères
  weight_min?: number;  // kg
  weight_max?: number;  // kg
  pallet_count?: number;

  // Prix
  cost: number;
  cost_type: 'fixed' | 'per_100kg' | 'per_kg' | 'per_pallet';
  currency: string;

  // Délai
  delivery_time?: string;  // "24h", "48h", "72h"

  // Validité
  valid_from: Date;
  valid_until?: Date;

  // Métadonnées
  source_file: string;
  source_sheet: string;
  source_row: number;
}
```

---

## 5. Plan d'implémentation

### Phase 1 : Partenaires prioritaires (format simple)

| Partenaire | Complexité | Priorité |
|------------|------------|----------|
| **BESSON** | Moyenne | 1 |
| **XPO** | Moyenne | 2 |
| **BIANCHI (France)** | Moyenne | 3 |

### Phase 2 : Partenaires complexes

| Partenaire | Complexité | Priorité |
|------------|------------|----------|
| **SOGEDIM** | Élevée (matrice zones) | 4 |
| **PROVENCE** | Moyenne (ADR) | 5 |
| **BIANCHI (Multi-pays)** | Élevée | 6 |

### Phase 3 : Référentiels

| Fichier | Utilisation |
|---------|-------------|
| **Liste localités haute Montagne** | Surcharges zones difficiles |
| **Taxes grandes villes** | Surcharges urbaines |

---

## 6. Réponse à votre question sur la documentation

### Le fichier `DOCUMENTATION_TECHNIQUE_FONCTIONNELLE.md` est-il encore d'actualité ?

**Non**, ce fichier est **obsolète**. Il a été remplacé par :

| Ancien fichier | Nouveau fichier | Statut |
|----------------|-----------------|--------|
| `DOCUMENTATION_TECHNIQUE_FONCTIONNELLE.md` | `DOCUMENTATION_SIMPLIFIEE.md` | **À utiliser** |

**Recommandation** : Supprimer ou archiver l'ancien fichier pour éviter toute confusion.

```bash
# Option 1 : Supprimer
rm docs/DOCUMENTATION_TECHNIQUE_FONCTIONNELLE.md

# Option 2 : Archiver
mv docs/DOCUMENTATION_TECHNIQUE_FONCTIONNELLE.md docs/archive/
```

### Documents actuels valides

| Document | Description |
|----------|-------------|
| `docs/DOCUMENTATION_SIMPLIFIEE.md` | Documentation principale |
| `docs/IMPORT_TARIFS_PARTENAIRES.md` | Solutions techniques d'import |
| `docs/RAPPORT_ANALYSE_FICHIERS_IMPORT.md` | Ce rapport |
| `PROPOSITIONS_ARCHITECTURE.md` | Propositions d'architecture |

---

## 7. Conclusion

### Constats

1. **Formats hétérogènes** : Chaque partenaire a son propre format
2. **Données d'exploitation ≠ Tarifs** : Les CSV sont des historiques, pas des grilles
3. **Complexité variable** : De simple (BESSON) à très complexe (SOGEDIM)

### Recommandations

1. **Approche par configuration** : Un fichier YAML par partenaire
2. **Parser configurable** : Un seul parser piloté par la config
3. **Validation humaine** : Prévisualisation obligatoire avant import
4. **Priorité** : Commencer par BESSON et XPO (formats les plus simples)

### Effort estimé

| Composant | Effort |
|-----------|--------|
| Parser Excel configurable | Moyen |
| Configuration BESSON | Faible |
| Configuration XPO | Faible |
| Configuration SOGEDIM | Élevé |
| Interface de prévisualisation | Moyen |

---

*Rapport généré pour le projet Transport Quote*
