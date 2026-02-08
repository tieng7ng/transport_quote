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

## Feuille 3 : Tarifs Slovénie (3.rates SI) - Phase 2

### 3.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `3.rates SI` |
| Origine | Melzo (Terminal), Italie |
| Destinations | Slovénie |
| Mode transport | Route (ROAD) |
| Statut | 📋 À faire |

### 3.2 Structure attendue

Cette feuille suit probablement une structure similaire à la feuille 2.TARIFS NT avec des destinations par ville/région de Slovénie.

---

## Feuille 4 : Tarifs Serbie (4.rates XS) - Phase 2

### 4.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `4.rates XS` |
| Origine | Melzo (Terminal), Italie |
| Destinations | Serbie (code pays ISO : `RS`) |
| Mode transport | Route (ROAD) |
| Layout | `zone_matrix` |
| Header row | 11 (0-indexed: 10) |
| Statut | 📋 À faire |

### 4.2 Structure de la feuille Excel

La feuille contient **3 sections** :

1. **Rows 11-41** : Matrice tarifs (zones × poids)
2. **Rows 42-44** : Délais de livraison et frais de transit
3. **Rows 46-68** : Table de correspondance zones → codes postaux

#### Section 1 : Matrice tarifaire (rows 11-41)

La colonne `Kg` contient les tranches de poids, les colonnes `A` à `H` sont des zones tarifaires.

```
Row 11 (header):
┌────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│   Kg   │   A    │   B    │   C    │   D    │   E    │   F    │   G    │   H    │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┘

Row 12+ (données):
┌────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│  0-20  │ 32.23  │ 34.09  │ 38.15  │ 41.01  │ 45.53  │ 47.63  │ 51.40  │ 53.65  │
│  -50   │ 34.49  │ 36.60  │ 41.47  │ 44.63  │ 49.74  │ 51.85  │ 55.91  │ 58.17  │
│  -100  │ 36.19  │ 38.48  │ 43.95  │ 47.33  │ 52.90  │ 55.01  │ 59.30  │ 61.55  │
│  ...   │  ...   │  ...   │  ...   │  ...   │  ...   │  ...   │  ...   │  ...   │
│ -10000 │1128.54 │1179.71 │1233.03 │1296.70 │1336.63 │1376.43 │1412.90 │1440.59 │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```

#### Section 2 : Délais et frais (rows 42-44)

| Row | Donnée | A | B | C | D | E | F | G | H |
|-----|--------|---|---|---|---|---|---|---|---|
| 42 | Lead time (cleared) | 24h | 24h | 24h | 24h | 24h | 24h | 24h | 24h |
| 43 | Lead time (uncleared) | 24h | 48h | 48h | 48h | 48h | 48h | 48h | 48h |
| 44 | Fee transit doc | 20€ | 20€ | 20€ | 20€ | 20€ | 20€ | 20€ | 20€ |

#### Section 3 : Table zones → codes postaux (rows 46-68)

Les zones `A` à `H` sont des **alias** qui correspondent à des codes postaux serbes. La table de correspondance se trouve en bas de la feuille (4 paires de colonnes `Postcodes | Zone`) :

| Zone | Codes postaux |
|------|---------------|
| **A** | 110, 111, 112, 220, 223, 224 |
| **B** | 113, 114, 115, 142, 143, 150, 152, 153, 210, 211, 212, 222, 260, 262 |
| **C** | 120, 122, 123, 140, 214, 230, 243, 263, 343, 2521, 2522, 2523, 2524, 2525, 3420, 3421, 3422 |
| **D** | 233, 240, 241, 242, 244, 250, 320, 322, 323, 340, 350, 352, 2526, 2527, 2528, 3125, 3126, 3423, 3424 |
| **E** | 310, 360, 361, 362, 370, 3120, 3121, 3122, 3123, 3124 |
| **F** | 180, 182, 184, 192, 363, 372, 3131, 3133 |
| **G** | 160, 162, 190, 193, 3130, 3132 |
| **H** | 170, 175, 181, 183 |

### 4.3 Colonne Kg : tranches de poids cumulatives

La colonne `Kg` utilise une notation **cumulative** où chaque ligne dépend de la précédente :

- `0-20` : explicite, de 0 à 20 kg
- `-50` : signifie "jusqu'à 50 kg", donc de **21** à 50 kg (weight_max précédent + 1)
- `-100` : de **51** à 100 kg
- etc.

#### Grille complète des tranches

| Valeur Excel | `weight_min` | `weight_max` | Règle |
|---|---|---|---|
| `0-20` | 0 | 20 | Plage explicite |
| `-50` | 21 | 50 | Précédent max (20) + 1 |
| `-100` | 51 | 100 | Précédent max (50) + 1 |
| `-150` | 101 | 150 | Précédent max (100) + 1 |
| `-200` | 151 | 200 | Précédent max (150) + 1 |
| `-250` | 201 | 250 | Précédent max (200) + 1 |
| `-300` | 251 | 300 | Précédent max (250) + 1 |
| `-350` | 301 | 350 | Précédent max (300) + 1 |
| `-400` | 351 | 400 | Précédent max (350) + 1 |
| `-500` | 401 | 500 | Précédent max (400) + 1 |
| `-600` | 501 | 600 | Précédent max (500) + 1 |
| `-700` | 601 | 700 | Précédent max (600) + 1 |
| `-800` | 701 | 800 | Précédent max (700) + 1 |
| `-900` | 801 | 900 | Précédent max (800) + 1 |
| `-1000` | 901 | 1000 | Précédent max (900) + 1 |
| `-1100` | 1001 | 1100 | Précédent max (1000) + 1 |
| `-1200` | 1101 | 1200 | Précédent max (1100) + 1 |
| `-1300` | 1201 | 1300 | Précédent max (1200) + 1 |
| `-1400` | 1301 | 1400 | Précédent max (1300) + 1 |
| `-1500` | 1401 | 1500 | Précédent max (1400) + 1 |
| `-2000` | 1501 | 2000 | Précédent max (1500) + 1 |
| `-2500` | 2001 | 2500 | Précédent max (2000) + 1 |
| `-3000` | 2501 | 3000 | Précédent max (2500) + 1 |
| `-4000` | 3001 | 4000 | Précédent max (3000) + 1 |
| `-5000` | 4001 | 5000 | Précédent max (4000) + 1 |
| `-6000` | 5001 | 6000 | Précédent max (5000) + 1 |
| `-7000` | 6001 | 7000 | Précédent max (6000) + 1 |
| `-8000` | 7001 | 8000 | Précédent max (7000) + 1 |
| `-9000` | 8001 | 9000 | Précédent max (8000) + 1 |
| `-10000` | 9001 | 10000 | Précédent max (9000) + 1 |

#### Représentation en BD (table `partner_quotes`)

Lors de l'import, chaque zone (A, B, ...) doit être **éclatée** en ses codes postaux réels. Chaque combinaison (tranche de poids × code postal) génère **une ligne** en BD.

Exemple : la zone A (tarif 32.23€ pour 0-20 kg) contient les codes postaux 110, 111, 112, 220, 223, 224. Cela produit **6 lignes** :

| `weight_min` | `weight_max` | `cost` | `dest_postal_code` | `dest_country` | `pricing_type` |
|---|---|---|---|---|---|
| 0 | 20 | 32.23 | 110 | RS | LUMPSUM |
| 0 | 20 | 32.23 | 111 | RS | LUMPSUM |
| 0 | 20 | 32.23 | 112 | RS | LUMPSUM |
| 0 | 20 | 32.23 | 220 | RS | LUMPSUM |
| 0 | 20 | 32.23 | 223 | RS | LUMPSUM |
| 0 | 20 | 32.23 | 224 | RS | LUMPSUM |

Au total : 30 tranches de poids × ~78 codes postaux = **~2340 lignes** en BD pour la Serbie.

#### Impact sur le code

Deux corrections sont nécessaires dans `column_mapper.py` pour le layout `zone_matrix` :

1. **Tranches cumulatives** : La méthode `_parse_weight_key()` traite actuellement chaque ligne **isolément** : `-50` donne `(0, 50)` au lieu de `(21, 50)`. Le traitement doit conserver le `weight_max` de la ligne précédente et l'utiliser comme `weight_min + 1` de la ligne courante.

2. **Résolution zones → codes postaux** : Actuellement `dest_postal_code` reçoit la lettre de zone (`A`, `B`, ...). L'import doit lire la table de correspondance (rows 46-68) et éclater chaque zone en autant de lignes que de codes postaux associés.

### 4.4 Règles métier spécifiques (rows 70-82)

#### Calcul du poids taxable
```
Poids taxable = MAX(poids réel, poids volumétrique)

Équivalences :
- 1 m³ = 250 kg
- 1 mètre linéaire (ldm) = 1500 kg
```

#### Surcharges et frais

| Surcharge | Montant | Condition |
|-----------|---------|-----------|
| Handling Melzo | 1,00 € / 100 kg | Poids réel |
| ADR (matières dangereuses) | +10% sur tarif de base | Minimum 5,00 € |
| Dédouanement export (avec EORI) | 35,00 € | Par envoi |
| Fuel surcharge | +8% | Depuis le 01/12/2022 |
| Fee transit doc Serbie | 20,00 € | Par envoi dédouané hors terminal Belgrade |

#### Tarification
- Prix en EUR **par envoi** (LUMPSUM)
- Départ le vendredi

### 4.5 Configuration technique

```yaml
- name: "serbia"
  sheet_name: "4.rates XS"
  header_row: 10
  layout: "zone_matrix"
  defaults:
    transport_mode: "ROAD"
    origin_country: "IT"
    origin_city: "MELZO"
    dest_country: "RS"
    dest_city: "ALL"
    currency: "EUR"
  zone_matrix:
    weight_column: "Kg"
    zone_to_postcodes:
      A: ["110", "111", "112", "220", "223", "224"]
      B: ["113", "114", "115", "142", "143", "150", "152", "153", "210", "211", "212", "222", "260", "262"]
      C: ["120", "122", "123", "140", "214", "230", "243", "263", "343", "2521", "2522", "2523", "2524", "2525", "3420", "3421", "3422"]
      D: ["233", "240", "241", "242", "244", "250", "320", "322", "323", "340", "350", "352", "2526", "2527", "2528", "3125", "3126", "3423", "3424"]
      E: ["310", "360", "361", "362", "370", "3120", "3121", "3122", "3123", "3124"]
      F: ["180", "182", "184", "192", "363", "372", "3131", "3133"]
      G: ["160", "162", "190", "193", "3130", "3132"]
      H: ["170", "175", "181", "183"]
```

---

## Feuille 5 : Tarifs Croatie (5.rates HR) - Phase 2

### 5.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `5.rates HR` |
| Origine | Melzo (Terminal), Italie |
| Destinations | Croatie (code pays ISO : `HR`) |
| Mode transport | Route (ROAD) |
| Layout | `zone_matrix` |
| Header row | 10 (0-indexed: 9) |
| Statut | 📋 À faire |

### 5.2 Structure de la feuille Excel

La feuille contient **3 sections** :

1. **Rows 10-36** : Matrice tarifs (zones × poids)
2. **Rows 38-51** : Table de correspondance zones → codes postaux
3. **Rows 53-71** : Conditions générales, délais de livraison et contacts

#### Section 1 : Matrice tarifaire (rows 10-36)

La colonne `Kg` contient les tranches de poids, les colonnes `A` à `G` sont des zones tarifaires (7 zones).

```
Row 10 (header):
┌────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│   Kg   │   A    │   B    │   C    │   D    │   E    │   F    │   G    │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┘

Row 11+ (données):
┌────────┬────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│  100   │ 49.85  │ 50.25  │ 51.28  │ 54.25  │ 56.45  │ 66.96  │ 72.39  │
│  200   │ 60.37  │ 60.80  │ 61.72  │ 73.23  │ 75.12  │ 80.19  │ 96.67  │
│  300   │ 79.34  │ 81.85  │ 85.06  │ 98.85  │106.93  │112.01  │127.41  │
│  ...   │  ...   │  ...   │  ...   │  ...   │  ...   │  ...   │  ...   │
│ 3000   │556.94  │581.19  │615.84  │660.25  │682.69  │821.55  │889.69  │
└────────┴────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```

#### Section 2 : Table zones → codes postaux (rows 38-51)

Les zones `A` à `G` sont des **alias** qui correspondent à des préfixes de codes postaux croates. La table de correspondance se trouve en dessous de la matrice (4 paires de colonnes `Postcodes | Zone`) :

| Zone | Codes postaux | Région |
|------|---------------|--------|
| **A** | 10000 | Zagreb centre |
| **B** | 10290, 10340, 10370, 10410, 10430 | Banlieue de Zagreb |
| **C** | 42000, 42240, 43000, 44000, 44310, 44320, 47000, 49000, 49210 | Croatie du Nord/Centre (Varazdin, Bjelovar, Sisak, Karlovac, Krapina) |
| **D** | 33000, 33520, 40000, 48000 | Centre-Nord (Virovitica, Cakovec, Koprivnica) |
| **E** | 31000, 31400, 32000, 32100, 32270, 34000, 35000, 51000, 51300, 53000, 53220, 53270 | Slavonie Est + Rijeka + Lika (Osijek, Vukovar, Pozega, Slavonski Brod, Rijeka, Gospic) |
| **F** | 21000, 21260, 21300, 22000, 22320, 52000, 52210, 52440, 52470 | Côte dalmate + Istrie (Split, Sibenik, Pula) |
| **G** | 20000, 20340, 20350 | Région de Dubrovnik |

**Note** : Les codes postaux sont des **préfixes**. Par exemple, le code 10290 correspond à toutes les localités dont le code postal commence par 10290.

#### Section 3 : Conditions générales et délais (rows 53-71)

| Row | Donnée |
|-----|--------|
| 53 | General conditions |
| 54 | 1 cbm = 250 kg, 1 ldm = 1500 kg |
| 55 | Handling in Melzo : 1,00 € / 100 kg real weight |
| 56 | Handling in Zagreb : 1,50 € / 100 kg real weight |
| 57 | Rates in EUR per each shipment |
| 58 | ADR shipments + 10% |
| 59 | Islands + 50% |
| 61 | Fuel surcharge: from 01/12/22 + 8% |
| 63-66 | Lead time (voir détails ci-dessous) |
| 67 | Departure on Friday |

### 5.3 Colonne Kg : tranches de poids cumulatives

La colonne `Kg` contient des **valeurs simples** représentant le poids maximum de chaque tranche. Le poids minimum est déduit du maximum de la tranche précédente + 1 :

- `100` : de 0 à 100 kg (première tranche)
- `200` : de **101** à 200 kg (précédent max (100) + 1)
- `300` : de **201** à 300 kg
- etc.

**Attention** : Les tranches ne sont **pas régulières** — des paliers irréguliers apparaissent (1200→1250, 1700→1750, 1900→2000, 2000→2200).

#### Grille complète des tranches

| Valeur Excel | `weight_min` | `weight_max` | Règle |
|---|---|---|---|
| `100` | 0 | 100 | Première tranche |
| `200` | 101 | 200 | Précédent max (100) + 1 |
| `300` | 201 | 300 | Précédent max (200) + 1 |
| `400` | 301 | 400 | Précédent max (300) + 1 |
| `500` | 401 | 500 | Précédent max (400) + 1 |
| `600` | 501 | 600 | Précédent max (500) + 1 |
| `700` | 601 | 700 | Précédent max (600) + 1 |
| `800` | 701 | 800 | Précédent max (700) + 1 |
| `900` | 801 | 900 | Précédent max (800) + 1 |
| `1000` | 901 | 1000 | Précédent max (900) + 1 |
| `1100` | 1001 | 1100 | Précédent max (1000) + 1 |
| `1200` | 1101 | 1200 | Précédent max (1100) + 1 |
| `1250` | 1201 | 1250 | Précédent max (1200) + 1 |
| `1300` | 1251 | 1300 | Précédent max (1250) + 1 |
| `1400` | 1301 | 1400 | Précédent max (1300) + 1 |
| `1500` | 1401 | 1500 | Précédent max (1400) + 1 |
| `1600` | 1501 | 1600 | Précédent max (1500) + 1 |
| `1700` | 1601 | 1700 | Précédent max (1600) + 1 |
| `1750` | 1701 | 1750 | Précédent max (1700) + 1 |
| `1900` | 1751 | 1900 | Précédent max (1750) + 1 |
| `2000` | 1901 | 2000 | Précédent max (1900) + 1 |
| `2200` | 2001 | 2200 | Précédent max (2000) + 1 |
| `2250` | 2201 | 2250 | Précédent max (2200) + 1 |
| `2500` | 2251 | 2500 | Précédent max (2250) + 1 |
| `2750` | 2501 | 2750 | Précédent max (2500) + 1 |
| `3000` | 2751 | 3000 | Précédent max (2750) + 1 |

#### Représentation en BD (table `partner_quotes`)

Lors de l'import, chaque zone (A, B, ...) doit être **éclatée** en ses codes postaux réels. Chaque combinaison (tranche de poids × code postal) génère **une ligne** en BD.

Exemple : la zone A (tarif 49.85€ pour 0-100 kg) contient le code postal 10000. Cela produit **1 ligne** :

| `weight_min` | `weight_max` | `cost` | `dest_postal_code` | `dest_country` | `pricing_type` |
|---|---|---|---|---|---|
| 0 | 100 | 49.85 | 10000 | HR | LUMPSUM |

La zone E (tarif 56.45€ pour 0-100 kg) contient 12 codes postaux, ce qui produit **12 lignes** pour cette seule tranche.

Au total : 26 tranches de poids × ~42 codes postaux = **~1092 lignes** en BD pour la Croatie.

#### Impact sur le code

Le parsing est similaire à la feuille Serbie (`zone_matrix`) avec deux différences :

1. **Format de la colonne Kg** : Les valeurs sont des entiers simples (`100`, `200`, `300`...) au lieu de la notation cumulative avec tiret (`0-20`, `-50`, `-100`...). La méthode `_parse_weight_key()` doit gérer ce format.

2. **Codes postaux 5 chiffres** : Les codes postaux croates sont des préfixes à 5 chiffres (ex: `10000`, `21000`) contrairement aux codes serbes à 3 chiffres.

### 5.4 Règles métier spécifiques (rows 53-67)

#### Calcul du poids taxable
```
Poids taxable = MAX(poids réel, poids volumétrique)

Équivalences :
- 1 m³ = 250 kg
- 1 mètre linéaire (ldm) = 1500 kg
```

#### Surcharges et frais

| Surcharge | Montant | Condition |
|-----------|---------|-----------|
| Handling Melzo | 1,00 € / 100 kg | Poids réel |
| Handling Zagreb | 1,50 € / 100 kg | Poids réel |
| ADR (matières dangereuses) | +10% sur tarif de base | |
| Îles | +50% sur tarif de base | |
| Fuel surcharge | +8% | Depuis le 01/12/2022 |

**Note** : Contrairement à la Serbie, la Croatie a un **double handling** (Melzo + Zagreb).

#### Délais de livraison

| Destination | Délai |
|-------------|-------|
| Général (toutes zones sauf G et îles) | 24h |
| Dubrovnik et environs (Zone G) | 48h |
| Îles | Sur demande (dépend des ferries, horaire été/hiver) |

#### Tarification
- Prix en EUR **par envoi** (LUMPSUM)
- Départ le vendredi

### 5.5 Exemples de tarifs

| Kg | Zone A (Zagreb) | Zone C (Varazdin) | Zone E (Osijek/Rijeka) | Zone G (Dubrovnik) |
|----|-----------------|-------------------|------------------------|---------------------|
| 100 | 49,85€ | 51,28€ | 56,45€ | 72,39€ |
| 500 | 125,60€ | 135,76€ | 149,78€ | 170,26€ |
| 1000 | 231,40€ | 265,72€ | 293,11€ | 325,71€ |
| 2000 | 434,22€ | 491,61€ | 531,54€ | 638,62€ |
| 3000 | 556,94€ | 615,84€ | 682,69€ | 889,69€ |

### 5.6 Configuration technique

```yaml
- name: "croatia"
  sheet_name: "5.rates HR"
  header_row: 9
  layout: "zone_matrix"
  defaults:
    transport_mode: "ROAD"
    origin_country: "IT"
    origin_city: "MELZO"
    dest_country: "HR"
    dest_city: "ALL"
    currency: "EUR"
  zone_matrix:
    weight_column: "Kg"
    zone_to_postcodes:
      A: ["10000"]
      B: ["10290", "10340", "10370", "10410", "10430"]
      C: ["42000", "42240", "43000", "44000", "44310", "44320", "47000", "49000", "49210"]
      D: ["33000", "33520", "40000", "48000"]
      E: ["31000", "31400", "32000", "32100", "32270", "34000", "35000", "51000", "51300", "53000", "53220", "53270"]
      F: ["21000", "21260", "21300", "22000", "22320", "52000", "52210", "52440", "52470"]
      G: ["20000", "20340", "20350"]
```

---

## Feuille 6 : Tarifs Portugal (6.rates PT) - Phase 2

### 6.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `6.rates PT` |
| Origine | Melzo (Terminal), Italie |
| Destinations | Portugal |
| Mode transport | Route (ROAD) |
| Statut | 📋 À faire |

### 6.2 Structure attendue

Cette feuille suit probablement une structure similaire à la feuille 2.TARIFS NT avec des destinations par ville/région du Portugal.

---

## Feuille 7 : Tarifs Grèce (7-rates GR-ADReNON) - Phase 2

### 7.1 Périmètre fonctionnel

| Élément | Valeur |
|---------|--------|
| Feuille Excel | `7-rates GR-ADReNON` |
| Origine | Melzo (Terminal), Italie |
| Destinations | Grèce |
| Mode transport | Route (ROAD) |
| Statut | 📋 À faire |

### 7.2 Structure attendue

Cette feuille suit probablement une structure similaire à la feuille 2.TARIFS NT avec des destinations par ville/région de Grèce.

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

---

## 8. Exemples de Calculs Détaillés

Cette section illustre le calcul du prix final (surcharges incluses) pour différents scénarios.

### 8.1 France (Feuille 1 - Nice vers Départements)

**Scénario : Envoi de 250 kg vers Marseille (13)**
- **Données** : 2 palettes, Poids réel 250 kg, Volume 1.2 m³.
- **1. Poids Taxable** :
  - Règle France : **1 m³ = 250 kg**.
  - Poids volume : $1.2 \times 250 = 300 \text{ kg}$.
  - Poids retenu : **300 kg** (MAX(250, 300)).
- **2. Prix de base (PER_100KG)** :
  - Tranche : 100/300 kg.
  - Tarif (exemple) : **17,00 €** / 100 kg.
  - Unités payantes : $300 / 100 = 3$.
  - Calcul : $17,00 \times 3 = \textbf{51,00 €}$.
- **3. Surcharges** :
  - Fuel Surcharge (+8%) : $51,00 \times 0.08 = 4,08 \text{ €}$.
- **PRIX TOTAL : 55,08 €**

**Scénario : Envoi de 1200 kg vers Var (83)**
- **Données** : Poids retenu 1200 kg.
- **1. Prix de base (LUMPSUM)** :
  - Tranche : 1001/1500 kg.
  - Type : **Forfait** (LUMPSUM).
  - Tarif (exemple) : **145,00 €**.
- **2. Surcharges** :
  - Fuel Surcharge (+8%) : $145,00 \times 0.08 = 11,60 \text{ €}$.
- **PRIX TOTAL : 156,60 €**

### 8.2 Italie (Feuille 2 - Melzo vers Provinces)

**Scénario : Envoi de 350 kg vers Roma (00)**
- **Données** : Poids réel 350 kg, 1 m³.
- **1. Poids Taxable** :
  - Règle Italie : **1 m³ = 300 kg** (Différent de la France !).
  - Poids volume : $1 \times 300 = 300 \text{ kg}$.
  - Poids retenu : **350 kg** (MAX(350, 300)).
  - Arrondi (au 100kg sup.) : **400 kg**.
- **2. Prix de base (PER_100KG)** :
  - Tranche : Till 500 kgs.
  - Tarif Roma (exemple) : **14,50 €** / 100 kg.
  - Calcul : $14,50 \times (400 / 100) = \textbf{58,00 €}$.
- **3. Surcharges** :
  - **Handling Melzo** (1,00 € / 100kg) : $1,00 \times (400 / 100) = \textbf{4,00 €}$.
  - **Fuel Surcharge** (+8% sur Transport + Handling) :
    - Base : $58,00 + 4,00 = 62,00 \text{ €}$.
    - Fuel : $62,00 \times 0.08 = 4,96 \text{ €}$.
- **PRIX TOTAL : 66,96 €**

### 8.3 International (Feuilles 3 à 7 - Melzo vers Europe)

Les règles sont identiques à celles de l'Italie (Ratio 1:300, Handling, Fuel) avec des frais fixes additionnels (Douane, Booking).

**Scénario : Colis de 15 kg vers Belgrade, Serbie (Zone A)**
- **Données** : Poids réel 15 kg.
- **1. Prix de base (LUMPSUM)** :
  - Tranche : 0-20 kg.
  - Zone : A (Belgrade).
  - Tarif (exemple) : **32,23 €**.
- **2. Surcharges** :
  - **Handling Melzo** (Min 100kg) : $1,00 \times 1 = \textbf{1,00 €}$.
  - **Booking Fee** : **8,00 €**.
  - **Dédouanement Export** : **35,00 €**.
- **3. Fuel Surcharge** (+8% sur Transport + Handling) :
  - Base : $32,23 + 1,00 = 33,23 \text{ €}$.
  - Fuel : $33,23 \times 0.08 = 2,66 \text{ €}$.
- **PRIX TOTAL : 78,89 €**
  - *(Détail : 32,23 + 1,00 + 8,00 + 35,00 + 2,66)*


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
