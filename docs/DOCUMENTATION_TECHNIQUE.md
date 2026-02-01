# Documentation Technique - Transport Quote

## 1. Architecture générale

### 1.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TRANSPORT QUOTE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐       │
│    │   FRONTEND   │         │   BACKEND    │         │   DATABASE   │       │
│    │              │  HTTP   │              │   SQL   │              │       │
│    │  React 19    │◀───────▶│  FastAPI     │◀───────▶│  PostgreSQL  │       │
│    │  TypeScript  │   REST  │  Python 3.11 │         │  16          │       │
│    │  Vite        │         │  SQLAlchemy  │         │              │       │
│    │  Port: 8080  │         │  Port: 3000  │         │  Port: 5432  │       │
│    └──────────────┘         └──────────────┘         └──────────────┘       │
│                                    │                                         │
│                                    ▼                                         │
│                             ┌──────────────┐                                │
│                             │    REDIS     │                                │
│                             │    Cache     │                                │
│                             │  Port: 6379  │                                │
│                             └──────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Frontend | React | 19.x |
| Build tool | Vite | 6.x |
| Styling | Tailwind CSS | 4.x |
| Routing | React Router | 7.x |
| HTTP Client | Axios | 1.x |
| Icons | Lucide React | - |
| Backend | FastAPI | 0.115.x |
| ORM | SQLAlchemy | 2.x |
| Validation | Pydantic | 2.x |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Containerisation | Docker Compose | 3.8 |

### 1.3 Structure des dossiers

```
transport_quote/
├── backend/
│   ├── app/
│   │   ├── api/                    # Routes API (endpoints)
│   │   │   ├── partners.py
│   │   │   ├── quotes.py
│   │   │   ├── imports.py
│   │   │   ├── matching.py
│   │   │   ├── customer_quotes.py
│   │   │   └── cities.py
│   │   ├── core/                   # Configuration
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/                 # Modèles SQLAlchemy
│   │   │   ├── partner.py
│   │   │   ├── partner_quote.py
│   │   │   ├── customer_quote.py
│   │   │   ├── customer.py
│   │   │   ├── import_job.py
│   │   │   └── generated_quote.py
│   │   ├── schemas/                # Schémas Pydantic
│   │   │   ├── partner.py
│   │   │   ├── partner_quote.py
│   │   │   ├── customer_quote.py
│   │   │   └── import_job.py
│   │   ├── services/               # Logique métier
│   │   │   ├── partner_service.py
│   │   │   ├── quote_service.py
│   │   │   ├── matching_service.py
│   │   │   ├── customer_quote_service.py
│   │   │   ├── pricing_service.py
│   │   │   ├── import_service.py
│   │   │   ├── import_logic/       # Logique d'import
│   │   │   │   ├── column_mapper.py
│   │   │   │   ├── data_normalizer.py
│   │   │   │   └── row_validator.py
│   │   │   └── parsers/            # Parseurs de fichiers
│   │   │       ├── csv_parser.py
│   │   │       ├── excel_parser.py
│   │   │       └── pdf_parser.py
│   │   └── main.py                 # Point d'entrée FastAPI
│   ├── configs/
│   │   └── partner_mapping.yaml    # Configuration des imports
│   ├── alembic/                    # Migrations DB
│   │   └── versions/
│   ├── uploads/                    # Fichiers uploadés
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Composants de pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Partners.tsx
│   │   │   ├── Quotes.tsx
│   │   │   ├── Imports.tsx
│   │   │   ├── Search.tsx
│   │   │   ├── Results.tsx
│   │   │   ├── CustomerQuotes.tsx
│   │   │   ├── CustomerQuoteDetail.tsx
│   │   │   └── CustomerQuoteEditor.tsx
│   │   ├── components/             # Composants réutilisables
│   │   │   ├── layout/
│   │   │   │   ├── Layout.tsx
│   │   │   │   └── Sidebar.tsx
│   │   │   ├── ui/
│   │   │   │   └── CityAutocomplete.tsx
│   │   │   └── customer-quote/
│   │   │       ├── QuoteSidebar.tsx
│   │   │       ├── QuoteItemEditor.tsx
│   │   │       ├── EditCustomerModal.tsx
│   │   │       ├── AddFeeModal.tsx
│   │   │       └── SearchModal.tsx
│   │   ├── services/               # Clients API
│   │   │   ├── api.ts
│   │   │   ├── partnerService.ts
│   │   │   ├── quoteService.ts
│   │   │   ├── customerQuoteService.ts
│   │   │   ├── importService.ts
│   │   │   └── cityService.ts
│   │   ├── context/                # State management
│   │   │   └── CustomerQuoteContext.tsx
│   │   ├── types/                  # TypeScript types
│   │   │   └── index.ts
│   │   ├── App.tsx                 # Router
│   │   └── main.tsx                # Entry point
│   ├── package.json
│   └── Dockerfile
├── docs/                           # Documentation
├── file_import/                    # Fichiers d'exemple
├── docker-compose.yml
├── start.sh
├── stop.sh
└── restart.sh
```

---

## 2. Backend

### 2.1 Configuration

#### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| DATABASE_URL | URL PostgreSQL | postgresql://... |
| REDIS_URL | URL Redis | redis://redis:6379/0 |
| UPLOAD_DIR | Dossier uploads | uploads |
| MAX_UPLOAD_SIZE | Taille max fichier | 52428800 (50MB) |

#### Fichier `app/core/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/transport_quote"
    REDIS_URL: str = "redis://localhost:6379/0"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024

settings = Settings()
```

#### Connection Pool

```python
# app/core/database.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### 2.2 Modèles de données

#### Diagramme Entité-Relation

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│  Customer   │       │  CustomerQuote  │       │CustomerQuote│
│             │1     n│                 │1     n│    Item     │
│ id          │───────│ id              │───────│ id          │
│ email       │       │ reference       │       │ type        │
│ company     │       │ status          │       │ description │
│ name        │       │ customer_id     │       │ cost_price  │
│ phone       │       │ customer_name   │       │ sell_price  │
└─────────────┘       │ total           │       │ margin_%    │
                      │ total_margin    │       │ quote_id    │
                      └─────────────────┘       │ partner_    │
                                                │  quote_id   │
┌─────────────┐       ┌─────────────────┐       └──────┬──────┘
│  Partner    │       │  PartnerQuote   │              │
│             │1     n│                 │◀─────────────┘
│ id          │───────│ id              │
│ code        │       │ partner_id      │
│ name        │       │ transport_mode  │
│ email       │       │ origin_city     │
│ rating      │       │ origin_country  │
│ is_active   │       │ dest_city       │
│ default_    │       │ dest_country    │
│  margin     │       │ dest_postal_code│
└──────┬──────┘       │ weight_min/max  │
       │              │ cost            │
       │              │ pricing_type    │
       │              │ currency        │
       │         n    │ delivery_time   │
       └──────────────│ import_job_id   │
                      └─────────────────┘
                              │
                              │ n
                      ┌───────┴───────┐
                      │   ImportJob   │
                      │               │
                      │ id            │
                      │ partner_id    │
                      │ filename      │
                      │ status        │
                      │ total_rows    │
                      │ success_count │
                      │ error_count   │
                      │ errors (JSON) │
                      └───────────────┘
```

#### Modèle Partner

```python
# app/models/partner.py
class Partner(Base):
    __tablename__ = "partners"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    rating = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    default_margin = Column(Numeric(5, 2), default=20.00)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    quotes = relationship("PartnerQuote", back_populates="partner")
    import_jobs = relationship("ImportJob", back_populates="partner")
```

#### Modèle PartnerQuote

```python
# app/models/partner_quote.py
class TransportMode(str, Enum):
    ROAD = "ROAD"
    RAIL = "RAIL"
    SEA = "SEA"
    AIR = "AIR"
    MULTIMODAL = "MULTIMODAL"

class PricingType(str, Enum):
    PER_100KG = "PER_100KG"
    PER_KG = "PER_KG"
    LUMPSUM = "LUMPSUM"
    PER_PALLET = "PER_PALLET"

class PartnerQuote(Base):
    __tablename__ = "partner_quotes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    partner_id = Column(String, ForeignKey("partners.id"), nullable=False)

    # Route
    transport_mode = Column(Enum(TransportMode), nullable=False)
    origin_city = Column(String, nullable=False)
    origin_country = Column(String(2), nullable=False)
    origin_postal_code = Column(String, nullable=True)
    dest_city = Column(String, nullable=False)
    dest_country = Column(String(2), nullable=False)
    dest_postal_code = Column(String, nullable=True)

    # Poids/Volume
    weight_min = Column(Float, nullable=True)
    weight_max = Column(Float, nullable=True)
    volume_min = Column(Float, nullable=True)
    volume_max = Column(Float, nullable=True)

    # Tarification
    cost = Column(Numeric(10, 2), nullable=False)
    pricing_type = Column(String, default="PER_100KG")
    currency = Column(String(3), default="EUR")

    # Métadonnées
    delivery_time = Column(String, nullable=True)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    import_job_id = Column(String, ForeignKey("import_jobs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Index composites
    __table_args__ = (
        Index('ix_partner_quotes_countries', 'origin_country', 'dest_country'),
        Index('ix_partner_quotes_active', 'is_active', 'valid_until'),
    )
```

#### Modèle CustomerQuote

```python
# app/models/customer_quote.py
class QuoteStatus(str, Enum):
    DRAFT = "DRAFT"
    READY = "READY"
    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class ItemType(str, Enum):
    TRANSPORT = "TRANSPORT"
    FEE = "FEE"

class CustomerQuote(Base):
    __tablename__ = "customer_quotes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reference = Column(String, unique=True, nullable=False)
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)

    # Client
    customer_id = Column(String, ForeignKey("customers.id"), nullable=True)
    customer_name = Column(String, nullable=True)
    customer_company = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)
    customer_phone = Column(String, nullable=True)

    # Totaux
    transport_subtotal = Column(Numeric(10, 2), default=0)
    fees_total = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), default=0)
    total_margin = Column(Numeric(10, 2), default=0)

    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(Date, nullable=True)

    # Relations
    items = relationship("CustomerQuoteItem", back_populates="quote",
                        order_by="CustomerQuoteItem.position")

class CustomerQuoteItem(Base):
    __tablename__ = "customer_quote_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quote_id = Column(String, ForeignKey("customer_quotes.id"), nullable=False)
    type = Column(Enum(ItemType), nullable=False)
    position = Column(Integer, default=0)
    description = Column(String, nullable=True)

    # Pricing
    cost_price = Column(Numeric(10, 2), nullable=False)
    sell_price = Column(Numeric(10, 2), nullable=False)
    margin_percent = Column(Numeric(5, 2), nullable=False)
    margin_amount = Column(Numeric(10, 2), nullable=False)

    # Snapshot (pour TRANSPORT)
    partner_quote_id = Column(String, ForeignKey("partner_quotes.id"), nullable=True)
    snapshot_transport_mode = Column(String, nullable=True)
    snapshot_origin = Column(String, nullable=True)
    snapshot_destination = Column(String, nullable=True)
    snapshot_delivery_time = Column(String, nullable=True)
    snapshot_weight = Column(Float, nullable=True)
```

### 2.3 API Endpoints

#### Routes Partenaires

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/partners/` | Créer un partenaire |
| GET | `/api/v1/partners/` | Lister les partenaires |
| GET | `/api/v1/partners/{id}` | Détail d'un partenaire |
| PUT | `/api/v1/partners/{id}` | Modifier un partenaire |
| DELETE | `/api/v1/partners/{id}` | Supprimer un partenaire |
| DELETE | `/api/v1/partners/{id}/quotes` | Supprimer tous les tarifs |

#### Routes Tarifs

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/quotes/` | Créer un tarif |
| GET | `/api/v1/quotes/` | Lister les tarifs |
| GET | `/api/v1/quotes/count` | Nombre total de tarifs |
| GET | `/api/v1/quotes/{id}` | Détail d'un tarif |
| DELETE | `/api/v1/quotes/{id}` | Supprimer un tarif |

#### Routes Import

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/imports/` | Lancer un import |
| GET | `/api/v1/imports/{id}` | Statut d'un import |

#### Routes Matching

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/match/` | Rechercher des tarifs |

**Payload de recherche :**
```json
{
  "origin_country": "FR",
  "origin_postal_code": "75",
  "dest_country": "FR",
  "dest_postal_code": "69",
  "weight": 500,
  "transport_mode": "ROAD",
  "shipping_date": "2024-01-15"
}
```

#### Routes Devis Clients

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/v1/customer-quotes/` | Créer un devis |
| GET | `/api/v1/customer-quotes/` | Lister les devis |
| GET | `/api/v1/customer-quotes/{id}` | Détail d'un devis |
| PUT | `/api/v1/customer-quotes/{id}` | Modifier un devis |
| DELETE | `/api/v1/customer-quotes/{id}` | Supprimer un devis |
| POST | `/api/v1/customer-quotes/{id}/items` | Ajouter ligne transport |
| POST | `/api/v1/customer-quotes/{id}/fees` | Ajouter frais |
| PUT | `/api/v1/customer-quotes/{id}/items/{item_id}` | Modifier ligne |
| DELETE | `/api/v1/customer-quotes/{id}/items/{item_id}` | Supprimer ligne |

### 2.4 Services métier

#### MatchingService

```python
# app/services/matching_service.py
class MatchingService:
    @staticmethod
    def find_quotes(db: Session, criteria: SearchCriteria) -> List[PartnerQuote]:
        query = db.query(PartnerQuote).join(Partner)

        # Filtres obligatoires
        query = query.filter(Partner.is_active == True)

        # Mode transport
        if criteria.transport_mode:
            query = query.filter(PartnerQuote.transport_mode == criteria.transport_mode)

        # Pays
        query = query.filter(
            func.upper(PartnerQuote.origin_country) == criteria.origin_country.upper(),
            func.upper(PartnerQuote.dest_country) == criteria.dest_country.upper()
        )

        # Code postal (préfixe 2 caractères)
        if criteria.dest_postal_code:
            prefix = criteria.dest_postal_code[:2]
            query = query.filter(
                PartnerQuote.dest_postal_code.like(f"{prefix}%")
            )

        # Poids
        if criteria.weight:
            query = query.filter(
                or_(PartnerQuote.weight_min.is_(None),
                    PartnerQuote.weight_min <= criteria.weight),
                or_(PartnerQuote.weight_max.is_(None),
                    PartnerQuote.weight_max >= criteria.weight)
            )

        # Validité
        today = date.today()
        query = query.filter(
            or_(PartnerQuote.valid_from.is_(None),
                PartnerQuote.valid_from <= today),
            or_(PartnerQuote.valid_until.is_(None),
                PartnerQuote.valid_until >= today)
        )

        results = query.all()

        # Calcul du prix
        for quote in results:
            quote.cost = MatchingService._calculate_price(
                quote, criteria.weight
            )

        return sorted(results, key=lambda q: float(q.cost))

    @staticmethod
    def _calculate_price(quote: PartnerQuote, weight: float) -> Decimal:
        cost = Decimal(str(quote.cost))

        if quote.pricing_type == "PER_100KG":
            # Arrondi au 100 kg supérieur
            rounded = math.ceil(weight / 100) * 100
            return cost * (rounded / 100)
        elif quote.pricing_type == "PER_KG":
            return cost * Decimal(str(weight))
        else:  # LUMPSUM
            return cost
```

#### CustomerQuoteService

```python
# app/services/customer_quote_service.py
class CustomerQuoteService:
    @staticmethod
    def create_quote(db: Session) -> CustomerQuote:
        # Génération référence: DEV-YYYY-XXXX
        year = datetime.now().year
        count = db.query(CustomerQuote).filter(
            CustomerQuote.reference.like(f"DEV-{year}-%")
        ).count()
        reference = f"DEV-{year}-{str(count + 1).zfill(4)}"

        quote = CustomerQuote(reference=reference)
        db.add(quote)
        db.commit()
        return quote

    @staticmethod
    def add_transport_item(
        db: Session,
        quote_id: str,
        partner_quote_id: str,
        weight: float
    ) -> CustomerQuoteItem:
        quote = db.query(CustomerQuote).get(quote_id)
        partner_quote = db.query(PartnerQuote).get(partner_quote_id)
        partner = partner_quote.partner

        # Calcul du prix d'achat
        cost_price = MatchingService._calculate_price(partner_quote, weight)

        # Application de la marge par défaut
        margin_percent = partner.default_margin or Decimal("20.00")
        sell_price = PricingService.calculate_sell_price(cost_price, margin_percent)
        margin_amount = PricingService.calculate_margin_amount(cost_price, sell_price)

        # Création de la ligne avec snapshot
        item = CustomerQuoteItem(
            quote_id=quote_id,
            type=ItemType.TRANSPORT,
            partner_quote_id=partner_quote_id,
            cost_price=cost_price,
            sell_price=sell_price,
            margin_percent=margin_percent,
            margin_amount=margin_amount,
            position=len(quote.items),
            description=f"{partner.name} - {partner_quote.transport_mode}",
            snapshot_transport_mode=partner_quote.transport_mode,
            snapshot_origin=f"{partner_quote.origin_city}, {partner_quote.origin_country}",
            snapshot_destination=f"{partner_quote.dest_city} ({partner_quote.dest_postal_code})",
            snapshot_delivery_time=partner_quote.delivery_time,
            snapshot_weight=weight
        )

        db.add(item)
        CustomerQuoteService._recalculate_totals(db, quote)
        db.commit()
        return item

    @staticmethod
    def _recalculate_totals(db: Session, quote: CustomerQuote):
        transport_total = Decimal("0")
        fees_total = Decimal("0")
        margin_total = Decimal("0")

        for item in quote.items:
            if item.type == ItemType.TRANSPORT:
                transport_total += item.sell_price
            else:
                fees_total += item.sell_price
            margin_total += item.margin_amount

        quote.transport_subtotal = transport_total
        quote.fees_total = fees_total
        quote.total = transport_total + fees_total
        quote.total_margin = margin_total
```

#### PricingService

```python
# app/services/pricing_service.py
from decimal import Decimal, ROUND_HALF_UP

class PricingService:
    @staticmethod
    def calculate_sell_price(cost: Decimal, margin_percent: Decimal) -> Decimal:
        """Prix de vente = Coût × (1 + marge/100)"""
        multiplier = Decimal("1") + (margin_percent / Decimal("100"))
        return (cost * multiplier).quantize(Decimal("0.01"), ROUND_HALF_UP)

    @staticmethod
    def calculate_margin_percent(cost: Decimal, sell: Decimal) -> Decimal:
        """Marge % = ((Vente/Coût) - 1) × 100"""
        if cost == 0:
            return Decimal("100.00")
        ratio = sell / cost
        return ((ratio - Decimal("1")) * Decimal("100")).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

    @staticmethod
    def calculate_margin_amount(cost: Decimal, sell: Decimal) -> Decimal:
        """Montant marge = Vente - Coût"""
        return (sell - cost).quantize(Decimal("0.01"), ROUND_HALF_UP)
```

### 2.5 Pipeline d'import

#### Architecture du pipeline

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  ImportJob  │────▶│   Parser    │────▶│ColumnMapper │────▶│DataNormalizer│
│  (PENDING)  │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
┌─────────────┐     ┌─────────────┐     ┌─────────────┐            │
│  ImportJob  │◀────│   Persist   │◀────│RowValidator │◀───────────┘
│ (COMPLETED) │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
```

#### ColumnMapper - Layouts supportés

**1. FLAT (par défaut)**
```python
# Une ligne Excel = une ligne DB
row = {"ville_depart": "Paris", "prix": 15.00}
→ [{"origin_city": "Paris", "cost": 15.00}]
```

**2. GRID (matrice)**
```python
# Une ligne Excel = N lignes DB (pivot sur colonnes poids)
row = {"Agence": "NIC", "5 KG": 8.50, "10 KG": 12.00}
→ [
    {"origin_city": "NIC", "weight_max": 5, "cost": 8.50},
    {"origin_city": "NIC", "weight_max": 10, "cost": 12.00}
]
```

**3. DUAL_GRID (double matrice)**
```python
# Deux sections: small_weights + large_weights
row = {"Dept": "06", "Minimum": 9.4, "1001/1500 kg": 4.95}
→ [
    {"dest_postal_code": "06", "weight_min": 0, "weight_max": 99,
     "cost": 9.4, "pricing_type": "PER_100KG"},
    {"dest_postal_code": "06", "weight_min": 1001, "weight_max": 1500,
     "cost": 4.95, "pricing_type": "LUMPSUM"}
]
```

#### Configuration YAML

```yaml
# backend/configs/partner_mapping.yaml

# Aliases par défaut (FR/EN)
default:
  columns:
    transport_mode: ["mode", "transport", "type"]
    origin_city: ["ville_depart", "origin_city", "depart"]
    origin_country: ["pays_depart", "origin_country", "pays"]
    dest_city: ["ville_arrivee", "dest_city", "arrivee"]
    dest_country: ["pays_arrivee", "dest_country"]
    cost: ["prix", "price", "tarif", "cost"]
    weight_min: ["poids_min", "weight_min"]
    weight_max: ["poids_max", "weight_max"]

# Configuration partenaire spécifique
partners:
  BESSON:
    layout: "grid"
    header_row: 0
    sheet_name: "Tarifs"
    columns:
      origin_city: "Agence"
      dest_postal_code: "Département"
    defaults:
      transport_mode: "ROAD"
      origin_country: "FR"
      dest_country: "FR"
      currency: "EUR"
    grid:
      pivot_axis: "weight"
      value_column: "cost"
      header_regex: "^(\\d+)[_\\s]*(KG|kg)"
      weight_min_gap: 1

  BIANCHI:
    layout: "dual_grid"
    header_row: 6
    sheet_name: "PROTOCOLE DISTRIBUTION FRANCE"
    columns:
      dest_postal_code: "zip_code"
    defaults:
      transport_mode: "ROAD"
      origin_city: "NICE"
      dest_city: "ALL"
    transforms:
      dest_postal_code:
        "20 (1)": "2A"
        "20 (2)": "2B"
      pricing_type:
        "PRICE PER 100KGS": "PER_100KG"
        "LUMPSUM FROM NICE": "LUMPSUM"
    dual_grid:
      small_weights:
        columns:
          "Minimum": { weight_min: 0, weight_max: 99 }
          "100/300 kg": { weight_min: 100, weight_max: 300 }
        pricing_col: "pricing_type_small"
      large_weights:
        columns:
          "1001/1500 kg": { weight_min: 1001, weight_max: 1500 }
        pricing_col: "pricing_type_large"
```

---

## 3. Frontend

### 3.1 State Management

#### CustomerQuoteContext

```typescript
// src/context/CustomerQuoteContext.tsx
interface CustomerQuoteContextType {
  // State
  currentQuote: CustomerQuote | null;
  isLoading: boolean;
  searchMode: 'consultation' | 'quote';
  isSidebarOpen: boolean;

  // Actions - Quote lifecycle
  createQuote: () => Promise<void>;
  loadQuote: (id: string) => Promise<void>;
  updateQuote: (data: Partial<CustomerQuote>) => Promise<void>;
  deleteQuote: () => Promise<void>;
  clearQuote: () => void;

  // Actions - Items
  addItem: (partnerQuoteId: string, weight: number) => Promise<void>;
  addFee: (description: string, price: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  updateItem: (itemId: string, data: UpdateItemData) => Promise<void>;

  // Actions - UI
  openSidebar: () => void;
  closeSidebar: () => void;
  setSearchMode: (mode: 'consultation' | 'quote') => void;
  openSearchForQuote: () => void;
  openSearchForConsultation: () => void;

  // Computed
  subtotal: number;
  totalFees: number;
  totalMargin: number;
  grandTotal: number;
}
```

#### Persistance localStorage

```typescript
// Stockage de l'ID du devis en cours
const STORAGE_KEY = 'transport_quote_current_quote_id';

// Au chargement
useEffect(() => {
  const savedId = localStorage.getItem(STORAGE_KEY);
  if (savedId) loadQuote(savedId);
}, []);

// À chaque changement
useEffect(() => {
  if (currentQuote?.id) {
    localStorage.setItem(STORAGE_KEY, currentQuote.id);
  }
}, [currentQuote?.id]);
```

### 3.2 Services API

#### Configuration Axios

```typescript
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:3000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
```

#### CustomerQuoteService

```typescript
// src/services/customerQuoteService.ts
export const CustomerQuoteService = {
  create: () => api.post('/customer-quotes/'),

  getAll: () => api.get('/customer-quotes/'),

  getById: (id: string) => api.get(`/customer-quotes/${id}`),

  update: (id: string, data: Partial<CustomerQuote>) =>
    api.put(`/customer-quotes/${id}`, data),

  delete: (id: string) => api.delete(`/customer-quotes/${id}`),

  addTransportItem: (quoteId: string, partnerQuoteId: string, weight: number) =>
    api.post(`/customer-quotes/${quoteId}/items`, {
      partner_quote_id: partnerQuoteId,
      weight,
    }),

  addFeeItem: (quoteId: string, description: string, price: number) =>
    api.post(`/customer-quotes/${quoteId}/fees`, {
      description,
      sell_price: price,
    }),

  updateItem: (quoteId: string, itemId: string, data: UpdateItemData) =>
    api.put(`/customer-quotes/${quoteId}/items/${itemId}`, data),

  removeItem: (quoteId: string, itemId: string) =>
    api.delete(`/customer-quotes/${quoteId}/items/${itemId}`),
};
```

### 3.3 Routing

```typescript
// src/App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <CustomerQuoteProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="partners" element={<Partners />} />
            <Route path="quotes" element={<Quotes />} />
            <Route path="imports" element={<Imports />} />
            <Route path="search" element={<Search />} />
            <Route path="results" element={<Results />} />
            <Route path="customer-quotes" element={<CustomerQuotes />} />
            <Route path="customer-quotes/:id" element={<CustomerQuoteDetail />} />
            <Route path="customer-quotes/:id/edit" element={<CustomerQuoteEditor />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </CustomerQuoteProvider>
  );
}
```

### 3.4 Types TypeScript

```typescript
// src/types/index.ts

export interface Partner {
  id: string;
  code: string;
  name: string;
  email: string;
  rating: number;
  is_active: boolean;
  default_margin?: number;
  created_at: string;
}

export interface Quote {
  id: string;
  partner_id: string;
  transport_mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA';
  origin_city: string;
  origin_country: string;
  origin_postal_code?: string;
  dest_city: string;
  dest_country: string;
  dest_postal_code?: string;
  weight_min: number;
  weight_max: number;
  cost: string | number;
  pricing_type?: string;
  currency: string;
  delivery_time: string | null;
  valid_until: string | null;
  partner: Partner;
}

export interface CustomerQuote {
  id: string;
  reference: string;
  status: 'DRAFT' | 'READY' | 'SENT' | 'ACCEPTED' | 'REJECTED' | 'EXPIRED';
  customer_name?: string;
  customer_company?: string;
  customer_email?: string;
  customer_phone?: string;
  transport_subtotal: number;
  fees_total: number;
  total: number;
  total_margin: number;
  items: CustomerQuoteItem[];
  created_at: string;
  valid_until?: string;
}

export interface CustomerQuoteItem {
  id: string;
  type: 'TRANSPORT' | 'FEE';
  description?: string;
  position: number;
  cost_price: number;
  sell_price: number;
  margin_percent: number;
  margin_amount: number;
  partner_quote_id?: string;
  snapshot_transport_mode?: string;
  snapshot_origin?: string;
  snapshot_destination?: string;
  snapshot_delivery_time?: string;
  snapshot_weight?: number;
}

export interface SearchCriteria {
  origin_country: string;
  origin_postal_code?: string;
  origin_city?: string;
  dest_country: string;
  dest_postal_code?: string;
  dest_city?: string;
  weight: number;
  volume?: number;
  transport_mode?: 'ROAD' | 'RAIL' | 'AIR' | 'SEA';
  shipping_date?: string;
}
```

---

## 4. Infrastructure

### 4.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: transport_user
      POSTGRES_PASSWORD: transport_pass
      POSTGRES_DB: transport_quote
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U transport_user -d transport_quote"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://transport_user:transport_pass@postgres:5432/transport_quote
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend/uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### 4.2 Dockerfiles

**Backend**
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
```

**Frontend**
```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
```

### 4.3 Scripts de démarrage

```bash
# start.sh
#!/bin/bash
docker-compose up -d --build

# stop.sh
#!/bin/bash
docker-compose down

# restart.sh
#!/bin/bash
docker-compose down
docker-compose up -d --build
```

---

## 5. Base de données

### 5.1 Migrations Alembic

```bash
# Créer une migration
alembic revision --autogenerate -m "description"

# Appliquer les migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### 5.2 Index et performances

```sql
-- Index pour la recherche de tarifs
CREATE INDEX ix_partner_quotes_countries
ON partner_quotes (origin_country, dest_country);

CREATE INDEX ix_partner_quotes_postal
ON partner_quotes (dest_postal_code);

CREATE INDEX ix_partner_quotes_weight
ON partner_quotes (weight_min, weight_max);

CREATE INDEX ix_partner_quotes_active
ON partner_quotes (valid_from, valid_until)
WHERE valid_until IS NULL OR valid_until >= CURRENT_DATE;
```

---

## 6. Sécurité (MVP)

### 6.1 État actuel

| Aspect | Statut | Note |
|--------|--------|------|
| Authentification | Non implémenté | MVP sans auth |
| Autorisation | Non implémenté | MVP sans rôles |
| CORS | Ouvert (all origins) | À restreindre |
| Upload files | Limité à 50MB | OK |
| SQL Injection | Protégé (SQLAlchemy) | OK |
| XSS | React escape par défaut | OK |

### 6.2 Recommandations production

1. Ajouter authentification JWT
2. Restreindre CORS aux domaines autorisés
3. Ajouter rate limiting
4. Configurer HTTPS
5. Valider les types MIME des uploads
6. Nettoyer les fichiers uploadés après traitement

---

## 7. Évolutions futures

### 7.1 Roadmap technique

| Phase | Fonctionnalité | Composants |
|-------|----------------|------------|
| 1 | Génération PDF | WeasyPrint, templates |
| 2 | Authentification | JWT, refresh tokens |
| 3 | Notifications | WebSocket, email |
| 4 | Historique | Audit trail, versioning |
| 5 | Analytics | Tableau de bord avancé |

### 7.2 Améliorations architecture

- Cache Redis pour les recherches fréquentes
- Queue de tâches (Celery) pour les imports lourds
- API GraphQL en complément REST
- Tests E2E (Playwright/Cypress)
