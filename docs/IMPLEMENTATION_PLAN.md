# Plan d'Implémentation - Transport Quote (MVP)

Ce plan détaille les étapes de développement de l'application "Transport Quote" dans sa version "Outil Interne / Admin".

**Objectif** : Fournir une plateforme permettant à un administrateur d'importer des tarifs transporteurs (CSV, Excel, PDF) et de générer des devis pour des clients finaux.

**Stack technique** : Python + FastAPI, SQLAlchemy, PostgreSQL, React + Vite

## Phase 1 : Initialisation du Projet & Infrastructure

- [x] **Initialisation du Backend Python**
    - [x] Setup FastAPI avec structure modulaire
    - [x] Configuration SQLAlchemy + Alembic
    - [x] Modèles de données (Partner, PartnerQuote, ImportJob, Customer, GeneratedQuote)
    - [x] Schémas Pydantic pour validation API
- [ ] **Infrastructure**
    - [x] Configuration Docker & Docker Compose (PostgreSQL, Redis)
    - [x] Exécuter migration initiale Alembic
    - [x] Tester démarrage application
- [x] **Frontend**
    - [x] Setup Frontend (Vite + React + Tailwind) pour l'interface Admin

## Phase 2 : Module Partenaires & Gestion des Tarifs

- [x] **API Gestion des Partenaires**
    - [x] CRUD Endpoints `Partners` (Create, Read, Update, Delete)
    - [x] Services de gestion
    - [x] Endpoint suppression tarifs partenaire `DELETE /partners/{id}/quotes`
- [x] **API Gestion des Tarifs**
    - [x] CRUD Endpoints `PartnerQuotes`
    - [x] Filtres et recherche basique (par mode, partenaire)
- [x] **Interface suppression tarifs** (Frontend)
    - [x] Bouton "Supprimer tarifs" dans la page Partenaires
    - [x] Modal de confirmation avec nombre de tarifs
    - [x] Notification de succès/erreur

## Phase 3 : Module d'Import (Coeur du Système)

- [x] **Moteur d'Import**
    - [x] Création du service `ImportService` (Gestion des Jobs)
    - [x] Endpoint d'upload de fichiers (python-multipart)
- [x] **Parsers**
    - [x] Implémentation `CsvParser` (pandas)
    - [x] Implémentation `ExcelParser` (pandas + openpyxl)
    - [x] Implémentation `PdfParser` (pdfplumber)
- [x] **Configuration par Partenaire**
    - [x] Chargement des fichiers YAML de configuration
    - [x] Mapping des colonnes selon config
- [x] **Validation & Mapping**
    - [x] Service de validation des données (Pydantic)
    - [x] Logique de feedback (Rapport d'erreurs par ligne)

## Phase 4 : Module de Correspondance (Matching)

- [x] **Moteur de Recherche**
    - [x] Endpoint de recherche `POST /quotes/match`
        - [x] Payload: `origin` (city/country), `dest` (city/country), `weight`, `volume`, `date`
    - [x] Service de filtrage
        - [x] Correspondance Exacte (Code Postal / Ville)
        - [x] Compatibilité Poids/Volume (Min/Max)
        - [x] Validité Date
- [x] **Flexible Search Validation**
    - [x] Backend: Update Pydantic Schema `matching.py` (Conditional Validation)
    - [x] Frontend: Update `Search.tsx` (Remove required, manual validation)
    - [ ] **Refinement Matching**: Fallback sur la Ville si Code Postal manquant (vs Wildcard)
- [ ] **Stratégies de Tri**
    - [ ] Tri par Prix (croissant)
    - [ ] Tri par Délai (court)
- [x] **Autocomplétion des villes**
    - [x] Endpoint `GET /cities/suggest` (Backend)
        - [x] Paramètres : `q` (query), `type` (origin/dest), `limit`
        - [x] Recherche insensible à la casse
        - [x] Retour : ville, pays, nombre de tarifs
    - [x] Service `CityService.suggest()` (Backend)
        - [x] Requête SQL avec DISTINCT et COUNT
        - [x] Tri par nombre de tarifs (pertinence)
    - [x] Composant `CityAutocomplete` (Frontend)
        - [x] Input avec debounce (300ms)
        - [x] Dropdown de suggestions
        - [x] Affichage ville + pays + badge count
        - [x] **Navigation clavier**
            - [x] `↓` ArrowDown : élément suivant
            - [x] `↑` ArrowUp : élément précédent
            - [x] `Enter` : valider la sélection
            - [x] `Tab` : valider et passer au champ suivant
            - [x] `Escape` : fermer le dropdown
        - [x] Surlignage de l'élément actif
        - [x] Support souris (hover + clic)

## Phase 5 : Module de Génération de Devis

- [ ] **Architecture "Panier" (CustomerQuote)**
    - [ ] Modèles `CustomerQuote` (Brouillon) et `CustomerQuoteItem` (Transport/Frais) <!-- id: model-customer-quote -->
    - [ ] Énumération `CustomerQuoteStatus` (DRAFT, READY, SENT...) <!-- id: model-status -->
    - [ ] Ajout champ `default_margin` sur le modèle `Partner` <!-- id: model-partner-margin -->
- [ ] **Services Métier**
    - [ ] `CustomerQuoteService` : CRUD et gestion du cycle de vie <!-- id: service-quote -->
    - [ ] `PricingService` : Calcul des marges, prix de vente et totaux <!-- id: service-pricing -->
- [ ] **API Endpoints**
    - [ ] `POST /customer-quotes` (Création brouillon) <!-- id: api-quote-create -->
    - [ ] `POST /customer-quotes/{id}/items` (Ajout tarif transport) <!-- id: api-quote-add-item -->
    - [ ] `POST /customer-quotes/{id}/fees` (Ajout frais manuel) <!-- id: api-quote-add-fee -->
    - [ ] `PUT /customer-quotes/{id}/items/{itemId}` (Ajustement Marge/Prix) <!-- id: api-quote-update -->
- [ ] **Génération de Documents**
    - [ ] Service PDF (reportlab) avec prix de vente uniquement <!-- id: service-pdf -->
    - [ ] Stockage local des fichiers générés <!-- id: storage -->
- [ ] **Envoi de Devis**
    - [ ] Service Email (aiosmtplib - Mock pour dev) <!-- id: service-email -->
    - [ ] Endpoint de génération et envoi <!-- id: api-quote-send -->

## Phase 6 : Interface Admin (Frontend)

- [x] **Espace Admin**
    - [x] Dashboard (Vue d'ensemble Partenaires) <!-- id: ui-dashboard -->
    - [x] Gestion des Partenaires (CRUD + Config YAML) <!-- id: ui-partners -->
    - [x] Gestion des Imports (Upload + Logs) <!-- id: ui-imports -->
- [x] **Espace Client / Opérateur**
    - [x] Wizard de Recherche (`/search`) <!-- id: ui-wizard -->
        - [x] Formulaire "Step-by-Step" ou "Single Page"
        - [x] Autocomplete pour Villes/Pays (Dropdown Pays, Input Ville)
        - [x] Sélecteur de Mode (Route, Air, Mer)
    - [x] **Page de Résultats (`/results`)** <!-- id: ui-results -->
        - [x] Liste des offres compatibles (Cartes)
        - [x] Affichage Prix Vente (avec Marge simulée)
        - [x] Affichage Délai & Transporteur
        - [ ] Bouton "Ajouter au devis" (vs "Selectionner")
    - [ ] **Module Devis Client (Nouveau)** <!-- id: ui-customer-quotes -->
        - [ ] Contexte Global `CustomerQuoteContext` (Panier)
        - [ ] Composant `QuoteSidebar` (Panneau latéral persistant)
        - [ ] Page `CustomerQuotes` (Liste des devis)
        - [ ] Page `CustomerQuoteEditor` (Constructeur de devis avec édition marges)
        - [ ] Sélection des services additionnels
        - [ ] Génération finale du PDF/Email

## Phase 7 : Tests & Validation

- [ ] **Tests**
    - [ ] Tests Unitaires avec pytest
    - [ ] Tests E2E (Flux complet Import -> Match -> Devis)
- [ ] **Documentation**
    - [ ] Swagger/OpenAPI (généré automatiquement par FastAPI)
    - [ ] README d'installation
