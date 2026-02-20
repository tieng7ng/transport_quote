# Documentation Technique et Fonctionnelle (Simplifiée)
## Application de Génération de Devis Transport

**Version** : 2.1.0
**Date** : Janvier 2026
**Stack** : Python + FastAPI

---

## Statut d'implémentation

| Module                     | Statut        | Description                      |
| -------------------------- | ------------- | -------------------------------- |
| Gestion Partenaires        | ✅ Complet     | CRUD + Suppression tarifs        |
| Import Tarifs              | ✅ Complet     | CSV, Excel, PDF + Validation     |
| Recherche (Matching)       | ✅ Complet     | Filtrage + Autocomplétion villes |
| Validation flexible        | ✅ Complet     | Code postal OU ville             |
| Tri résultats              | ⏳ En cours    | Prix, Délai                      |
| **Devis Clients (Panier)** | ✅ Complet     | Liste, Détail, Édition, Sidebar  |
| Génération PDF             | ❌ Non démarré | Export PDF du devis              |
| Envoi Email                | ❌ Non démarré | Envoi devis au client            |

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Architecture simplifiée](#2-architecture-simplifiée)
3. [Modules fonctionnels](#3-modules-fonctionnels)
4. [Interfaces Utilisateur](#4-interfaces-utilisateur)
5. [Cas d'usage](#5-cas-dusage)
6. [Flux de données](#6-flux-de-données)
7. [Modèle de données](#7-modèle-de-données)
8. [API Reference](#8-api-reference)
9. [Stack technique](#9-stack-technique)
10. [Déploiement](#10-déploiement)

---

## 1. Présentation

### 1.1 Objectif

Application permettant de :
1. **Importer** les tarifs des transporteurs depuis des fichiers (PDF, Excel, CSV)
2. **Rechercher** les meilleures offres pour un trajet
3. **Générer** et envoyer des devis aux clients

### 1.2 Acteurs

| Acteur             | Rôle                                        |
| ------------------ | ------------------------------------------- |
| **Administrateur** | Importe les fichiers tarifs des partenaires |
| **Client**         | Recherche des offres et reçoit des devis    |

### 1.3 Flux simplifié

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Partenaire  │     │    Admin     │     │   Système    │     │   Client     │
│  (externe)   │     │              │     │              │     │              │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │
       │ Envoie fichier     │                    │                    │
       │ (email/FTP)        │                    │                    │
       │───────────────────>│                    │                    │
       │                    │                    │                    │
       │                    │ Upload fichier     │                    │
       │                    │───────────────────>│                    │
       │                    │                    │                    │
       │                    │                    │ Parse + Valide     │
       │                    │                    │ + Stocke           │
       │                    │                    │                    │
       │                    │<── Rapport import ─│                    │
       │                    │                    │                    │
       │                    │                    │<─── Recherche ─────│
       │                    │                    │                    │
       │                    │                    │──── Résultats ────>│
       │                    │                    │                    │
       │                    │                    │<─── Demande devis ─│
       │                    │                    │                    │
       │                    │                    │──── PDF + Email ──>│
```

---

## 2. Architecture simplifiée

### 2.1 Vue d'ensemble

```
┌────────────────────────────────────────────────────────────────────────────┐
│                               APPLICATION                                  │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                       Interface Web (Admin)                          │  │
│  │                  Upload fichiers + Consultation                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│  ┌─────────────────────────────────┴────────────────────────────────────┐  │
│  │                             API REST                                 │  │
│  └─────────────────────────────────┬────────────────────────────────────┘  │
│                                    │                                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Module Import   │  │  Module Matching │  │ Module Generator │          │
│  │  ──────────────  │  │  ──────────────  │  │ ──────────────── │          │
│  │  • CSV Parser    │  │  • Recherche     │  │ • Templates      │          │
│  │  • Excel Parser  │  │  • Scoring       │  │ • PDF            │          │
│  │  • PDF Parser    │  │  • Cache         │  │ • Email          │          │
│  │  • Validation    │  │                  │  │                  │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                    │
│  ┌────────┴─────────────────────┴─────────────────────┴─────────────────┐  │
│  │                           PostgreSQL                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Composants

| Composant            | Description                                                 |
| -------------------- | ----------------------------------------------------------- |
| **Interface Admin**  | Upload fichiers, visualisation imports, gestion partenaires |
| **API REST**         | Endpoints pour recherche et génération de devis             |
| **Module Import**    | Parsing des fichiers CSV, Excel, PDF                        |
| **Module Matching**  | Recherche et classement des offres                          |
| **Module Generator** | Génération PDF et envoi email                               |
| **PostgreSQL**       | Stockage des tarifs et devis                                |

---

## 3. Modules fonctionnels

### 3.1 Module 1 : Gestion des Partenaires (Socle)

#### Objectif
Gérer le référentiel des transporteurs et leurs configurations.

#### Fonctionnalités

| ID   | Fonctionnalité      | Description                                  |
| ---- | ------------------- | -------------------------------------------- |
| F1.1 | Création Partenaire | Ajout d'un transporteur (Nom, Code, Contact) |
| F1.2 | Configuration       | Définition des règles d'import (Yaml)        |
| F1.3 | Activation          | Activer/Désactiver un partenaire globalement |
| F1.4 | Suppression Tarifs  | Supprimer tous les tarifs d'un partenaire    |

### 3.2 Module 2 : Import des tarifs

#### Objectif
Importer les fichiers tarifs des partenaires et les stocker en base.

#### Formats supportés

| Format                  | Parsing           | Fiabilité |
| ----------------------- | ----------------- | --------- |
| **CSV**                 | pandas            | 100%      |
| **Excel** (.xlsx, .xls) | pandas + openpyxl | 100%      |
| **PDF** (texte)         | pdfplumber        | 80%       |
| **PDF** (complexe)      | IA Claude         | 95%       |

#### Fonctionnalités

| ID   | Fonctionnalité   | Description                             |
| ---- | ---------------- | --------------------------------------- |
| F1.1 | Upload fichier   | Réception CSV, Excel ou PDF             |
| F1.2 | Détection format | Auto-détection du type de fichier       |
| F1.3 | Mapping colonnes | Correspondance automatique des colonnes |
| F1.4 | Validation       | Vérification des données obligatoires   |
| F1.5 | Rapport d'import | Liste des succès et erreurs             |

#### Flux d'import

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────>│   Parser    │────>│  Validator  │────>│   Insert    │
│   Fichier   │     │ CSV/XLS/PDF │     │             │     │     BD      │
└─────────────┘     └─────────────┘     └──────┬──────┘     └─────────────┘
                                               │
                                               v
                                        ┌─────────────┐
                                        │   Rapport   │
                                        │  d'erreurs  │
                                        └─────────────┘
```

### 3.3 Module 3 : Recherche (Matching)

#### Objectif
Trouver les meilleures offres pour un trajet donné.

#### Fonctionnalités

| ID   | Fonctionnalité        | Description                                             | Statut |
| ---- | --------------------- | ------------------------------------------------------- | ------ |
| F3.1 | Recherche             | Filtrer par origine, destination, poids                 | ✅      |
| F3.2 | Tri                   | Par prix, délai ou score combiné                        | ⏳      |
| F3.3 | Limite                | Retourner les N meilleures offres                       | ✅      |
| F3.4 | Autocomplétion villes | Suggestions de villes basées sur les tarifs existants   | ✅      |
| F3.5 | Validation flexible   | Code postal OU ville requis (pas les deux obligatoires) | ✅      |

#### Autocomplétion des villes (F3.4) ✅ Implémenté

**Objectif** : Permettre à l'utilisateur de rechercher une ville parmi celles disponibles dans la base de tarifs.

**Source des données** : Les villes sont extraites des champs `origin_city` et `dest_city` de la table `PartnerQuote`.

**Algorithme de recherche** :
1. Recherche insensible à la casse
2. Recherche par préfixe (commence par) ou contient
3. Dédoublonnage des villes identiques
4. Comptage du nombre de tarifs par ville

**Flux** :
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Input     │────>│  Debounce   │────>│    API      │────>│  Dropdown   │
│  (2+ chars) │     │   (300ms)   │     │ /cities/    │     │ Suggestions │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 3.4 Module 4 : Génération de devis

#### Objectif
Créer et envoyer des devis PDF aux clients.

#### Fonctionnalités

| ID   | Fonctionnalité | Description                                       |
| ---- | -------------- | ------------------------------------------------- |
| F4.1 | Édition Prix   | Ajustement marge et prix de vente (Flexible)      |
| F4.2 | Frais annexes  | Ajout de lignes manuelles (Assurance, Dossier)    |
| F4.3 | Génération PDF | Créer un devis formaté (Prix de vente uniquement) |
| F4.4 | Envoi email    | Transmettre au client                             |
| F4.5 | Archivage      | Stocker le devis                                  |

### 3.5 Module 5 : Authentification et Rôles ✅ Implémenté

#### Objectif
Sécuriser l'accès à l'application et restreindre les fonctionnalités selon le profil de l'utilisateur.

#### Rôles définis (Matrice 1.2)
| Rôle            | Description              | Droits Principaux                                                               |
| --------------- | ------------------------ | ------------------------------------------------------------------------------- |
| **SUPER_ADMIN** | Administrateur Technique | Accès total, y compris suppression de données sensibles (Partenaires, Imports). |
| **ADMIN**       | Gestionnaire             | Gestion des utilisateurs, création de partenaires, accès à tous les devis.      |
| **COMMERCIAL**  | Vendeur                  | Création de devis, gestion de *ses* propres dossiers uniquement.                |
| **OPERATOR**    | Opérateur Saisie         | Création et modification de devis (sans suppression).                           |
| **VIEWER**      | Auditeur                 | Lecture seule sur l'ensemble des données.                                       |

#### Fonctionnalités
| ID   | Fonctionnalité     | Description                                                 |
| ---- | ------------------ | ----------------------------------------------------------- |
| F5.1 | Connexion (Login)  | Authentification par Email/Mot de passe (JWT).              |
| F5.2 | Protection Routes  | Restriction des pages et API selon le rôle.                 |
| F5.3 | Gestion Profil     | Modification mot de passe et informations personnelles.     |
| F5.4 | Admin Utilisateurs | Création, modification, désactivation des comptes (Admin+). |

---

## 4. Interfaces Utilisateur

Cette section décrit les écrans disponibles dans l'application React.

### 4.1 Espace Administrateur

#### Gestion des Partenaires
*   **Liste des partenaires** : Tableau affichant ID, Nom, Code, Statut (Actif/Inactif). Actions : Modifier, Supprimer.
*   **Fiche Partenaire** : Formulaire pour créer/éditer un partenaire et ses configurations (YAML).

#### Gestion des Imports
*   **Nouvel Import** : Formulaire d'upload (Sélection Partenaire + Drag & Drop fichier).
*   **Historique** : Tableau des jobs d'import passés avec statut (Succès/Erreur) et statistiques.
*   **Détail Import** : Vue des lignes en erreur pour correction (si supporté) ou analyse.

### 4.2 Espace Opérateur / Client (Simulation)

#### Recherche de Transport (Wizard)
*   **Étape 1 - Itinéraire** :
    - Pays départ/arrivée (obligatoire)
    - Code postal OU Ville (au moins un des deux) avec **autocomplétion**
*   **Étape 2 - Marchandise** : Saisie des palettes (Dimensions, Poids, Gerbable).
*   **Étape 3 - Options** : Filtres (Hayon, Express, etc.).

**Règle de validation** : L'utilisateur doit saisir soit un code postal, soit une ville (ou les deux) pour l'origine et la destination.

#### Autocomplétion des villes ✅ Implémenté

L'autocomplétion permet à l'utilisateur de rechercher rapidement une ville parmi celles disponibles dans la base de tarifs.

```
┌─────────────────────────────────────────────────────────────────────┐
│  Ville d'origine                                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Par_                                                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  📍 Paris (FR)                                    125 tarifs  │  │
│  │  📍 Paray-le-Monial (FR)                           12 tarifs  │  │
│  │  📍 Parthenay (FR)                                  8 tarifs  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

**Caractéristiques :**
- Recherche dès 2 caractères saisis
- Affiche ville + pays + nombre de tarifs disponibles
- Suggestions basées sur les villes présentes dans les tarifs importés
- Délai de debounce (300ms) pour éviter les requêtes excessives
- **Navigation clavier** : flèches haut/bas pour naviguer, Enter pour sélectionner, Escape pour fermer

**Navigation clavier :**

```
┌─────────────────────────────────────────────────────────────────────┐
│  Ville d'origine                                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Par_                                                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  📍 Paris (FR)                                    125 tarifs  │◀─── ↑↓ Navigation
│  │  ▶ Paray-le-Monial (FR)                           12 tarifs  │◀─── Élément actif (surligné)
│  │  📍 Parthenay (FR)                                  8 tarifs  │     Enter = Sélectionner
│  └───────────────────────────────────────────────────────────────┘  │     Esc = Fermer
└─────────────────────────────────────────────────────────────────────┘
```

| Touche          | Action                                        |
| --------------- | --------------------------------------------- |
| `↓` (ArrowDown) | Sélectionne l'élément suivant                 |
| `↑` (ArrowUp)   | Sélectionne l'élément précédent               |
| `Enter`         | Valide la sélection et ferme le dropdown      |
| `Tab`           | Valide la sélection et passe au champ suivant |
| `Escape`        | Ferme le dropdown sans sélectionner           |

#### Sélection & Devis
*   **Résultats de recherche** : Liste des offres correspondantes (triées par prix).
*   **Génération de devis** : Formulaire pour saisir les infos client et générer le PDF final.

### 4.3 Espace Devis Clients (Workflow Panier) ✅ Implémenté

Cette section décrit le workflow "Panier" permettant de construire un devis progressivement en ajoutant plusieurs trajets.

#### 4.3.1 Liste des Devis (`CustomerQuotes.tsx`)

**Structure actuelle :**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Devis Clients                                         [+ Nouveau Devis]    │
│  Gérez vos propositions commerciales                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🔍 Rechercher par référence, client...                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Référence    │ Client           │ Date     │ Montant HT │ Statut │    │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ DEV-2026-001 │ Société ABC      │ 📅 27/01 │  450.00 €  │ DRAFT  │👁🗑│ │
│  │              │ SARL ABC         │          │            │ (gris) │    │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ DEV-2026-002 │ Transport Martin │ 📅 25/01 │  820.00 €  │ SENT   │ 👁 │ │
│  │              │ SAS Martin       │          │            │ (jaune)│    │ │
│  ├───────────────────────────────────────────────────────────────────────┤ │
│  │ DEV-2026-003 │ Logistique Plus  │ 📅 20/01 │ 1250.00 €  │ACCEPTED│ 👁 │ │
│  │              │                  │          │            │ (vert) │    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│  État vide :                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          📄                                         │   │
│  │                     Aucun devis                                     │   │
│  │    Commencez par créer une nouvelle recherche pour générer un devis │   │
│  │                  Aller à la recherche →                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Colonnes du tableau :**
| Colonne    | Source                                           | Description                  |
| ---------- | ------------------------------------------------ | ---------------------------- |
| Référence  | `quote.reference`                                | DEV-YYYY-XXXX ou "Brouillon" |
| Client     | `quote.customer_name` + `quote.customer_company` | Nom et société               |
| Date       | `quote.created_at`                               | Date de création             |
| Montant HT | `quote.total`                                    | Total en euros               |
| Statut     | `quote.status`                                   | Badge coloré                 |
| Actions    | -                                                | Icônes d'action              |

**Statuts et couleurs :**
| Statut     | Couleur | Description        |
| ---------- | ------- | ------------------ |
| `DRAFT`    | Gris    | Brouillon en cours |
| `READY`    | Bleu    | Prêt à envoyer     |
| `SENT`     | Jaune   | Envoyé au client   |
| `ACCEPTED` | Vert    | Accepté            |
| `REJECTED` | Rouge   | Refusé             |

**Actions disponibles :**
| Action            | Icône | Condition        | Description                                  |
| ----------------- | ----- | ---------------- | -------------------------------------------- |
| `+ Nouveau Devis` | -     | Toujours         | Crée un devis et redirige vers l'éditeur     |
| Voir le devis     | 👁     | Toujours         | Navigue vers `/customer-quotes/{id}`         |
| Supprimer         | 🗑     | Statut = `DRAFT` | Supprime le devis brouillon                  |
| Recherche         | 🔍     | Toujours         | Filtre par référence ou client (placeholder) |

#### 4.3.2 Affichage d'un Devis (`CustomerQuoteDetail.tsx`)

**Structure actuelle :**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Retour à la liste                                                        │
│                                                                             │
│  DEV-2026-0042                                    ┌──────┐                  │
│                                                   │ DRAFT│                  │
│                                                   └──────┘                  │
│                                    [🖨 Imprimer] [📤 Envoyer] [✏️ Éditer]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────┐  ┌───────────────────────┐ │
│  │  📄 Détail des prestations      3 lignes    │  │  CLIENT               │ │
│  ├─────────────────────────────────────────────┤  │  ┌───┐                │ │
│  │                                             │  │  │ S │ Société ABC    │ │
│  │  ┌─────────┐                                │  │  └───┘ SARL           │ │
│  │  │TRANSPORT│ Paris → Lyon                   │  │                       │ │
│  │  └─────────┘                                │  │  Email: contact@abc.fr│ │
│  │  🚚 ROAD - DHL Express                      │  │  Validité: 28/02/2026 │ │
│  │  Paris, FR → Lyon, FR                       │  └───────────────────────┘ │
│  │  Poids: 500 kg | Délai: 24h                 │                            │
│  │                              172.50 €       │  ┌───────────────────────┐ │
│  │                    Marge: 15% (22.50 €)     │  │  RÉCAPITULATIF        │ │
│  ├─────────────────────────────────────────────┤  │                       │ │
│  │                                             │  │  Total Transport      │ │
│  │  ┌─────────┐                                │  │            304.50 €   │ │
│  │  │TRANSPORT│ Lyon → Marseille               │  │  Total Frais          │ │
│  │  └─────────┘                                │  │             25.00 €   │ │
│  │  🚚 ROAD - Transport Besson                 │  │  ─────────────────    │ │
│  │  Lyon, FR → Marseille, FR                   │  │  Total HT             │ │
│  │  Poids: 500 kg | Délai: 48h                 │  │            329.50 €   │ │
│  │                              132.00 €       │  │                       │ │
│  │                    Marge: 10% (12.00 €)     │  │  Marge Totale         │ │
│  ├─────────────────────────────────────────────┤  │             34.50 €   │ │
│  │                                             │  └───────────────────────┘ │
│  │  ┌─────┐                                    │                            │
│  │  │FRAIS│ Frais de dossier                   │                            │
│  │  └─────┘                                    │                            │
│  │                               25.00 €       │                            │
│  │                    Marge: 100% (25.00 €)    │                            │
│  └─────────────────────────────────────────────┘                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Layout :** Grille 3 colonnes (2/3 contenu principal + 1/3 sidebar)

**Zone principale - Détail des prestations :**
| Élément           | Description                                           |
| ----------------- | ----------------------------------------------------- |
| Badge type        | `TRANSPORT` (bleu) ou `FRAIS` (orange)                |
| Description       | `item.description`                                    |
| Détails transport | Mode, partenaire, origine → destination, poids, délai |
| Prix vente        | `item.sell_price`                                     |
| Marge             | Pourcentage et montant                                |

**Sidebar - Informations :**
| Section       | Contenu                                              |
| ------------- | ---------------------------------------------------- |
| Client        | Avatar, nom, société, email, validité                |
| Récapitulatif | Total transport, total frais, total HT, marge totale |

**Actions disponibles :**
| Bouton   | Action                                       |
| -------- | -------------------------------------------- |
| Imprimer | Placeholder (non implémenté)                 |
| Envoyer  | Placeholder (non implémenté)                 |
| Éditer   | Navigation vers `/customer-quotes/{id}/edit` |

#### 4.3.3 Édition d'un Devis (`CustomerQuoteEditor.tsx`)

**Structure actuelle :**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← │ Éditeur de Devis | DEV-2026-0042                                       │
│      Sans client - DRAFT                                                    │
│                                          Marge Totale │ Total HT            │
│                                             34.50 €   │ 329.50 €            │
│                                                       │        [Enregistrer]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  👤 Informations Client                                        [✏️ Modifier]│
│  ───────────────────────────────────────────────────────────────────────    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Nom : Société ABC                                                  │   │
│  │  Société : SARL ABC                                                 │   │
│  │  Email : contact@abc.fr                                             │   │
│  │  Validité : 28/02/2026                                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  📊 Prestations Transport                          Sous-total: 304.50 €     │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Paris → Lyon                                                       │   │
│  │  DHL Express | ROAD | 24h | 500 kg                                  │   │
│  │                                                                     │   │
│  │  Prix Achat    Marge %      Marge €      Prix Vente                 │   │
│  │  150.00 €      [15   ]%     22.50 €      172.50 €              [🗑] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Lyon → Marseille                                                   │   │
│  │  Transport Besson | ROAD | 48h | 500 kg                             │   │
│  │                                                                     │   │
│  │  Prix Achat    Marge %      Marge €      Prix Vente                 │   │
│  │  120.00 €      [10   ]%     12.00 €      132.00 €              [🗑] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Mode de transport : [🚚 Route ▼] [🚂 Rail] [✈️ Aérien] [🚢 Maritime] │   │
│  │                                                                     │   │
│  │                    [+ Ajouter un transport]                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  (Visible uniquement si statut = DRAFT)                                    │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  ➕ Frais Annexes                                   [+ Ajouter un coût]     │
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Frais de dossier                                                   │   │
│  │                                                                     │   │
│  │  Prix Vente                                                         │   │
│  │  [25.00  ] €                                                   [🗑] │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ───────────────────────────────────────────────────────────────────────    │
│  (Si aucun transport: "Aucune ligne de transport. Ajoutez des tarifs        │
│   depuis la recherche." + lien vers /search)                                │
│  (Si aucun frais: "Aucun frais additionnel.")                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

Modal Édition Client :
┌─────────────────────────────────────────────────────────┐
│  Modifier les informations client                [X]    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Nom *                                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Société ABC                                     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Société                                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │ SARL ABC                                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Email                                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ contact@abc.fr                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Date de validité                                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 28/02/2026                                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌───────────────┐  ┌───────────────┐                  │
│  │   Annuler     │  │  Enregistrer  │                  │
│  └───────────────┘  └───────────────┘                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Barre supérieure :**
| Élément      | Description                       |
| ------------ | --------------------------------- |
| Retour       | Lien vers `/customer-quotes/{id}` |
| Titre        | "Éditeur de Devis \| {reference}" |
| Sous-titre   | Client et statut                  |
| Marge Totale | Affichage en temps réel           |
| Total HT     | Affichage en temps réel           |
| Enregistrer  | Bouton de sauvegarde              |

**Section Client :**
| Champ    | Éditable | Description                               |
| -------- | -------- | ----------------------------------------- |
| Nom      | **Oui**  | `customer_name` - Nom du contact          |
| Société  | **Oui**  | `customer_company` - Raison sociale       |
| Email    | **Oui**  | `customer_email` - Email de contact       |
| Validité | **Oui**  | `valid_until` - Date de validité du devis |

**Sélecteur Mode de Transport :**
| Mode     | Icône | Valeur |
| -------- | ----- | ------ |
| Route    | 🚚     | `ROAD` |
| Rail     | 🚂     | `RAIL` |
| Aérien   | ✈️     | `AIR`  |
| Maritime | 🚢     | `SEA`  |

Le mode sélectionné est passé à la modal de recherche lors de l'ajout d'un transport.

**Bouton "+ Ajouter un transport" :**
- Visible uniquement si `status === 'DRAFT'`
- Ouvre la modal de recherche avec le mode de transport pré-sélectionné
- Le mode n'est plus modifiable dans la modal

**Section Transport (`QuoteItemEditor`) :**
| Champ       | Éditable | Description                         |
| ----------- | -------- | ----------------------------------- |
| Description | Non      | Trajet (origine → destination)      |
| Détails     | Non      | Partenaire, mode, délai, poids      |
| Prix Achat  | Non      | `cost_price` (prix partenaire)      |
| Marge %     | **Oui**  | Pourcentage de marge modifiable     |
| Marge €     | Calculé  | `cost_price × margin_percent / 100` |
| Prix Vente  | Calculé  | `cost_price + margin_amount`        |
| Supprimer   | Oui      | Bouton corbeille                    |

**Section Frais (`QuoteItemEditor`) :**
| Champ       | Éditable | Description                    |
| ----------- | -------- | ------------------------------ |
| Description | Non      | Libellé du frais               |
| Prix Vente  | **Oui**  | Montant modifiable directement |
| Supprimer   | Oui      | Bouton corbeille               |

**Modal Ajout de Frais (`AddFeeModal`) :**
- Permet d'ajouter des frais prédéfinis ou personnalisés
- Champs : description, montant

**Modal Édition Client (`EditCustomerModal`) :**
- Permet de modifier les informations du client
- Champs : nom, société, email, date de validité

#### 4.3.4 Modal Recherche (`SearchModal.tsx`)

**Évolution proposée :** Transformer la page de recherche en modal pour améliorer l'ergonomie et permettre de lancer une recherche sans quitter le contexte actuel.

**Note importante :** Le mode de transport est sélectionné dans l'éditeur de devis (section 4.3.3) et passé à la modal. Il n'est plus modifiable dans la modal.

**Structure cible :**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐     │
│   │  Rechercher un transport                                     [X]  │     │
│   │  Mode : 🚚 Route                                                  │     │
│   ├───────────────────────────────────────────────────────────────────┤     │
│   │                                                                   │     │
│   │  ┌─────────────────────────┐  ┌─────────────────────────┐        │     │
│   │  │  📍 Origine             │  │  📍 Destination         │        │     │
│   │  │  ┌───────┐ ┌──────────┐ │  │  ┌───────┐ ┌──────────┐ │        │     │
│   │  │  │France▼│ │ 75001    │ │  │  │France▼│ │ 69002    │ │        │     │
│   │  │  └───────┘ └──────────┘ │  │  └───────┘ └──────────┘ │        │     │
│   │  │  ┌────────────────────┐ │  │  ┌────────────────────┐ │        │     │
│   │  │  │ Paris              │ │  │  │ Lyon               │ │        │     │
│   │  │  └────────────────────┘ │  │  └────────────────────┘ │        │     │
│   │  └─────────────────────────┘  └─────────────────────────┘        │     │
│   │                                                                   │     │
│   │  ┌──────────────────────────┐  ┌──────────────────────────┐      │     │
│   │  │📦 Marchandise            │  │📅 Date                   │      │     │
│   │  │                          │  │                          │      │     │
│   │  │ Poids (kg) *             │  │ Date d'expédition *      │      │     │
│   │  │ ┌──────────────────────┐ │  │ ┌──────────────────────┐ │      │     │
│   │  │ │ 500                  │ │  │ │ 27/01/2026           │ │      │     │
│   │  │ └──────────────────────┘ │  │ └──────────────────────┘ │      │     │
│   │  │                          │  │                          │      │     │
│   │  │ Volume (m3)              │  │                          │      │     │
│   │  │ ┌──────────────────────┐ │  │                          │      │     │
│   │  │ │ 2.5                  │ │  │                          │      │     │
│   │  │ └──────────────────────┘ │  │                          │      │     │
│   │  └──────────────────────────┘  └──────────────────────────┘      │     │
│   │                                                                   │     │
│   │  ┌───────────────┐  ┌─────────────────────────────────────────┐  │     │
│   │  │   Annuler     │  │         🔍 Rechercher les offres        │  │     │
│   │  └───────────────┘  └─────────────────────────────────────────┘  │     │
│   │                                                                   │     │
│   └───────────────────────────────────────────────────────────────────┘     │
│                                                                             │
│  (Arrière-plan : page des résultats ou devis en cours visible)              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Points d'accès à la modal :**
| Emplacement    | Action                          | Mode transport                  |
| -------------- | ------------------------------- | ------------------------------- |
| Header/Navbar  | Bouton "🔍 Rechercher"           | Aucun (tous modes)              |
| Éditeur Devis  | Bouton "+ Ajouter un transport" | Mode sélectionné dans l'éditeur |
| Page Résultats | Bouton "Nouvelle recherche"     | Mode précédent conservé         |

**Champs disponibles :**
| Champ                | Type         | Obligatoire | Description             |
| -------------------- | ------------ | ----------- | ----------------------- |
| `origin_country`     | Select       | Oui         | FR, DE, IT, ES, BE      |
| `origin_postal_code` | Text         | Non*        | Code postal origine     |
| `origin_city`        | Autocomplete | Non*        | Ville origine           |
| `dest_country`       | Select       | Oui         | FR, DE, IT, ES, BE      |
| `dest_postal_code`   | Text         | Non*        | Code postal destination |
| `dest_city`          | Autocomplete | Non*        | Ville destination       |
| `weight`             | Number       | Oui         | Poids en kg             |
| `volume`             | Number       | Non         | Volume en m³            |
| `shipping_date`      | Date         | Oui         | Date d'expédition       |

*Au moins ville OU code postal requis pour origine et destination.

**Paramètre passé (non modifiable) :**
| Paramètre        | Source           | Description                              |
| ---------------- | ---------------- | ---------------------------------------- |
| `transport_mode` | Éditeur de devis | ROAD, RAIL, AIR, SEA ou undefined (tous) |

**Comportement :**
| Action                | Résultat                                                   |
| --------------------- | ---------------------------------------------------------- |
| Clic "Rechercher"     | Ferme la modal, navigue vers `/results` avec les résultats |
| Clic "Annuler" ou "X" | Ferme la modal, reste sur la page actuelle                 |
| Clic hors modal       | Ferme la modal                                             |
| Touche Escape         | Ferme la modal                                             |

#### 4.3.5 Page Résultats (`Results.tsx`)

**Structure actuelle :**
```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Retour à la recherche                                                    │
│                                                                             │
│  3 offre(s) correspondante(s)                                               │
│  📍 Paris, 75001, France → 📍 Lyon, 69002, France | 📦 500 kg               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌────┐                                                             │   │
│  │  │ 🚚 │  DHL Express                                                │   │
│  │  └────┘  ┌──────┐ ┌────────────────┐                                │   │
│  │          │ ROAD │ │ 100 - 1000 kg  │                                │   │
│  │          └──────┘ └────────────────┘                                │   │
│  │                                                                     │   │
│  │  📍 dest: Lyon     🕐 transit: 24h     📅 validité: 2026-03-01      │   │
│  │                                                                     │   │
│  │                                    Prix estimé                      │   │
│  │                                    150.00 EUR   [➕ Ajouter au devis]│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌────┐                                                             │   │
│  │  │ 🚚 │  Transport Besson                                           │   │
│  │  └────┘  ┌──────┐ ┌────────────────┐                                │   │
│  │          │ ROAD │ │ 200 - 2000 kg  │                                │   │
│  │          └──────┘ └────────────────┘                                │   │
│  │                                                                     │   │
│  │  📍 dest: Dept 69  🕐 transit: 48h     📅 validité: illimitée       │   │
│  │                                                                     │   │
│  │                                    Prix estimé                      │   │
│  │                                    120.00 EUR   [➕ Ajouter au devis]│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌────┐                                                             │   │
│  │  │ 🚚 │  XPO Logistics                                              │   │
│  │  └────┘  ┌──────┐ ┌────────────────┐                                │   │
│  │          │ ROAD │ │ 50 - 800 kg    │                                │   │
│  │          └──────┘ └────────────────┘                                │   │
│  │                                                                     │   │
│  │  📍 dest: Lyon     🕐 transit: 36h     📅 validité: 2026-02-15      │   │
│  │                                                                     │   │
│  │                                    Prix estimé                      │   │
│  │                                    135.00 EUR   [➕ Ajouter au devis]│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Informations affichées par résultat :**
| Élément           | Source                                  | Description                          |
| ----------------- | --------------------------------------- | ------------------------------------ |
| Nom partenaire    | `quote.partner.name`                    | Nom du transporteur                  |
| Mode transport    | `quote.transport_mode`                  | ROAD, RAIL, AIR, SEA                 |
| Plage poids       | `quote.weight_min` - `quote.weight_max` | Capacité en kg                       |
| Délai transit     | `quote.delivery_time`                   | Durée de livraison                   |
| Ville destination | `quote.dest_city`                       | Ville de destination (si spécifique) |
| Validité          | `quote.valid_until`                     | Date limite de validité              |
| Prix              | `quote.cost` + `quote.currency`         | Prix estimé                          |

**Action disponible :** Bouton "Ajouter au devis" → appelle `addItem(quote.id, criteria.weight)`

#### 4.3.6 Sidebar Devis en Cours (`QuoteSidebar.tsx`)

**Structure actuelle :**
```
┌────────────────────────────────────────┐
│  🛒 Mon Devis en cours              [X]│  ← Header bleu foncé
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────────────────────────┐  │
│  │ ┌──────────┐                     │  │
│  │ │TRANSPORT │  500 kg         [🗑]│  │
│  │ └──────────┘                     │  │
│  │ Paris → Lyon                     │  │
│  │                                  │  │
│  │ DHL Express                      │  │
│  │              172.50 €            │  │
│  │              Marge: 15% (22.50 €)│  │
│  └──────────────────────────────────┘  │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │ ┌──────────┐                     │  │
│  │ │TRANSPORT │  500 kg         [🗑]│  │
│  │ └──────────┘                     │  │
│  │ Lyon → Marseille                 │  │
│  │                                  │  │
│  │ Transport Besson                 │  │
│  │              132.00 €            │  │
│  │              Marge: 10% (12.00 €)│  │
│  └──────────────────────────────────┘  │
│                                        │
│  ┌──────────────────────────────────┐  │
│  │ ┌──────┐                         │  │
│  │ │FRAIS │                     [🗑]│  │
│  │ └──────┘                         │  │
│  │ Frais de dossier                 │  │
│  │                       25.00 €    │  │
│  └──────────────────────────────────┘  │
│                                        │
├────────────────────────────────────────┤
│  Sous-total Transport      304.50 €    │
│  Frais annexes              25.00 €    │
│  ─────────────────────────────────     │
│  Total HT                  329.50 €    │
│  Marge Totale               34.50 €    │
│                                        │
│  ┌────────────┐  ┌────────────────┐    │
│  │   Vider    │  │ 📄 Finaliser   │    │
│  └────────────┘  └────────────────────┘│
└────────────────────────────────────────┘
```

**Fonctionnalités actuelles :**
| Action         | Fonction                                     | Description               |
| -------------- | -------------------------------------------- | ------------------------- |
| Fermer         | `closeSidebar()`                             | Ferme le panel latéral    |
| Supprimer item | `removeItem(item.id)`                        | Retire une ligne du devis |
| Vider          | `clearQuote()`                               | Supprime tout le devis    |
| Finaliser      | Navigation vers `/customer-quotes/{id}/edit` | Ouvre l'éditeur de prix   |

---

## 5. Cas d'usage

### 4.1 UC01 : Importer les tarifs d'un partenaire

```
Acteur: Administrateur
Précondition: Admin authentifié, fichier tarifs reçu du partenaire

Scénario principal:
1. L'admin accède à l'interface d'import
2. L'admin sélectionne le partenaire concerné
3. L'admin uploade le fichier (CSV, Excel ou PDF)
4. Le système détecte le format et parse le fichier
5. Le système affiche un aperçu avec le mapping des colonnes
6. L'admin valide le mapping (ou l'ajuste si nécessaire)
7. Le système valide et importe les tarifs
8. Le système affiche le rapport d'import (X succès, Y erreurs)

Extensions:
5a. Mapping incorrect détecté:
    5a1. L'admin corrige manuellement le mapping
    5a2. Retour étape 6

7a. Erreurs de validation:
    7a1. Le système liste les lignes en erreur
    7a2. L'admin peut télécharger le rapport d'erreurs
    7a3. Les lignes valides sont importées

Postcondition: Tarifs importés et disponibles pour recherche
```

### 4.2 UC02 : Rechercher des offres

```
Acteur: Client (via API ou interface)
Précondition: Aucune

Scénario principal:
1. Le client saisit son besoin:
   - Pays d'origine (obligatoire)
   - Code postal OU Ville d'origine (au moins un des deux)
   - Pays de destination (obligatoire)
   - Code postal OU Ville de destination (au moins un des deux)
   - Poids (optionnel)
   - Volume (optionnel)
2. Le système valide que chaque localisation a au moins un identifiant (CP ou ville)
3. Le système recherche les offres correspondantes
4. Le système classe par prix (par défaut)
5. Le système retourne les meilleures offres

Extensions:
2a. Validation échouée (ni CP ni ville):
    2a1. Le système affiche "Veuillez saisir un code postal ou une ville"
    2a2. Retour étape 1

Postcondition: Liste des offres affichée
```

### 4.3 UC03 : Générer et envoyer un devis

```
Acteur: Client
Précondition: Offres affichées (UC02)

Scénario principal:
1. Le client sélectionne une ou plusieurs offres
2. Le client saisit son email
3. Le système génère le PDF du devis
4. Le système envoie le devis par email
5. Le système confirme l'envoi

Postcondition: Devis envoyé et archivé
```

### 4.4 UC04 : Supprimer tous les tarifs d'un partenaire

```
Acteur: Administrateur
Précondition: Admin authentifié, partenaire existant avec des tarifs

Scénario principal:
1. L'admin accède à la page Partenaires
2. L'admin clique sur l'icône "Supprimer tarifs" du partenaire concerné
3. Le système affiche une modal de confirmation avec :
   - Le nom du partenaire
   - Le nombre de tarifs à supprimer
   - Un champ de saisie pour le code partenaire
4. L'admin saisit le code du partenaire pour confirmer
5. L'admin clique sur "Supprimer"
6. Le système supprime tous les tarifs du partenaire
7. Le système affiche une notification de succès avec le nombre de tarifs supprimés
8. La liste des partenaires est rafraîchie

Extensions:
3a. Aucun tarif associé au partenaire:
    3a1. Le système affiche un message "Aucun tarif à supprimer"
    3a2. Le bouton "Supprimer" est désactivé

4a. Code partenaire incorrect:
    4a1. Le bouton "Supprimer" reste désactivé
    4a2. L'admin corrige la saisie

5a. Annulation:
    5a1. L'admin clique sur "Annuler"
    5a2. La modal se ferme, aucune action effectuée

7a. Erreur lors de la suppression:
    7a1. Le système affiche une notification d'erreur
    7a2. Les tarifs ne sont pas supprimés

Postcondition: Tarifs du partenaire supprimés de la base de données
```

### 4.5 UC05 : Créer un devis multi-trajets (Workflow Panier) ✅ Implémenté

```
Acteur: Opérateur
Précondition: Tarifs importés, opérateur connecté

Scénario principal:
1. L'opérateur clique sur "Nouveau Devis" ou ajoute un tarif depuis les résultats
   → Un brouillon est créé automatiquement (DEV-2026-XXXX)
   → La sidebar "Devis en cours" s'ouvre

2. L'opérateur sélectionne un mode de transport (Route, Rail, Aérien, Maritime)
3. L'opérateur clique sur "+ Ajouter un transport"
   → La modal de recherche s'ouvre avec le mode pré-sélectionné

4. L'opérateur saisit les critères et lance la recherche
   → Les résultats s'affichent

5. L'opérateur clique sur "Ajouter au devis" pour un tarif
   → Le tarif est ajouté avec la marge par défaut du partenaire
   → La sidebar se met à jour avec les totaux

6. L'opérateur répète les étapes 2-5 pour ajouter d'autres trajets

7. L'opérateur clique sur "Finaliser" dans la sidebar
   → L'éditeur de devis s'ouvre

8. L'opérateur ajuste les marges si nécessaire
   → Les prix de vente sont recalculés automatiquement

9. L'opérateur ajoute des frais (dossier, assurance...)
   → Modal de saisie des frais

10. L'opérateur renseigne les informations client
    → Modal d'édition client (nom, société, email, validité)

11. L'opérateur enregistre le devis
    → Le devis passe en statut READY

Extensions:
1a. Ajout direct depuis les résultats sans devis en cours:
    1a1. Le système crée automatiquement un brouillon
    1a2. Le tarif est ajouté au nouveau devis
    1a3. La sidebar s'ouvre

5a. Tarif déjà dans le devis:
    5a1. Le bouton affiche "Retirer du devis"
    5a2. L'opérateur peut retirer le tarif

8a. Modification du prix de vente directement:
    8a1. L'opérateur saisit le prix de vente
    8a2. La marge est recalculée automatiquement

Postcondition: Devis créé avec plusieurs trajets, prêt à envoyer
```

### 4.6 UC06 : Supprimer un devis brouillon

```
Acteur: Opérateur
Précondition: Devis existant avec statut DRAFT

Scénario principal:
1. L'opérateur accède à la liste des devis
2. L'opérateur clique sur l'icône poubelle (🗑) d'un devis DRAFT
3. Le système demande confirmation
4. L'opérateur confirme la suppression
5. Le devis est supprimé
6. La liste est rafraîchie

Extensions:
2a. Le devis n'est pas en DRAFT:
    2a1. L'icône poubelle n'est pas visible
    2a2. Seule l'icône œil (👁) est disponible

Postcondition: Devis supprimé de la base de données
```

---

## 5. Flux de données

### 5.1 Format fichier d'entrée (attendu)

Le système accepte les colonnes suivantes (noms flexibles) :

| Champ système         | Variantes acceptées                  | Obligatoire |
| --------------------- | ------------------------------------ | ----------- |
| `transport_mode`      | mode, type_transport, mode_transport | ✓           |
| `origin_city`         | ville_origine, depart, from_city     | ✓           |
| `origin_country`      | pays_origine, from_country           | ✓           |
| `destination_city`    | ville_destination, arrivee, to_city  | ✓           |
| `destination_country` | pays_destination, to_country         | ✓           |
| `cost`                | prix, tarif, price, montant          | ✓           |
| `weight_min`          | poids_min, min_weight                | -           |
| `weight_max`          | poids_max, max_weight                | -           |
| `delivery_time`       | delai, transit_time, temps_livraison | -           |
| `valid_until`         | validite, expiration, date_fin       | -           |

### 5.2 Exemple CSV

```csv
mode_transport,ville_origine,pays_origine,ville_destination,pays_destination,poids_max,prix,delai
road,Paris,FR,Brussels,BE,1000,120.50,48h
road,Paris,FR,Amsterdam,NL,1000,180.00,72h
rail,Lyon,FR,Milan,IT,5000,350.00,96h
sea,Marseille,FR,Shanghai,CN,20000,2500.00,30d
air,Paris,FR,New York,US,500,850.00,24h
```

### 5.3 Exemple Excel

| Mode | Origine | Pays | Destination | Pays | Poids max (kg) | Prix (€) | Délai |
| ---- | ------- | ---- | ----------- | ---- | -------------- | -------- | ----- |
| road | Paris   | FR   | Brussels    | BE   | 1000           | 120.50   | 48h   |
| road | Paris   | FR   | Amsterdam   | NL   | 1000           | 180.00   | 72h   |
| rail | Lyon    | FR   | Milan       | IT   | 5000           | 350.00   | 96h   |

### 5.4 Données normalisées (sortie)

```json
{
  "partner_id": "uuid",
  "transport_mode": "ROAD",
  "origin_city": "Paris",
  "origin_country": "FR",
  "destination_city": "Brussels",
  "destination_country": "BE",
  "weight_max": 1000,
  "cost": 120.50,
  "currency": "EUR",
  "delivery_time": "48h",
  "is_active": true
}
```

---

## 6. Modèle de données

### 6.1 Schéma simplifié

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Partner      │       │  PartnerQuote   │       │ GeneratedQuote  │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id          PK  │───┐   │ id          PK  │       │ id          PK  │
│ name            │   │   │ partner_id  FK  │<──────│ quote_number    │
│ code            │   │   │ transport_mode  │       │ customer_email  │
│ is_active       │   └──>│ origin_city     │       │ items (JSON)    │
│ created_at      │       │ origin_country  │       │ total_amount    │
└─────────────────┘       │ dest_city       │       │ pdf_url         │
                          │ dest_country    │       │ status          │
┌─────────────────┐       │ weight_min      │       │ sent_at         │
│   ImportJob     │       │ weight_max      │       │ created_at      │
├─────────────────┤       │ cost            │       └─────────────────┘
│ id          PK  │       │ currency        │
│ partner_id  FK  │       │ delivery_time   │
│ filename        │       │ valid_until     │
│ status          │       │ is_active       │
│ total_rows      │       │ created_at      │
│ success_count   │       └────────┬────────┘
│ error_count     │                │
│ errors (JSON)   │                │
│ created_at      │                │
└─────────────────┘                │
                                   │
┌──────────────────────────────────┴───────────────────────────────────┐
│                        DEVIS CLIENTS (Workflow Panier)               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────┐       ┌───────────────────────┐                │
│  │  CustomerQuote  │       │  CustomerQuoteItem    │                │
│  ├─────────────────┤       ├───────────────────────┤                │
│  │ id          PK  │──────>│ id               PK   │                │
│  │ reference       │       │ quote_id         FK   │                │
│  │ status          │       │ item_type             │                │
│  │ customer_name   │       │ description           │                │
│  │ customer_email  │       │ partner_quote_id FK───┼── (vers PartnerQuote)
│  │ customer_company│       │ origin_city (snap)    │                │
│  │ transport_subtot│       │ dest_city (snap)      │                │
│  │ fees_total      │       │ partner_name (snap)   │                │
│  │ total           │       │ cost_price            │                │
│  │ total_margin    │       │ sell_price            │                │
│  │ valid_until     │       │ margin_percent        │                │
│  │ created_at      │       │ margin_amount         │                │
│  └─────────────────┘       └───────────────────────┘                │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 Modèles SQLAlchemy

```python
# app/models/partner.py

class Partner(Base):
    __tablename__ = "partners"

    id = Column(String, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    quotes = relationship("PartnerQuote", back_populates="partner")
    import_jobs = relationship("ImportJob", back_populates="partner")


class TransportMode(str, Enum):
    ROAD = "ROAD"
    RAIL = "RAIL"
    SEA = "SEA"
    AIR = "AIR"
    MULTIMODAL = "MULTIMODAL"


class PartnerQuote(Base):
    __tablename__ = "partner_quotes"

    id = Column(String, primary_key=True)
    partner_id = Column(String, ForeignKey("partners.id"))
    transport_mode = Column(Enum(TransportMode))
    origin_city = Column(String)
    origin_country = Column(String)
    dest_city = Column(String)
    dest_country = Column(String)
    weight_min = Column(Float, nullable=True)
    weight_max = Column(Float, nullable=True)
    cost = Column(Numeric(10, 2))  # Prix Achat Partenaire
    currency = Column(String, default="EUR")
    delivery_time = Column(String, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuoteItem(Base):
    """ détail d'une ligne de devis généré """
    __tablename__ = "quote_items"

    id = Column(String, primary_key=True)
    generated_quote_id = Column(String, ForeignKey("generated_quotes.id"))
    description = Column(String)      # ex: "Transport Paris->Lyon"
    cost_price = Column(Numeric(10, 2)) # Prix Achat
    sell_price = Column(Numeric(10, 2)) # Prix Vente (Client)
    margin_amount = Column(Numeric(10, 2)) # Marge
    item_type = Column(String) # "TRANSPORT" ou "FEE"


# ============ DEVIS CLIENTS (Workflow Panier) ============

class CustomerQuoteStatus(str, Enum):
    DRAFT = "DRAFT"         # En cours de construction
    READY = "READY"         # Prêt à envoyer
    SENT = "SENT"           # Envoyé au client
    ACCEPTED = "ACCEPTED"   # Accepté par le client
    REJECTED = "REJECTED"   # Refusé


class CustomerQuote(Base):
    """Devis client (cycle complet : brouillon → envoyé → accepté)"""
    __tablename__ = "customer_quotes"

    id = Column(String, primary_key=True)
    reference = Column(String, unique=True)  # DEV-2026-XXXX
    status = Column(Enum(CustomerQuoteStatus), default=CustomerQuoteStatus.DRAFT)

    # Client (optionnel en brouillon)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_company = Column(String, nullable=True)

    # Totaux (calculés)
    transport_subtotal = Column(Numeric(10, 2), default=0)
    fees_total = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), default=0)
    total_margin = Column(Numeric(10, 2), default=0)
    currency = Column(String, default="EUR")

    # Validité
    valid_until = Column(DateTime, nullable=True)

    # Métadonnées
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relations
    items = relationship("CustomerQuoteItem", back_populates="quote")


class CustomerQuoteItemType(str, Enum):
    TRANSPORT = "TRANSPORT"   # Trajet issu d'un tarif partenaire
    FEE = "FEE"               # Frais ajouté manuellement


class CustomerQuoteItem(Base):
    """Ligne de devis client (trajet ou frais)"""
    __tablename__ = "customer_quote_items"

    id = Column(String, primary_key=True)
    quote_id = Column(String, ForeignKey("customer_quotes.id"))
    item_type = Column(Enum(CustomerQuoteItemType))

    # Description
    description = Column(String)  # Ex: "Paris → Lyon" ou "Frais de dossier"

    # Référence au tarif source (NULL pour les frais)
    partner_quote_id = Column(String, ForeignKey("partner_quotes.id"), nullable=True)

    # Snapshot des données transport
    origin_city = Column(String, nullable=True)
    origin_country = Column(String, nullable=True)
    dest_city = Column(String, nullable=True)
    dest_country = Column(String, nullable=True)
    partner_name = Column(String, nullable=True)
    transport_mode = Column(String, nullable=True)
    delivery_time = Column(String, nullable=True)
    weight = Column(Float, nullable=True)

    # Prix
    cost_price = Column(Numeric(10, 2), default=0)   # Prix d'achat
    sell_price = Column(Numeric(10, 2))              # Prix de vente
    margin_percent = Column(Numeric(5, 2))           # Marge en %
    margin_amount = Column(Numeric(10, 2))           # Marge en EUR

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    quote = relationship("CustomerQuote", back_populates="items")
```

---

## 7. API Reference

### 7.1 Endpoints

| Méthode           | Endpoint                                       | Description                               |
| ----------------- | ---------------------------------------------- | ----------------------------------------- |
| `POST`            | `/api/v1/imports/upload`                       | Importer un fichier tarifs                |
| `GET`             | `/api/v1/imports/{id}`                         | Statut d'un import                        |
| `POST`            | `/api/v1/partners`                             | Créer un partenaire                       |
| `GET`             | `/api/v1/partners`                             | Liste des partenaires                     |
| `GET`             | `/api/v1/partners/{id}`                        | Détails d'un partenaire                   |
| `PUT`             | `/api/v1/partners/{id}`                        | Modifier un partenaire                    |
| `DELETE`          | `/api/v1/partners/{id}`                        | Supprimer un partenaire                   |
| `DELETE`          | `/api/v1/partners/{id}/quotes`                 | Supprimer tous les tarifs d'un partenaire |
| `GET`             | `/api/v1/cities/suggest`                       | Autocomplétion des villes                 |
| `POST`            | `/api/v1/match`                                | Rechercher des offres                     |
| `POST`            | `/api/v1/generated-quotes`                     | Générer un devis                          |
| `GET`             | `/api/v1/generated-quotes/{id}`                | Détail d'un devis                         |
|                   |                                                |                                           |
| **Devis Clients** |                                                |                                           |
| `POST`            | `/api/v1/customer-quotes`                      | Créer un nouveau devis (brouillon)        |
| `GET`             | `/api/v1/customer-quotes`                      | Lister les devis                          |
| `GET`             | `/api/v1/customer-quotes/{id}`                 | Détail d'un devis                         |
| `PUT`             | `/api/v1/customer-quotes/{id}`                 | Modifier un devis (client, validité)      |
| `DELETE`          | `/api/v1/customer-quotes/{id}`                 | Supprimer un devis                        |
| `POST`            | `/api/v1/customer-quotes/{id}/items`           | Ajouter un transport au devis             |
| `PUT`             | `/api/v1/customer-quotes/{id}/items/{item_id}` | Modifier une ligne (marge, prix)          |
| `DELETE`          | `/api/v1/customer-quotes/{id}/items/{item_id}` | Retirer une ligne                         |
| `POST`            | `/api/v1/customer-quotes/{id}/fees`            | Ajouter une ligne de frais                |

### 7.2 Import de fichier

```bash
POST /api/v1/imports/upload
Content-Type: multipart/form-data

# Paramètres
file: <fichier>              # CSV, Excel ou PDF
partner_id: <uuid>           # ID du partenaire
```

**Réponse (succès)**
```json
{
  "id": "uuid",
  "status": "COMPLETED",
  "total_rows": 150,
  "success_count": 147,
  "error_count": 3,
  "errors": [
    {
      "row": 45,
      "field": "cost",
      "message": "Le prix doit être positif",
      "value": "-50"
    }
  ]
}
```

### 7.3 Recherche d'offres

#### Description

Recherche des tarifs correspondant aux critères de transport.
**Règle de validation** : Pour l'origine et la destination, il faut saisir **soit un code postal, soit une ville** (ou les deux).

#### Paramètres

| Paramètre            | Type   | Requis        | Description                            |
| -------------------- | ------ | ------------- | -------------------------------------- |
| `origin_country`     | string | Oui           | Code pays ISO (ex: FR, BE)             |
| `origin_postal_code` | string | Conditionnel* | Code postal origine                    |
| `origin_city`        | string | Conditionnel* | Ville d'origine                        |
| `dest_country`       | string | Oui           | Code pays ISO destination              |
| `dest_postal_code`   | string | Conditionnel* | Code postal destination                |
| `dest_city`          | string | Conditionnel* | Ville de destination                   |
| `weight`             | number | Non           | Poids en kg                            |
| `volume`             | number | Non           | Volume en m³                           |
| `sort_by`            | string | Non           | Tri : `cost` (défaut), `delivery_time` |
| `limit`              | number | Non           | Nombre max de résultats (défaut: 10)   |

*\* Conditionnel : Au moins `postal_code` OU `city` requis pour origine et destination*

#### Exemples de requêtes valides

```bash
# Recherche par ville uniquement
POST /api/v1/match
{
  "origin_country": "FR",
  "origin_city": "Paris",
  "dest_country": "BE",
  "dest_city": "Brussels",
  "weight": 500
}

# Recherche par code postal uniquement
POST /api/v1/match
{
  "origin_country": "FR",
  "origin_postal_code": "75001",
  "dest_country": "BE",
  "dest_postal_code": "1000",
  "weight": 500
}

# Recherche mixte (ville + code postal)
POST /api/v1/match
{
  "origin_country": "FR",
  "origin_city": "Paris",
  "origin_postal_code": "75001",
  "dest_country": "BE",
  "dest_city": "Brussels",
  "weight": 500
}
```

#### Réponse (erreur de validation - 400)

```json
{
  "detail": "L'origine doit contenir au moins un code postal ou une ville"
}
```

#### Réponse (succès - 200)

```json
{
  "quotes": [
    {
      "id": "uuid",
      "partner_id": "uuid",
      "transport_mode": "ROAD",
      "origin_city": "Paris",
      "origin_country": "FR",
      "dest_city": "Brussels",
      "dest_country": "BE",
      "cost": "120.50",
      "currency": "EUR",
      "delivery_time": "48h"
    }
  ],
  "total": 1
}
```

### 7.4 Générer un devis

```bash
POST /api/v1/generated-quotes
Content-Type: application/json

{
  "customer_id": "uuid",
  "items": [
    {"id": "quote-uuid-1", "cost": 120.50},
    {"id": "quote-uuid-2", "cost": 180.00}
  ],
  "valid_until": "2026-02-28T00:00:00Z"
}
```

**Réponse**
```json
{
  "id": "uuid",
  "quote_number": "DEV-20260124-A1B2C3",
  "total_amount": "300.50",
  "currency": "EUR",
  "status": "DRAFT",
  "created_at": "2026-01-24T10:30:00Z"
}
```

### 7.5 Supprimer tous les tarifs d'un partenaire

#### Description

Supprime l'ensemble des tarifs (`PartnerQuote`) associés à un partenaire donné.
Cette action est irréversible et nécessite une confirmation côté interface.

#### Cas d'utilisation

- Réinitialiser les tarifs avant un nouvel import
- Nettoyer les données obsolètes d'un partenaire
- Supprimer les tarifs d'un partenaire désactivé

#### Requête

```bash
DELETE /api/v1/partners/{partner_id}/quotes

# Exemple
curl -X DELETE http://localhost:3000/api/v1/partners/a619635b-32b3-4003-9953-5c71dc1c5007/quotes
```

#### Paramètres

| Paramètre    | Type | Requis | Description                      |
| ------------ | ---- | ------ | -------------------------------- |
| `partner_id` | UUID | Oui    | Identifiant unique du partenaire |

#### Réponse (succès - 200)

```json
{
  "message": "Tarifs supprimés avec succès",
  "partner_id": "a619635b-32b3-4003-9953-5c71dc1c5007",
  "deleted_count": 1620
}
```

#### Réponse (partenaire non trouvé - 404)

```json
{
  "detail": "Partenaire non trouvé"
}
```

#### Réponse (aucun tarif - 200)

```json
{
  "message": "Aucun tarif à supprimer",
  "partner_id": "a619635b-32b3-4003-9953-5c71dc1c5007",
  "deleted_count": 0
}
```

#### Interface utilisateur

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Supprimer les tarifs                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ⚠️  Attention : Cette action est irréversible !                    │
│                                                                     │
│  Vous êtes sur le point de supprimer tous les tarifs                │
│  du partenaire "DHL Express".                                       │
│                                                                     │
│  Nombre de tarifs concernés : 1,620                                 │
│                                                                     │
│  Pour confirmer, tapez le code du partenaire : DHL                  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│                          [Annuler]  [Supprimer]                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Flux de suppression

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Bouton    │────>│   Modal     │────>│   API       │────>│   Toast     │
│  "Supprimer │     │ Confirmation│     │   DELETE    │     │   Succès    │
│   tarifs"   │     │ + Saisie    │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                          │
                          │ Annulation
                          v
                    ┌─────────────┐
                    │   Fermer    │
                    │   Modal     │
                    └─────────────┘
```

### 7.6 Autocomplétion des villes ✅ Implémenté

#### Description

Retourne une liste de villes correspondant à la recherche, basée sur les villes présentes dans les tarifs importés.
Utilisé pour l'autocomplétion dans le formulaire de recherche.

#### Requête

```bash
GET /api/v1/cities/suggest?q={query}&type={origin|dest}&limit={limit}

# Exemples
curl "http://localhost:3000/api/v1/cities/suggest?q=par&type=origin&limit=10"
curl "http://localhost:3000/api/v1/cities/suggest?q=lyon&type=dest"
```

#### Paramètres

| Paramètre | Type   | Requis | Défaut | Description                                 |
| --------- | ------ | ------ | ------ | ------------------------------------------- |
| `q`       | string | Oui    | -      | Terme de recherche (min 2 caractères)       |
| `type`    | string | Non    | `both` | Type de ville : `origin`, `dest`, ou `both` |
| `limit`   | int    | Non    | 10     | Nombre max de suggestions                   |

#### Réponse (succès - 200)

```json
{
  "suggestions": [
    {
      "city": "Paris",
      "country": "FR",
      "quote_count": 1250
    },
    {
      "city": "Paray-le-Monial",
      "country": "FR",
      "quote_count": 45
    },
    {
      "city": "Parthenay",
      "country": "FR",
      "quote_count": 12
    }
  ],
  "total": 3
}
```

#### Réponse (requête trop courte - 400)

```json
{
  "detail": "Le terme de recherche doit contenir au moins 2 caractères"
}
```

#### Algorithme de recherche

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Recherche de villes                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Normalisation du terme (lowercase, trim)                        │
│                                                                     │
│  2. Requête SQL :                                                   │
│     SELECT DISTINCT city, country, COUNT(*) as quote_count          │
│     FROM partner_quotes                                             │
│     WHERE LOWER(origin_city) LIKE 'par%'                            │
│        OR LOWER(dest_city) LIKE 'par%'                              │
│     GROUP BY city, country                                          │
│     ORDER BY quote_count DESC                                       │
│     LIMIT 10                                                        │
│                                                                     │
│  3. Retour JSON avec suggestions triées par pertinence              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### Implémentation Frontend

```typescript
// Composant React avec debounce et navigation clavier
const [query, setQuery] = useState('');
const [suggestions, setSuggestions] = useState([]);
const [activeIndex, setActiveIndex] = useState(-1);
const [isOpen, setIsOpen] = useState(false);

// Debounce pour la recherche
useEffect(() => {
  if (query.length < 2) {
    setSuggestions([]);
    setIsOpen(false);
    return;
  }

  const timer = setTimeout(async () => {
    const response = await api.get('/cities/suggest', {
      params: { q: query, type: 'origin' }
    });
    setSuggestions(response.data.suggestions);
    setIsOpen(true);
    setActiveIndex(-1);
  }, 300);

  return () => clearTimeout(timer);
}, [query]);

// Gestion du clavier
const handleKeyDown = (e: React.KeyboardEvent) => {
  if (!isOpen || suggestions.length === 0) return;

  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      setActiveIndex(prev =>
        prev < suggestions.length - 1 ? prev + 1 : 0
      );
      break;
    case 'ArrowUp':
      e.preventDefault();
      setActiveIndex(prev =>
        prev > 0 ? prev - 1 : suggestions.length - 1
      );
      break;
    case 'Enter':
    case 'Tab':
      if (activeIndex >= 0) {
        e.preventDefault();
        selectCity(suggestions[activeIndex]);
      }
      break;
    case 'Escape':
      setIsOpen(false);
      setActiveIndex(-1);
      break;
  }
};

const selectCity = (city: CitySuggestion) => {
  setQuery(`${city.city} (${city.country})`);
  setIsOpen(false);
  onSelect(city); // Callback parent
};
```

#### Rendu JSX

```tsx
<div className="relative">
  <input
    value={query}
    onChange={(e) => setQuery(e.target.value)}
    onKeyDown={handleKeyDown}
    onFocus={() => suggestions.length > 0 && setIsOpen(true)}
    placeholder="Rechercher une ville..."
  />

  {isOpen && suggestions.length > 0 && (
    <ul className="absolute w-full bg-white border rounded-lg shadow-lg mt-1 max-h-60 overflow-auto">
      {suggestions.map((city, index) => (
        <li
          key={`${city.city}-${city.country}`}
          className={`px-4 py-2 cursor-pointer flex justify-between
            ${index === activeIndex ? 'bg-blue-100' : 'hover:bg-gray-100'}`}
          onClick={() => selectCity(city)}
          onMouseEnter={() => setActiveIndex(index)}
        >
          <span>📍 {city.city} ({city.country})</span>
          <span className="text-gray-400 text-sm">{city.quote_count} tarifs</span>
        </li>
      ))}
    </ul>
  )}
</div>
```

### 7.7 API Devis Clients ✅ Implémenté

#### Créer un devis

```bash
POST /api/v1/customer-quotes
Content-Type: application/json

{
  "customer_name": "Société ABC",
  "customer_email": "contact@abc.fr",
  "customer_company": "SARL ABC",
  "valid_until": "2026-02-28"
}
```

**Réponse (201)**
```json
{
  "id": "uuid",
  "reference": "DEV-2026-0042",
  "status": "DRAFT",
  "customer_name": "Société ABC",
  "items": [],
  "transport_subtotal": 0,
  "fees_total": 0,
  "total": 0,
  "total_margin": 0
}
```

#### Ajouter un transport au devis

```bash
POST /api/v1/customer-quotes/{quote_id}/items
Content-Type: application/json

{
  "partner_quote_id": "uuid-du-tarif",
  "weight": 500
}
```

**Réponse (201)**
```json
{
  "id": "item-uuid",
  "item_type": "TRANSPORT",
  "description": "Paris → Lyon",
  "origin_city": "Paris",
  "dest_city": "Lyon",
  "partner_name": "DHL Express",
  "transport_mode": "ROAD",
  "delivery_time": "24h",
  "weight": 500,
  "cost_price": 150.00,
  "margin_percent": 15.00,
  "margin_amount": 22.50,
  "sell_price": 172.50
}
```

#### Modifier la marge d'une ligne

```bash
PUT /api/v1/customer-quotes/{quote_id}/items/{item_id}
Content-Type: application/json

{
  "margin_percent": 20.00
}
```

**Réponse (200)** - Recalcul automatique du prix de vente
```json
{
  "id": "item-uuid",
  "cost_price": 150.00,
  "margin_percent": 20.00,
  "margin_amount": 30.00,
  "sell_price": 180.00
}
```

#### Ajouter une ligne de frais

```bash
POST /api/v1/customer-quotes/{quote_id}/fees
Content-Type: application/json

{
  "description": "Frais de dossier",
  "sell_price": 25.00
}
```

**Réponse (201)**
```json
{
  "id": "fee-uuid",
  "item_type": "FEE",
  "description": "Frais de dossier",
  "cost_price": 0,
  "sell_price": 25.00,
  "margin_percent": 100,
  "margin_amount": 25.00
}
```

#### Modifier les informations client

```bash
PUT /api/v1/customer-quotes/{quote_id}
Content-Type: application/json

{
  "customer_name": "Nouveau Nom",
  "customer_company": "Nouvelle Société",
  "customer_email": "nouveau@email.fr",
  "valid_until": "2026-03-15"
}
```

#### Supprimer un devis (DRAFT uniquement)

```bash
DELETE /api/v1/customer-quotes/{quote_id}
```

**Réponse (200)**
```json
{
  "message": "Devis supprimé avec succès"
}
```

**Réponse (400)** - Si le statut n'est pas DRAFT
```json
{
  "detail": "Seuls les devis en brouillon peuvent être supprimés"
}
```

---

## 8. Stack technique

### 8.1 Technologies

| Composant         | Technologie           |
| ----------------- | --------------------- |
| Backend           | Python 3.12 + FastAPI |
| Base de données   | PostgreSQL 16         |
| ORM               | SQLAlchemy + Alembic  |
| Parsing CSV/Excel | pandas + openpyxl     |
| Parsing PDF       | pdfplumber            |
| Génération PDF    | reportlab             |
| Email             | aiosmtplib            |
| Cache             | Redis                 |

### 8.2 Structure du projet

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   │
│   ├── models/
│   │   ├── partner.py
│   │   ├── partner_quote.py
│   │   ├── import_job.py
│   │   ├── customer.py
│   │   └── generated_quote.py
│   │
│   ├── schemas/
│   │   ├── partner.py
│   │   ├── partner_quote.py
│   │   └── ...
│   │
│   ├── api/
│   │   ├── partners.py
│   │   ├── quotes.py
│   │   ├── imports.py
│   │   ├── matching.py
│   │   ├── generated_quotes.py
│   │   └── customer_quotes.py      # ✅ Devis clients (Panier)
│   │
│   └── services/
│       ├── import_service.py
│       ├── matching_service.py
│       └── quote_generator.py
│
├── alembic/
│   └── versions/
│
├── configs/
│   └── partners/
│       └── example.yaml
│
├── uploads/
├── requirements.txt
├── alembic.ini
└── Dockerfile

frontend/src/
├── pages/
│   ├── CustomerQuotes.tsx          # ✅ Liste des devis clients
│   ├── CustomerQuoteDetail.tsx     # ✅ Détail d'un devis
│   ├── CustomerQuoteEditor.tsx     # ✅ Éditeur de devis (marges, frais)
│   ├── Results.tsx                 # ✅ Résultats + bouton "Ajouter au devis"
│   └── ...
│
├── components/
│   ├── customer-quote/
│   │   ├── QuoteSidebar.tsx        # ✅ Panel latéral "Devis en cours"
│   │   ├── QuoteItem.tsx           # ✅ Ligne de devis (sidebar)
│   │   └── editor/
│   │       ├── QuoteItemEditor.tsx # ✅ Ligne éditable (marge)
│   │       ├── AddFeeModal.tsx     # ✅ Modal ajout de frais
│   │       └── EditCustomerModal.tsx # ✅ Modal édition client
│   │
│   ├── SearchModal.tsx             # ✅ Modal de recherche
│   └── ...
│
├── context/
│   └── CustomerQuoteContext.tsx    # ✅ Context pour le devis en cours
│
├── services/
│   └── customerQuoteService.ts     # ✅ API calls pour devis clients
│
└── types/
    └── customerQuote.ts            # ✅ Types TypeScript
```

### 8.3 Dépendances

```txt
# requirements.txt

fastapi==0.109.2
uvicorn[standard]==0.27.1
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic==2.6.1
pydantic-settings==2.1.0
pandas==2.2.0
openpyxl==3.1.2
pdfplumber==0.10.3
reportlab==4.0.9
redis==5.0.1
python-multipart==0.0.9
pyyaml==6.0.1
```

---

## 9. Déploiement

### 9.1 Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/transport_quote
      REDIS_HOST: redis
      REDIS_PORT: 6379
    volumes:
      - ./backend/uploads:/app/uploads
      - ./backend/configs:/app/configs
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: transport_quote
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 9.2 Variables d'environnement

```bash
# .env

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/transport_quote

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Storage
UPLOAD_DIR=./uploads
PARTNER_CONFIGS_DIR=./configs/partners

# Email (optionnel)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=password
```

### 9.3 Démarrage

```bash
# Installation
cd backend
pip install -r requirements.txt

# Migrations
alembic revision --autogenerate -m "initial"
alembic upgrade head

# Développement
uvicorn app.main:app --reload --port 3000

# Avec Docker
docker-compose up -d
```

---

## Résumé

Application en 4 modules principaux :

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│     IMPORT      │     │    MATCHING     │     │  DEVIS CLIENT   │     │   GENERATOR     │
│ ─────────────── │     │ ─────────────── │     │ ─────────────── │     │ ─────────────── │
│                 │     │                 │     │                 │     │                 │
│ Admin uploade   │────>│ Client cherche  │────>│ Workflow Panier │────>│ Devis PDF       │
│ fichiers tarifs │     │ les offres      │     │ Multi-trajets   │     │ envoyé par mail │
│                 │     │                 │     │                 │     │                 │
│ CSV/Excel/PDF   │     │ Tri par prix    │     │ Marges, Frais   │     │ (À venir)       │
│ → Base données  │     │ ou délai        │     │ Client info     │     │                 │
│                 │     │                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Points clés :**
- Pas d'API partenaire complexe → Simple upload de fichiers
- Pas de formulaire de saisie → Tout passe par les fichiers
- Admin centralise les imports → Contrôle qualité des données
- Parsing intelligent → CSV, Excel, PDF supportés
- **Workflow Panier** → Construction progressive du devis multi-trajets
- **Gestion des marges** → Marge par défaut partenaire, ajustable par ligne
- **Frais annexes** → Ajout de frais manuels (dossier, assurance...)
