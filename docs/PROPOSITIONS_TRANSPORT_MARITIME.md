# Propositions : Ajout du Transport Maritime

## Contexte

L'application gère actuellement le transport routier (ROAD), ferroviaire (RAIL) et aérien (AIR).
L'enum `TransportMode` contient déjà la valeur `SEA`, mais aucune logique métier spécifique au maritime n'est implémentée.

Ce document propose les évolutions nécessaires pour intégrer pleinement le transport maritime.

---

## 1. Modèle de données

### 1.1 Nouvelles colonnes sur `partner_quotes`

Le maritime introduit des concepts absents du routier :

| Colonne | Type | Description |
|---------|------|-------------|
| `container_type` | Enum (20FT, 40FT, 40HC, 45HC, REEFER, FLAT_RACK, OPEN_TOP) | Type de conteneur |
| `origin_port_code` | VARCHAR(10) | Code port UN/LOCODE (ex: FRLEH = Le Havre) |
| `dest_port_code` | VARCHAR(10) | Code port UN/LOCODE (ex: ITMIL = Milan) |
| `transit_time_min` | INTEGER | Temps de transit minimum (jours) |
| `transit_time_max` | INTEGER | Temps de transit maximum (jours) |
| `free_days_detention` | INTEGER | Jours gratuits de détention conteneur |
| `free_days_demurrage` | INTEGER | Jours gratuits de surestarie |

> **Alternative** : stocker ces champs dans la colonne JSON `meta_data` existante pour éviter une migration lourde. Avantage : flexibilité. Inconvénient : pas d'index SQL direct.

### 1.2 Nouveaux types de tarification (`pricing_type`)

Ajouter à l'enum existante (`PER_100KG`, `PER_KG`, `LUMPSUM`, `PALLET`) :

| Valeur | Description |
|--------|-------------|
| `PER_TEU` | Prix par EVP (Equivalent Vingt Pieds) |
| `PER_CONTAINER` | Prix forfaitaire par conteneur (20', 40', etc.) |
| `PER_CBM` | Prix au mètre cube (groupage maritime / LCL) |

### 1.3 Table dédiée aux ports (optionnel mais recommandé)

```
ports
├── id (UUID)
├── un_locode (VARCHAR 5, unique) -- Ex: FRLEH, ESMAD
├── name (VARCHAR)               -- Ex: Le Havre, Madrid Seca
├── country_code (VARCHAR 2)     -- Ex: FR, ES
├── city (VARCHAR)               -- Ex: Le Havre
├── latitude / longitude         -- Pour calculs de distance
├── is_active (BOOLEAN)
└── created_at (TIMESTAMP)
```

Cela permet l'autocomplétion des ports dans le formulaire de recherche et la validation des données importées.

---

## 2. Logique de tarification

### 2.1 Deux modes de transport maritime

**FCL (Full Container Load)** — Conteneur complet :
- Tarification par conteneur (`PER_CONTAINER`)
- Le client réserve un conteneur entier (20', 40', etc.)
- Prix fixe par trajet, indépendant du poids (dans la limite du conteneur)

**LCL (Less than Container Load)** — Groupage :
- Tarification au volume (`PER_CBM`) ou au poids (`PER_KG`)
- Règle du "poids taxable" maritime : `max(poids_réel, volume_m3 × 1000)`
- Minimum de facturation typique : 1 CBM ou 1 tonne

### 2.2 Surcharges maritimes typiques

Créer des types de frais additionnels à gérer (soit en `customer_quote_items` de type FEE, soit dans un nouveau système de surcharges) :

| Surcharge | Description | Mode de calcul |
|-----------|-------------|----------------|
| BAF (Bunker Adjustment Factor) | Surcharge carburant | % du fret de base |
| CAF (Currency Adjustment Factor) | Ajustement devise | % du fret de base |
| THC (Terminal Handling Charge) | Manutention portuaire | Forfait par conteneur |
| ISPS (Security) | Sécurité portuaire | Forfait |
| BL Fee | Frais de connaissement | Forfait par expédition |
| ENS (Entry Summary Declaration) | Déclaration douanière EU | Forfait |
| Detention / Demurrage | Surestaries (si dépassement jours gratuits) | Par jour par conteneur |

### 2.3 Formule de calcul proposée

```
# FCL
prix_base = tarif_conteneur
total_fret = prix_base × nombre_conteneurs

# LCL
poids_taxable = max(poids_reel_kg, volume_m3 × 1000)
total_fret = tarif_par_cbm × ceil(poids_taxable / 1000)
  ou
total_fret = tarif_par_kg × poids_taxable

# Commun
total_surcharges = BAF + CAF + THC + ISPS + BL_fee + ...
cout_total = total_fret + total_surcharges
prix_vente = cout_total × (1 + marge% / 100)
```

---

## 3. Import des tarifs partenaires

### 3.1 Configuration YAML

Ajouter un nouveau partenaire maritime dans `backend/configs/partner_mapping.yaml` :

```yaml
CMA_CGM:  # Exemple compagnie maritime
  layout: "flat"
  columns:
    origin_port: "POL"           # Port of Loading
    dest_port: "POD"             # Port of Discharge
    container_type: "Equipment"
    cost: "Rate"
    currency: "Currency"
    valid_from: "Effective"
    valid_until: "Expiry"
    transit_time: "Transit Days"
  defaults:
    transport_mode: "SEA"
    pricing_type: "PER_CONTAINER"
  transforms:
    origin_port:
      type: "port_code_lookup"   # Résoudre nom → UN/LOCODE
    dest_port:
      type: "port_code_lookup"
```

### 3.2 Mapping port → pays/ville

Le `column_mapper.py` doit pouvoir résoudre un code port vers :
- `origin_country` / `dest_country`
- `origin_city` / `dest_city`
- `origin_postal_code` / `dest_postal_code` (code port comme identifiant)

Ceci peut se faire via la table `ports` ou un fichier de référence JSON/YAML.

### 3.3 Multi-feuilles pour le maritime

Comme pour MONACO_LOG, un fichier maritime peut contenir :
- Feuille "FCL Rates" (conteneur complet)
- Feuille "LCL Rates" (groupage)
- Feuille "Surcharges" (frais additionnels)

Le système multi-sheet existant supporte déjà cette logique.

---

## 4. Recherche et matching

### 4.1 Nouveaux critères de recherche

Étendre `QuoteSearchRequest` (schéma Pydantic) :

```python
# Champs additionnels pour le maritime
container_type: Optional[str] = None      # 20FT, 40FT, etc.
shipping_type: Optional[str] = None       # FCL ou LCL
volume_cbm: Optional[float] = None        # Volume en m3 (pour LCL)
origin_port_code: Optional[str] = None    # UN/LOCODE
dest_port_code: Optional[str] = None      # UN/LOCODE
```

### 4.2 Adaptation du matching

Dans `matching_service.py` :

- Si `transport_mode == SEA` et `origin_port_code` fourni → matcher sur `origin_port_code` au lieu de `origin_postal_code`
- Si `shipping_type == FCL` → filtrer par `container_type`
- Si `shipping_type == LCL` → calculer le poids taxable via `max(weight, volume_cbm × 1000)`

### 4.3 Calcul du prix dans les résultats

Adapter `_calculate_price()` dans le matching service pour les nouveaux `pricing_type` :

```python
if pricing_type == "PER_CONTAINER":
    total = cost * nb_containers
elif pricing_type == "PER_CBM":
    taxable = max(weight, volume_cbm * 1000)
    total = cost * ceil(taxable / 1000)
elif pricing_type == "PER_TEU":
    teu = convert_to_teu(container_type, nb_containers)
    total = cost * teu
```

---

## 5. Interface utilisateur (Frontend)

### 5.1 Formulaire de recherche (`Search.tsx`)

Quand l'utilisateur sélectionne le mode **SEA** :

- Afficher un sélecteur **FCL / LCL**
- **Si FCL** : afficher sélecteur `container_type` (20', 40', 40HC...) + nombre de conteneurs
- **Si LCL** : afficher champs `poids (kg)` + `volume (m3)`
- Remplacer les champs ville/code postal par des **sélecteurs de port** avec autocomplétion (composant `PortAutocomplete` similaire à `CityAutocomplete`)
- Ou : conserver les champs ville et résoudre automatiquement vers le port le plus proche

### 5.2 Affichage des résultats (`Results.tsx`)

Pour les résultats maritimes, afficher :
- Ports d'origine et destination (avec codes UN/LOCODE)
- Type de conteneur et nombre
- Transit time (plage min-max jours)
- Détail des surcharges
- Jours gratuits detention/demurrage
- Badge distinctif "Maritime" (icône navire au lieu de camion)

### 5.3 Icônes et visuels

Ajouter les icônes Lucide correspondantes :
- `Ship` pour le transport maritime
- `Container` ou `Package` pour les types de conteneurs
- `Anchor` pour les ports

Le composant `Results.tsx` utilise actuellement `Truck` pour tout — conditionner l'icône selon le `transport_mode`.

### 5.4 Devis client (`CustomerQuoteEditor.tsx`)

- Le snapshot de ligne de devis doit inclure les infos maritimes (port, conteneur, transit time)
- Le `PriceBreakdown` doit afficher la formule maritime (ex: "2 × 40HC @ 1 850 € = 3 700 €")
- Permettre l'ajout de lignes de surcharges maritimes pré-remplies (THC, BAF, etc.)

---

## 6. Périmètre géographique

### 6.1 Routes maritimes principales à couvrir

Routes prioritaires depuis/vers la France :

| Origine | Destination | Corridor |
|---------|-------------|----------|
| Le Havre (FRLEH) | Ports Asie (Shanghai, Ningbo, Shenzhen) | Asie-Europe |
| Marseille/Fos (FRFOS) | Ports Méditerranée (Gênes, Barcelone, Tanger) | Intra-Med |
| Le Havre (FRLEH) | Ports Amérique du Nord (New York, Savannah) | Transatlantique |
| Le Havre (FRLEH) | Ports Afrique de l'Ouest (Abidjan, Dakar) | Afrique |
| Dunkerque (FRDKK) | Ports Scandinavie | Short-sea Nord |

### 6.2 Ajout de pays hors Europe

Le fichier `frontend/src/constants/countries.ts` ne contient que 21 pays européens.
Le maritime implique potentiellement le monde entier. Options :

1. **Extension progressive** : ajouter les pays au fur et à mesure des partenaires maritimes
2. **Liste complète** : importer la liste ISO 3166-1 (~250 pays) mais n'activer que ceux ayant des tarifs
3. **Approche hybride** : garder la liste courte pour le routier, liste étendue uniquement quand `mode == SEA`

**Recommandation** : option 3 — filtrer la liste de pays selon le mode de transport sélectionné.

---

## 7. Stratégie de mise en oeuvre

### Phase 1 — Fondations (estimation : petite)
- [ ] Migration BDD : nouveaux champs sur `partner_quotes` (ou usage de `meta_data`)
- [ ] Ajout des `pricing_type` : `PER_TEU`, `PER_CONTAINER`, `PER_CBM`
- [ ] Création de la table `ports` + seed des ports principaux
- [ ] API endpoint `/api/v1/ports/` pour autocomplétion

### Phase 2 — Import des tarifs
- [ ] Configuration YAML pour un premier partenaire maritime
- [ ] Adaptation `column_mapper.py` pour résoudre les codes ports
- [ ] Adaptation `data_normalizer.py` pour les données maritimes
- [ ] Test d'import avec un fichier de tarifs réel

### Phase 3 — Recherche et tarification
- [ ] Étendre `QuoteSearchRequest` avec les champs maritimes
- [ ] Adapter `matching_service.py` pour le matching par port
- [ ] Implémenter les formules de calcul FCL/LCL dans `pricing_service.py`
- [ ] Gestion des surcharges

### Phase 4 — Interface utilisateur
- [ ] Formulaire de recherche conditionnel (mode SEA)
- [ ] Composant `PortAutocomplete`
- [ ] Adaptation affichage résultats (icônes, infos maritimes)
- [ ] Adaptation éditeur de devis (snapshot maritime, surcharges)
- [ ] Extension de la liste de pays

### Phase 5 — Consolidation
- [ ] Tests unitaires et d'intégration
- [ ] Import de tarifs de 2-3 partenaires maritimes réels
- [ ] Validation métier avec des cas réels
- [ ] Documentation utilisateur

---

## 8. Points d'attention

### 8.1 Incoterms
Le maritime utilise intensivement les Incoterms (FOB, CIF, CFR, EXW, DDP...).
Il serait pertinent d'ajouter un champ `incoterm` sur `partner_quotes` et `customer_quote_items` pour qualifier la portée du prix.

### 8.2 Pré/post acheminement
Un transport maritime nécessite souvent :
- **Pré-acheminement** : transport routier usine → port d'embarquement
- **Post-acheminement** : transport routier port de débarquement → destination finale

L'application gère déjà le routier — il faudrait pouvoir combiner un devis "door-to-door" avec :
1. Ligne routière (pré-acheminement)
2. Ligne maritime (fret principal)
3. Ligne routière (post-acheminement)

Le mode `MULTIMODAL` existant pourrait encapsuler ce concept, ou on laisse l'utilisateur ajouter manuellement les 3 lignes dans un même devis client.

### 8.3 Devises
Le fret maritime est souvent coté en USD. Le système actuel stocke `currency` mais ne gère pas la conversion. Prévoir :
- Taux de change configurable
- Conversion automatique EUR ↔ USD à l'affichage

### 8.4 Dangereux (IMO/IMDG)
Les marchandises dangereuses en maritime suivent le code IMDG. Si pertinent, ajouter :
- Classe IMO (1-9)
- Numéro ONU
- Surcharge matières dangereuses

### 8.5 Assurance maritime
Le maritime implique souvent une assurance cargo. Ajouter éventuellement un calcul automatique :
- Taux standard : 0.3% à 0.5% de la valeur déclarée de la marchandise
- En tant que ligne de frais (`FEE`) dans le devis

---

## 9. Résumé des fichiers impactés

| Fichier | Modification |
|---------|-------------|
| `backend/app/models/partner_quote.py` | Nouveaux champs, nouveaux enums |
| `backend/app/schemas/partner_quote.py` | Nouveaux champs Pydantic |
| `backend/app/schemas/matching.py` | Critères recherche maritime |
| `backend/app/services/pricing_service.py` | Formules FCL/LCL/TEU |
| `backend/app/services/matching_service.py` | Matching par port, poids taxable |
| `backend/app/services/import_logic/column_mapper.py` | Résolution codes ports |
| `backend/app/services/import_logic/data_normalizer.py` | Normalisation données maritimes |
| `backend/configs/partner_mapping.yaml` | Config partenaires maritimes |
| `frontend/src/types/index.ts` | Types SearchCriteria étendus |
| `frontend/src/pages/Search.tsx` | Formulaire conditionnel mode SEA |
| `frontend/src/pages/Results.tsx` | Affichage résultats maritimes |
| `frontend/src/components/ui/PriceBreakdown.tsx` | Formules maritimes |
| `frontend/src/constants/countries.ts` | Pays supplémentaires |
| **Nouveaux fichiers** | |
| `backend/app/models/port.py` | Modèle Port |
| `backend/app/api/ports.py` | API ports |
| `frontend/src/components/ui/PortAutocomplete.tsx` | Sélecteur de port |
