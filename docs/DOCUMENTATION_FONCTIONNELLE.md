# Documentation Fonctionnelle - Transport Quote

## 1. Présentation générale

### 1.1 Objectif de l'application

**Transport Quote** est une application web de gestion de devis transport. Elle permet aux commissionnaires de transport de :

- Importer les grilles tarifaires de leurs partenaires transporteurs
- Rechercher les meilleurs tarifs selon les critères d'expédition
- Constituer des devis clients avec gestion des marges
- Suivre le cycle de vie des devis (brouillon → envoyé → accepté)

### 1.2 Utilisateurs cibles

| Rôle | Description |
|------|-------------|
| Commercial | Recherche de tarifs, création de devis clients |
| Administrateur | Gestion des partenaires, import des tarifs |
| Manager | Suivi des devis, analyse des marges |

### 1.3 Périmètre fonctionnel

```
┌─────────────────────────────────────────────────────────────────────┐
│                      TRANSPORT QUOTE                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐ │
│  │  PARTENAIRES │   │   TARIFS     │   │    DEVIS CLIENTS         │ │
│  │              │   │              │   │                          │ │
│  │ - Création   │   │ - Import     │   │ - Création               │ │
│  │ - Gestion    │   │ - Recherche  │   │ - Ajout lignes transport │ │
│  │ - Marge par  │   │ - Matching   │   │ - Ajout frais            │ │
│  │   défaut     │   │              │   │ - Gestion marges         │ │
│  └──────────────┘   └──────────────┘   └──────────────────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Modules fonctionnels

### 2.1 Module Partenaires

#### Description
Gestion des transporteurs partenaires avec lesquels l'entreprise travaille.

#### Fonctionnalités

| Fonction | Description |
|----------|-------------|
| Créer un partenaire | Ajouter un nouveau transporteur (code, nom, email) |
| Modifier un partenaire | Mettre à jour les informations |
| Supprimer un partenaire | Retirer un partenaire (et ses tarifs) |
| Définir la marge par défaut | Marge appliquée automatiquement aux devis (20% par défaut) |
| Activer/Désactiver | Masquer un partenaire sans le supprimer |

#### Données gérées

| Champ | Description | Obligatoire |
|-------|-------------|-------------|
| Code | Identifiant unique (ex: DHL, BESSON) | Oui |
| Nom | Raison sociale | Oui |
| Email | Contact principal | Oui |
| Note | Évaluation du partenaire (1-5) | Non |
| Marge par défaut | % de marge automatique | Non (20%) |
| Actif | Partenaire actif ou non | Non (Oui) |

#### Règles métier

1. Le code partenaire doit être unique
2. La suppression d'un partenaire supprime tous ses tarifs
3. Les tarifs d'un partenaire inactif n'apparaissent pas dans les recherches

---

### 2.2 Module Import de tarifs

#### Description
Import automatisé des grilles tarifaires fournies par les partenaires.

#### Formats supportés

| Format | Extension | Particularités |
|--------|-----------|----------------|
| CSV | .csv | Colonnes séparées par virgule ou point-virgule |
| Excel | .xlsx, .xls | Support multi-feuilles |
| PDF | .pdf | Extraction de tableaux (limité) |

#### Types de grilles tarifaires

**1. Format plat (FLAT)**
```
Origine | Destination | Poids Min | Poids Max | Prix
Paris   | Lyon        | 0         | 100       | 15.00
Paris   | Lyon        | 101       | 500       | 12.00
```

**2. Format matrice (GRID)** - Ex: BESSON
```
Agence | Dept | 5 KG | 10 KG | 20 KG | 30 KG
NIC    | 01   | 8.50 | 12.00 | 18.00 | 25.00
NIC    | 02   | 9.00 | 13.00 | 19.00 | 27.00
```
- Les colonnes de poids sont pivotées en lignes

**3. Format double matrice (DUAL_GRID)** - Ex: BIANCHI, MONACO_LOG
```
Section 1 (Petits poids)           | Section 2 (Gros poids)
Dept | Min | 100-300 | PRICING     | Dept | 1001-1500 | PRICING
06   | 9.4 | 5.7     | PER_100KG   | 06   | 4.95      | LUMPSUM
```
- Deux sections côte à côte avec règles de tarification différentes

#### Processus d'import

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Upload  │───▶│ Parsing │───▶│ Mapping │───▶│Validation│───▶│  Base   │
│ fichier │    │         │    │ colonnes│    │ données │    │ données │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                   │
                                   ▼
                            ┌─────────────┐
                            │ Config YAML │
                            │ partenaire  │
                            └─────────────┘
```

1. **Upload** : L'utilisateur sélectionne un partenaire et un fichier
2. **Parsing** : Le système lit le fichier selon son format
3. **Mapping** : Les colonnes sont mappées aux champs standards
4. **Validation** : Chaque ligne est validée (prix > 0, codes pays, etc.)
5. **Persistance** : Les lignes valides sont enregistrées

#### Statuts d'import

| Statut | Description |
|--------|-------------|
| PENDING | Import en attente de traitement |
| PROCESSING | Import en cours |
| COMPLETED | Import terminé (avec ou sans erreurs) |
| FAILED | Échec complet de l'import |

#### Gestion des erreurs

Les erreurs sont collectées et affichées à l'utilisateur :
- Numéro de ligne
- Champ en erreur
- Message d'erreur
- Valeur brute

---

### 2.3 Module Recherche de tarifs

#### Description
Recherche des tarifs partenaires correspondant à une demande de transport.

#### Critères de recherche

| Critère | Type | Obligatoire |
|---------|------|-------------|
| Pays origine | Liste déroulante | Oui |
| Département origine | Texte (2-3 car.) | Non* |
| Ville origine | Autocomplete | Non* |
| Pays destination | Liste déroulante | Oui |
| Département destination | Texte (2-3 car.) | Non* |
| Ville destination | Autocomplete | Non* |
| Poids (kg) | Numérique | Oui |
| Volume (m³) | Numérique | Non |
| Mode transport | Liste | Non |
| Date expédition | Date | Non |

*Au moins un département OU une ville requis pour origine et destination

#### Algorithme de matching

```
1. Filtrer par mode de transport (si spécifié)
2. Filtrer par pays origine/destination
3. Filtrer par département (préfixe 2 caractères)
4. Filtrer par tranche de poids
5. Filtrer par dates de validité
6. Calculer le prix selon le type de tarification
7. Trier par prix croissant
```

#### Types de tarification

| Type | Code | Calcul |
|------|------|--------|
| Prix au 100 kg | PER_100KG | Prix × (poids arrondi au 100 kg supérieur / 100) |
| Prix au kg | PER_KG | Prix × poids |
| Forfait | LUMPSUM | Prix fixe |
| Prix à la palette | PER_PALLET | Prix × nombre de palettes |

**Exemple PER_100KG** :
- Poids : 250 kg
- Prix unitaire : 17€/100kg
- Poids arrondi : 300 kg
- **Prix calculé : 17 × 3 = 51€**

#### Résultats affichés

Pour chaque tarif trouvé :
- Nom du partenaire
- Mode de transport
- Tranche de poids
- Département destination
- Délai de transit
- Date de validité
- Prix calculé

---

### 2.4 Module Devis clients

#### Description
Création et gestion des devis à destination des clients finaux.

#### Cycle de vie d'un devis

```
┌────────┐    ┌───────┐    ┌──────┐    ┌──────────┐
│ DRAFT  │───▶│ READY │───▶│ SENT │───▶│ ACCEPTED │
│        │    │       │    │      │    └──────────┘
│        │    │       │    │      │    ┌──────────┐
│        │    │       │    │      │───▶│ REJECTED │
└────────┘    └───────┘    └──────┘    └──────────┘
                                       ┌──────────┐
                                  ───▶│ EXPIRED  │
                                       └──────────┘
```

| Statut | Description |
|--------|-------------|
| DRAFT | Brouillon en cours d'édition |
| READY | Devis prêt à envoyer |
| SENT | Devis envoyé au client |
| ACCEPTED | Devis accepté par le client |
| REJECTED | Devis refusé par le client |
| EXPIRED | Devis expiré (date dépassée) |

#### Structure d'un devis

**En-tête**
| Champ | Description |
|-------|-------------|
| Référence | Générée automatiquement (DEV-YYYY-XXXX) |
| Client | Nom, entreprise, email, téléphone |
| Date de création | Automatique |
| Date de validité | Optionnelle |

**Lignes**
| Type | Description |
|------|-------------|
| TRANSPORT | Ligne issue d'un tarif partenaire |
| FEE | Frais additionnel manuel |

**Totaux**
| Total | Calcul |
|-------|--------|
| Sous-total transport | Somme des lignes TRANSPORT |
| Total frais | Somme des lignes FEE |
| Total général | Sous-total + Frais |
| Marge totale | Somme des marges de toutes les lignes |

#### Gestion des marges

**Ajout d'une ligne transport**
1. Le système récupère la marge par défaut du partenaire (20%)
2. Prix de vente = Prix d'achat × (1 + marge/100)
3. Montant marge = Prix de vente - Prix d'achat

**Ajout d'un frais**
- Prix d'achat = 0€
- Prix de vente = Montant saisi
- Marge = 100%

**Modification manuelle**
L'utilisateur peut modifier :
- Le prix de vente → la marge est recalculée
- Le % de marge → le prix de vente est recalculé

#### Snapshot des données

Lors de l'ajout d'une ligne transport, les données suivantes sont **copiées** (snapshot) :
- Mode de transport
- Origine (ville, pays)
- Destination (ville, département, pays)
- Délai de transit
- Poids demandé

Cela garantit que le devis reste cohérent même si les tarifs partenaires changent.

---

## 3. Cas d'utilisation

### UC1 : Créer un devis transport

**Acteur** : Commercial

**Préconditions** :
- Des partenaires avec tarifs sont configurés
- Le commercial est connecté

**Scénario principal** :
1. Le commercial accède à la liste des devis
2. Il clique sur "Nouveau devis"
3. Le système crée un devis en brouillon (DRAFT)
4. Le commercial renseigne les informations client
5. Il ouvre la recherche de tarifs
6. Il saisit les critères (origine, destination, poids)
7. Le système affiche les tarifs correspondants
8. Le commercial sélectionne un tarif et l'ajoute au devis
9. Le système calcule automatiquement le prix de vente avec la marge
10. Le commercial peut ajuster la marge si nécessaire
11. Il peut ajouter des frais additionnels
12. Le devis est sauvegardé automatiquement

**Résultat** : Un devis avec lignes de transport et totaux calculés

---

### UC2 : Importer une grille tarifaire

**Acteur** : Administrateur

**Préconditions** :
- Le partenaire existe dans le système
- Le fichier Excel/CSV est disponible

**Scénario principal** :
1. L'administrateur accède au module Import
2. Il sélectionne le partenaire concerné
3. Il charge le fichier tarifaire
4. Le système lance l'import en arrière-plan
5. L'administrateur voit le statut passer à "En cours"
6. Une fois terminé, le système affiche :
   - Nombre total de lignes
   - Nombre de lignes importées avec succès
   - Nombre d'erreurs
7. En cas d'erreurs, le détail est affiché

**Scénario alternatif** - Erreurs de format :
- Si le fichier ne correspond pas au format attendu
- Le système affiche les erreurs par ligne
- L'administrateur peut corriger le fichier et relancer

**Résultat** : Les tarifs du partenaire sont mis à jour

---

### UC3 : Rechercher un tarif en consultation

**Acteur** : Commercial

**Préconditions** : Des tarifs sont importés

**Scénario principal** :
1. Le commercial accède à la recherche
2. Il saisit les critères de recherche
3. Le système affiche les tarifs correspondants
4. Le commercial consulte les prix sans créer de devis

**Résultat** : Affichage des tarifs disponibles (mode consultation)

---

## 4. Règles de gestion

### RG1 : Référence de devis
- Format : `DEV-YYYY-XXXX`
- YYYY : Année en cours
- XXXX : Numéro séquentiel sur 4 chiffres
- Exemple : DEV-2024-0042

### RG2 : Calcul du poids taxable
```
Poids taxable = MAX(poids réel, poids volumétrique)

Conversions standards :
- 1 m³ = 250 kg (messagerie)
- 1 m³ = 333 kg (express)
- 1 mètre linéaire = 1600-1750 kg (selon partenaire)
```

### RG3 : Arrondi des prix
- Les prix sont arrondis à 2 décimales
- L'arrondi se fait au centime supérieur

### RG4 : Marge minimale
- Aucune marge minimale imposée par le système
- Une marge négative génère un avertissement

### RG5 : Suppression de tarifs
- La suppression des tarifs d'un partenaire détache les lignes de devis existantes
- Les devis conservent les données en snapshot
- Un avertissement est affiché avant suppression

### RG6 : Validité des tarifs
- Un tarif est valide si :
  - `valid_from` est null OU `valid_from <= date du jour`
  - `valid_until` est null OU `valid_until >= date du jour`

---

## 5. Interfaces utilisateur

### 5.1 Dashboard

```
┌─────────────────────────────────────────────────────────────────────┐
│  Transport Quote                                    [User Menu ▼]   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Bienvenue sur Transport Quote                                       │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐         │
│  │  12            │  │  1,547         │  │  95%           │         │
│  │  Partenaires   │  │  Tarifs        │  │  Taux succès   │         │
│  │  actifs        │  │  disponibles   │  │  imports       │         │
│  └────────────────┘  └────────────────┘  └────────────────┘         │
│                                                                      │
│  Actions rapides                                                     │
│  [Nouvel import]  [Nouveau devis]  [Rechercher un tarif]            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Éditeur de devis

```
┌─────────────────────────────────────────────────────────────────────┐
│  Devis DEV-2024-0042                           [Enregistrer] [PDF]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Client: Société ABC                                                 │
│  Contact: Jean Dupont - jean@abc.com                                │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  LIGNES DU DEVIS                                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ #1 TRANSPORT - DHL Express                                    │  │
│  │ Paris (75) → Lyon (69) | 500 kg | Route                       │  │
│  │ Délai: 24h                                                    │  │
│  │                                                               │  │
│  │ Coût: 150.00€  |  Vente: 180.00€  |  Marge: 20% (30.00€)     │  │
│  │                                              [Modifier] [X]   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ #2 FRAIS - Manutention spéciale                               │  │
│  │                                                               │  │
│  │ Coût: 0.00€  |  Vente: 50.00€  |  Marge: 100% (50.00€)       │  │
│  │                                              [Modifier] [X]   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  [+ Ajouter transport]  [+ Ajouter frais]                           │
│  ─────────────────────────────────────────────────────────────────  │
│                                                                      │
│  TOTAUX                                                             │
│  Sous-total transport:  180.00€                                     │
│  Total frais:            50.00€                                     │
│  ─────────────────────────                                          │
│  TOTAL:                 230.00€                                     │
│  Marge totale:           80.00€ (34.8%)                             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.3 Recherche de tarifs

```
┌─────────────────────────────────────────────────────────────────────┐
│  Rechercher un tarif                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ORIGINE                        DESTINATION                         │
│  ┌─────────────────────┐        ┌─────────────────────┐            │
│  │ Pays: [France    ▼] │        │ Pays: [France    ▼] │            │
│  │ Dept: [75        ]  │        │ Dept: [69        ]  │            │
│  │ Ville: [Paris    ]  │        │ Ville: [Lyon     ]  │            │
│  └─────────────────────┘        └─────────────────────┘            │
│                                                                      │
│  MARCHANDISE                    TRANSPORT                           │
│  ┌─────────────────────┐        ┌─────────────────────┐            │
│  │ Poids: [500    ] kg │        │ Mode: [Tous      ▼] │            │
│  │ Volume: [    ] m³   │        │ Date: [2024-01-15]  │            │
│  └─────────────────────┘        └─────────────────────┘            │
│                                                                      │
│                              [Rechercher]                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Glossaire

| Terme | Définition |
|-------|------------|
| **Partenaire** | Transporteur avec lequel l'entreprise a un accord tarifaire |
| **Tarif** | Prix d'un transport pour une relation origine-destination donnée |
| **Devis** | Document commercial proposant un prix à un client |
| **Marge** | Différence entre le prix de vente et le prix d'achat |
| **Snapshot** | Copie des données à un instant T pour historisation |
| **PER_100KG** | Tarification au 100 kg avec arrondi supérieur |
| **LUMPSUM** | Tarification forfaitaire |
| **Matching** | Algorithme de recherche de tarifs correspondants |
| **Import** | Processus de chargement des grilles tarifaires |
