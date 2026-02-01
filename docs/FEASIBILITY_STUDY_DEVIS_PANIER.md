# Étude de Faisabilité : Workflow Devis en mode "Panier"

## Objectif

Ce document analyse les modifications nécessaires pour implémenter l'approche "Panier" décrite dans `PROPOSAL_DEVIS_PANIER.md`.

---

## 1. État actuel de l'application

### 1.1 Backend - Fichiers existants

| Fichier | État | Remarques |
|---------|------|-----------|
| `app/models/generated_quote.py` | Existant | Modèle `GeneratedQuote` avec statut, items JSON |
| `app/models/customer.py` | Existant | Modèle `Customer` basique |
| `app/schemas/generated_quote.py` | Existant | Schémas Pydantic simples |
| `app/api/generated_quotes.py` | **Stub vide** | Juste un `router = APIRouter()` |
| `app/api/customers.py` | **Stub vide** | Juste un `router = APIRouter()` |
| `app/services/` | Existants | Aucun service pour les devis |

### 1.2 Frontend - Fichiers existants

| Fichier | État | Remarques |
|---------|------|-----------|
| `src/pages/Results.tsx` | Existant | Bouton "Sélectionner" sans action |
| `src/pages/Search.tsx` | Existant | Formulaire de recherche |
| `src/types/index.ts` | Existant | Types `Quote`, `SearchCriteria` |
| `src/services/` | Existant | Services pour partners, quotes, imports |
| `src/context/` | **Inexistant** | Dossier à créer |

### 1.3 Éléments réutilisables

| Élément | Réutilisation |
|---------|---------------|
| `QuoteStatus` enum | Oui - mêmes statuts (DRAFT, SENT, ACCEPTED...) |
| `Customer` model | Oui - référence optionnelle |
| `PartnerQuote` model | Oui - source des items |
| Layout & Navigation | Oui - ajouter nouvelles routes |
| Search.tsx | Partiel - intégrer le contexte CustomerQuote |
| Results.tsx | Partiel - modifier bouton "Sélectionner" |

---

## 2. Modifications Backend

### 2.1 Nouveaux fichiers à créer

| Fichier | Description | Effort |
|---------|-------------|--------|
| `app/models/customer_quote.py` | Modèles `CustomerQuote` + `CustomerQuoteItem` + `CustomerQuoteItemType` | 1h |
| `app/schemas/customer_quote.py` | Schémas Pydantic pour les devis client | 45min |
| `app/services/customer_quote_service.py` | Logique métier des devis | 2h |
| `app/services/pricing_service.py` | Calcul automatique des marges | 1h |
| `migrations/versions/xxx_add_customer_quotes.py` | Migration Alembic | 15min |

### 2.2 Fichiers à modifier

| Fichier | Modifications | Effort |
|---------|---------------|--------|
| `app/models/__init__.py` | Import nouveaux modèles | 5min |
| `app/models/partner.py` | Ajout champ `default_margin` | 15min |
| `app/api/__init__.py` | Ajouter route `/customer-quotes` | 5min |
| `app/api/generated_quotes.py` | Implémenter endpoints (ou fusionner avec customer-quotes) | 30min |

### 2.3 Détail des modèles à créer

```python
# app/models/customer_quote.py

class CustomerQuoteStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class CustomerQuoteItemType(str, Enum):
    TRANSPORT = "TRANSPORT"   # Trajet issu d'un tarif partenaire
    FEE = "FEE"               # Frais ajouté manuellement


class CustomerQuote(Base):
    __tablename__ = "customer_quotes"

    id = Column(String, primary_key=True)
    reference = Column(String, unique=True)  # DEV-2026-XXXX
    status = Column(Enum(CustomerQuoteStatus), default=CustomerQuoteStatus.DRAFT)

    # Client (optionnel en brouillon)
    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_company = Column(String, nullable=True)

    # Totaux
    transport_subtotal = Column(Numeric(10, 2), default=0)  # Sous-total transports
    fees_total = Column(Numeric(10, 2), default=0)          # Total frais
    total = Column(Numeric(10, 2), default=0)               # Grand total
    total_margin = Column(Numeric(10, 2), default=0)        # Marge totale
    currency = Column(String, default="EUR")

    # Validité et tracking
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)

    # Relations
    items = relationship("CustomerQuoteItem", back_populates="quote", cascade="all, delete-orphan")


class CustomerQuoteItem(Base):
    __tablename__ = "customer_quote_items"

    id = Column(String, primary_key=True)
    quote_id = Column(String, ForeignKey("customer_quotes.id"))

    # Type de ligne (TRANSPORT ou FEE)
    item_type = Column(Enum(CustomerQuoteItemType), default=CustomerQuoteItemType.TRANSPORT)

    # Description (généré pour transport, saisi pour frais)
    description = Column(String)  # Ex: "Paris → Lyon" ou "Frais de dossier"

    # Référence au tarif source (NULL pour les frais)
    partner_quote_id = Column(String, ForeignKey("partner_quotes.id"), nullable=True)

    # Snapshot des données transport (NULL pour les frais)
    origin_city = Column(String, nullable=True)
    origin_country = Column(String, nullable=True)
    dest_city = Column(String, nullable=True)
    dest_country = Column(String, nullable=True)
    partner_name = Column(String, nullable=True)
    transport_mode = Column(String, nullable=True)
    delivery_time = Column(String, nullable=True)
    weight = Column(Numeric(10, 2), nullable=True)

    # Prix
    cost_price = Column(Numeric(10, 2), default=0)   # Prix d'achat (0 pour frais)
    sell_price = Column(Numeric(10, 2))              # Prix de vente
    margin_percent = Column(Numeric(5, 2))           # Marge en %
    margin_amount = Column(Numeric(10, 2))           # Marge en EUR

    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    quote = relationship("CustomerQuote", back_populates="items")
    source_quote = relationship("PartnerQuote")
```

**Modification du modèle Partner existant :**

```python
# app/models/partner.py (ajout)

class Partner(Base):
    # ... champs existants ...
    default_margin = Column(Numeric(5, 2), default=20.00)  # Marge par défaut en %
```

### 2.4 Endpoints API à implémenter

**Gestion des devis :**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/customer-quotes` | POST | Créer un nouveau brouillon |
| `/api/v1/customer-quotes` | GET | Lister les devis |
| `/api/v1/customer-quotes/{id}` | GET | Détail d'un devis |
| `/api/v1/customer-quotes/{id}` | PUT | Modifier (client, validité) |
| `/api/v1/customer-quotes/{id}` | DELETE | Supprimer |

**Gestion des lignes transport :**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/customer-quotes/{id}/items` | POST | Ajouter un tarif (marge auto) |
| `/api/v1/customer-quotes/{id}/items/{item_id}` | PUT | Modifier marge/prix |
| `/api/v1/customer-quotes/{id}/items/{item_id}` | DELETE | Retirer |

**Gestion des frais :**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/customer-quotes/{id}/fees` | POST | Ajouter une ligne de frais |
| `/api/v1/customer-quotes/{id}/fees/{item_id}` | PUT | Modifier un frais |
| `/api/v1/customer-quotes/{id}/fees/{item_id}` | DELETE | Supprimer un frais |

**Actions :**

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/customer-quotes/{id}/generate-pdf` | POST | Générer PDF |
| `/api/v1/customer-quotes/{id}/send` | POST | Envoyer par email |

---

## 3. Modifications Frontend

### 3.1 Nouveaux fichiers à créer

| Fichier | Description | Effort |
|---------|-------------|--------|
| `src/context/CustomerQuoteContext.tsx` | Context React pour le devis courant | 1h30 |
| `src/pages/CustomerQuotes.tsx` | Liste des devis | 1h30 |
| `src/pages/CustomerQuoteDetail.tsx` | Détail d'un devis | 2h |
| `src/pages/CustomerQuoteEditor.tsx` | Éditeur de prix (marges, frais) | 2h30 |
| `src/components/customer-quote/QuoteSidebar.tsx` | Panel latéral "Devis en cours" | 2h |
| `src/components/customer-quote/QuoteItem.tsx` | Ligne de devis dans le panel | 30min |
| `src/components/customer-quote/QuoteItemEditor.tsx` | Ligne éditable (prix, marge) | 1h |
| `src/components/customer-quote/QuoteFeeRow.tsx` | Ligne de frais | 30min |
| `src/components/customer-quote/QuoteSummary.tsx` | Totaux et boutons d'action | 30min |
| `src/components/customer-quote/AddToQuoteButton.tsx` | Bouton "Ajouter au devis" | 30min |
| `src/components/customer-quote/AddFeeModal.tsx` | Modal ajout de frais | 1h |
| `src/services/customerQuoteService.ts` | Appels API pour les devis | 1h |
| `src/types/customerQuote.ts` | Types TypeScript pour les devis | 30min |

### 3.2 Fichiers à modifier

| Fichier | Modifications | Effort |
|---------|---------------|--------|
| `src/App.tsx` | Ajouter routes `/customer-quotes`, `/customer-quotes/:id` + CustomerQuoteProvider | 15min |
| `src/pages/Results.tsx` | Remplacer "Sélectionner" par "Ajouter au devis" | 30min |
| `src/components/layout/Layout.tsx` | Ajouter lien navigation "Mes Devis" | 10min |
| `src/types/index.ts` | Exporter les nouveaux types | 5min |

### 3.3 Détail du CustomerQuoteContext

```typescript
// src/context/CustomerQuoteContext.tsx

interface CustomerQuote {
  id: string;
  reference: string;
  status: 'DRAFT' | 'READY' | 'SENT' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED';
  customer_name?: string;
  customer_email?: string;
  customer_company?: string;
  transport_subtotal: number;  // Sous-total transports
  fees_total: number;          // Total frais
  total: number;               // Grand total
  total_margin: number;        // Marge totale
  currency: string;
  valid_until?: string;
  items: CustomerQuoteItem[];
  created_at: string;
}

interface CustomerQuoteItem {
  id: string;
  item_type: 'TRANSPORT' | 'FEE';
  description: string;
  partner_quote_id?: string;    // NULL pour les frais
  origin_city?: string;
  origin_country?: string;
  dest_city?: string;
  dest_country?: string;
  partner_name?: string;
  transport_mode?: string;
  delivery_time?: string;
  weight?: number;
  cost_price: number;           // 0 pour les frais
  sell_price: number;
  margin_percent?: number;
  margin_amount: number;
  position: number;
}

interface CustomerQuoteContextType {
  // État
  currentQuote: CustomerQuote | null;
  loading: boolean;

  // Actions - Lignes transport
  createQuote: () => Promise<CustomerQuote>;
  loadQuote: (id: string) => Promise<void>;
  addItem: (partnerQuoteId: string, weight: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  updateItemMargin: (itemId: string, marginPercent: number) => Promise<void>;
  updateItemPrice: (itemId: string, sellPrice: number) => Promise<void>;

  // Actions - Lignes frais
  addFee: (description: string, price: number) => Promise<void>;
  updateFee: (itemId: string, description: string, price: number) => Promise<void>;
  removeFee: (itemId: string) => Promise<void>;

  clearQuote: () => void;

  // Computed
  transportSubtotal: number;
  feesTotal: number;
  total: number;
  totalMargin: number;
  itemCount: number;

  // UI
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}
```

### 3.4 Structure des dossiers après modification

```
frontend/src/
├── App.tsx                              # Modifié
├── context/
│   └── CustomerQuoteContext.tsx         # Nouveau
├── pages/
│   ├── Dashboard.tsx
│   ├── Partners.tsx
│   ├── Quotes.tsx
│   ├── Imports.tsx
│   ├── Search.tsx
│   ├── Results.tsx                      # Modifié
│   ├── CustomerQuotes.tsx               # Nouveau
│   ├── CustomerQuoteDetail.tsx          # Nouveau
│   └── CustomerQuoteEditor.tsx          # Nouveau (éditeur prix)
├── components/
│   ├── layout/
│   │   └── Layout.tsx                   # Modifié
│   └── customer-quote/                  # Nouveau dossier
│       ├── QuoteSidebar.tsx
│       ├── QuoteItem.tsx
│       ├── QuoteItemEditor.tsx          # Ligne éditable (marge)
│       ├── QuoteFeeRow.tsx              # Ligne de frais
│       ├── QuoteSummary.tsx
│       ├── AddToQuoteButton.tsx
│       └── AddFeeModal.tsx              # Modal ajout frais
├── services/
│   ├── api.ts
│   ├── partnerService.ts
│   ├── quoteService.ts
│   ├── importService.ts
│   └── customerQuoteService.ts          # Nouveau
└── types/
    ├── index.ts                         # Modifié
    └── customerQuote.ts                 # Nouveau
```

---

## 4. Migration Base de Données

### 4.1 Nouvelles tables

```sql
-- Table customer_quotes
CREATE TABLE customer_quotes (
    id VARCHAR PRIMARY KEY,
    reference VARCHAR UNIQUE NOT NULL,
    status VARCHAR DEFAULT 'DRAFT',
    customer_name VARCHAR,
    customer_email VARCHAR,
    customer_company VARCHAR,
    subtotal DECIMAL(10,2) DEFAULT 0,
    fees DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) DEFAULT 0,
    currency VARCHAR DEFAULT 'EUR',
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    sent_at TIMESTAMP
);

CREATE INDEX ix_customer_quotes_status ON customer_quotes(status);
CREATE INDEX ix_customer_quotes_reference ON customer_quotes(reference);

-- Table customer_quote_items
CREATE TABLE customer_quote_items (
    id VARCHAR PRIMARY KEY,
    quote_id VARCHAR REFERENCES customer_quotes(id) ON DELETE CASCADE,
    partner_quote_id VARCHAR REFERENCES partner_quotes(id),
    origin_city VARCHAR,
    origin_country VARCHAR,
    dest_city VARCHAR,
    dest_country VARCHAR,
    partner_name VARCHAR,
    transport_mode VARCHAR,
    delivery_time VARCHAR,
    weight DECIMAL(10,2),
    cost_price DECIMAL(10,2),
    sell_price DECIMAL(10,2),
    margin DECIMAL(10,2),
    position INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_customer_quote_items_quote_id ON customer_quote_items(quote_id);
```

### 4.2 Impact sur les tables existantes

| Table | Impact |
|-------|--------|
| `partners` | Ajout colonne `default_margin` |
| `partner_quotes` | Aucun (référencée par FK) |
| `generated_quotes` | Aucun (peut coexister ou être remplacée) |
| `customers` | Aucun (non utilisée par customer_quotes) |

---

## 5. Décision sur `GeneratedQuote` existant

### Option A : Garder les deux modèles (Recommandé)

- `CustomerQuote` = Brouillon en construction
- `GeneratedQuote` = Devis finalisé (converti depuis CustomerQuote)

**Avantages** : Séparation claire, historique des devis finalisés

### Option B : Remplacer par CustomerQuote

- Supprimer `GeneratedQuote`
- `CustomerQuote` gère tout le cycle de vie

**Avantages** : Plus simple, moins de code

**Recommandation** : Option A pour garder un historique propre des devis envoyés.

---

## 6. Fonctionnalités hors scope (Phase 2)

Les éléments suivants ne sont pas inclus dans cette estimation :

| Fonctionnalité | Raison |
|----------------|--------|
| Génération PDF (reportlab) | Phase 5 du plan initial |
| Envoi email (aiosmtplib) | Phase 5 du plan initial |
| Authentification utilisateur | Non prévu dans le MVP |
| Multi-devise | Complexité additionnelle |
| Historique des modifications | Nice-to-have |

---

## 7. Résumé des efforts

### Backend

| Tâche | Effort estimé |
|-------|---------------|
| Modèles `CustomerQuote` + `CustomerQuoteItem` + `CustomerQuoteItemType` | 1h |
| Ajout `default_margin` sur Partner | 15min |
| Schémas Pydantic | 45min |
| Migration Alembic | 15min |
| Service `CustomerQuoteService` | 2h |
| Service `PricingService` (calcul marges) | 1h |
| API CRUD CustomerQuotes | 2h |
| API Items transport (add/remove/update margin) | 2h |
| API Fees (add/remove/update) | 1h |
| Tests unitaires | 2h |
| **Sous-total Backend** | **~12h30** |

### Frontend

| Tâche | Effort estimé |
|-------|---------------|
| Types TypeScript | 30min |
| Service `customerQuoteService.ts` | 1h |
| `CustomerQuoteContext.tsx` | 1h30 |
| `QuoteSidebar.tsx` + composants de base | 2h |
| `QuoteItemEditor.tsx` (ligne éditable marge) | 1h |
| `QuoteFeeRow.tsx` + `AddFeeModal.tsx` | 1h30 |
| Page `CustomerQuotes.tsx` (liste) | 1h30 |
| Page `CustomerQuoteDetail.tsx` | 2h |
| Page `CustomerQuoteEditor.tsx` (éditeur prix) | 2h30 |
| Modification `Results.tsx` | 30min |
| Modification `App.tsx` + Layout | 30min |
| **Sous-total Frontend** | **~14h30** |

### Total

| Phase | Effort |
|-------|--------|
| Backend | ~12h30 |
| Frontend | ~14h30 |
| **TOTAL** | **~27h** |

---

## 8. Risques identifiés

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Complexité du CustomerQuoteContext | Moyen | Bien définir les interfaces avant |
| Synchronisation panel/page | Moyen | Utiliser les events React |
| Performance avec beaucoup d'items | Faible | Pagination si > 50 items |
| Tarif supprimé après ajout au devis | Moyen | Snapshot des données dans CustomerQuoteItem |
| Calcul de marge incorrect | Moyen | Tests unitaires sur PricingService |
| UX de l'éditeur de prix complexe | Moyen | Prototypage avant implémentation |

---

## 9. Dépendances

### Avant de commencer

- [x] Modèle `PartnerQuote` fonctionnel
- [x] API `/match` fonctionnelle
- [ ] Décision sur le modèle `GeneratedQuote` (garder/remplacer)

### Packages à ajouter

**Backend** : Aucun nouveau package requis

**Frontend** : Aucun nouveau package requis (utilise React Context natif)

---

## 10. Plan d'implémentation suggéré

### Sprint 1 : Fondations Backend
1. Ajouter `default_margin` au modèle Partner
2. Créer modèles `CustomerQuote` + `CustomerQuoteItem` + `CustomerQuoteItemType`
3. Migration Alembic
4. Créer `CustomerQuoteService`
5. Créer `PricingService` (calcul marges automatique)
6. Implémenter API CRUD basique

### Sprint 2 : API Pricing & Frais
1. Implémenter API Items transport (avec marge auto)
2. Implémenter API update margin/price
3. Implémenter API Fees (add/remove/update)
4. Tests unitaires pricing

### Sprint 3 : Fondations Frontend
1. Créer types TypeScript
2. Créer `customerQuoteService.ts`
3. Créer `CustomerQuoteContext.tsx` (avec méthodes pricing)
4. Tester avec console.log

### Sprint 4 : Interface utilisateur
1. Créer `QuoteSidebar` + composants de base
2. Intégrer dans `Results.tsx`
3. Créer page `CustomerQuotes.tsx`
4. Créer page `CustomerQuoteDetail.tsx`

### Sprint 5 : Éditeur de prix
1. Créer `QuoteItemEditor.tsx` (ligne éditable marge)
2. Créer `QuoteFeeRow.tsx` + `AddFeeModal.tsx`
3. Créer page `CustomerQuoteEditor.tsx`
4. Intégration et tests

### Sprint 4 : Intégration et tests
1. Tests end-to-end du workflow
2. Corrections et polish UI
3. Documentation

---

## 11. Conclusion

L'implémentation du workflow "Panier" est **faisable** avec l'architecture actuelle.

**Points positifs** :
- Les modèles de base existent (`PartnerQuote`, `Customer`)
- L'API de matching fonctionne
- Le frontend a déjà la structure de pages

**Points d'attention** :
- Les API `generated_quotes` et `customers` sont des stubs vides
- Pas de Context React existant (à créer de zéro)
- Le bouton "Sélectionner" de Results.tsx ne fait rien actuellement

**Recommandation** : Procéder à l'implémentation en suivant le plan de sprint proposé.
