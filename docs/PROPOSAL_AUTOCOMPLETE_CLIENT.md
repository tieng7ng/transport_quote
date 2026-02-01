# Proposition : Autocomplete Client depuis la table Partners

## Contexte

Optimiser la saisie des informations client dans les devis pour :
- Réduire les erreurs de saisie
- Gagner en efficacité
- Assurer la cohérence des données

---

## 1. Analyse de l'existant

### 1.1 Situation actuelle

Actuellement, dans `CustomerQuoteEditor.tsx`, les informations client sont saisies manuellement :
- `customer_name` : Nom du contact (texte libre)
- `customer_company` : Société (texte libre)
- `customer_email` : Email (texte libre)
- `valid_until` : Date de validité

**Problèmes identifiés :**
| Problème | Impact |
|----------|--------|
| Saisie libre | Risque de fautes de frappe |
| Pas de validation | Données incohérentes |
| Ressaisie à chaque devis | Perte de temps |
| Pas de lien avec les partenaires | Données dupliquées |

### 1.2 Table Partners existante

```python
class Partner(Base):
    __tablename__ = "partners"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)        # Nom du partenaire
    code = Column(String, unique=True)           # Code unique
    is_active = Column(Boolean, default=True)
    # ... autres champs existants
```

**Question clé :** Les "Partners" actuels sont des **transporteurs** (fournisseurs de tarifs).
Pour les **clients**, il faut soit :
- A) Créer une nouvelle table `Customers`
- B) Étendre la table `Partners` avec un champ `type` (SUPPLIER/CUSTOMER)
- C) Utiliser la même table Partners pour les deux usages

---

## 2. Propositions d'architecture

### Option A : Nouvelle table `Customers` (Recommandée)

Créer une table dédiée aux clients avec tous les champs nécessaires.

```python
class Customer(Base):
    """Client pour les devis"""
    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))

    # Identifiants
    code = Column(String, unique=True)           # Code client (ex: CLI-001)
    siret = Column(String(14), unique=True, nullable=True)

    # Société
    company_name = Column(String, nullable=False)  # Raison sociale
    trade_name = Column(String, nullable=True)     # Nom commercial

    # Contact principal
    contact_name = Column(String, nullable=True)   # Nom du contact
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)

    # Adresse
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, default="FR")

    # Conditions commerciales
    payment_terms = Column(Integer, default=30)    # Délai de paiement (jours)
    default_margin = Column(Numeric(5, 2), default=15.00)  # Marge par défaut

    # Métadonnées
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relations
    quotes = relationship("CustomerQuote", back_populates="customer")
```

**Avantages :**
- Séparation claire des responsabilités (transporteurs vs clients)
- Champs spécifiques aux clients (SIRET, conditions de paiement)
- Évolutivité (CRM, facturation, etc.)

**Inconvénients :**
- Nouvelle table à maintenir
- Migration des données existantes

---

### Option B : Extension de la table Partners

Ajouter un champ `partner_type` à la table existante.

```python
class PartnerType(str, Enum):
    SUPPLIER = "SUPPLIER"   # Transporteur
    CUSTOMER = "CUSTOMER"   # Client

class Partner(Base):
    # ... champs existants ...
    partner_type = Column(Enum(PartnerType), default=PartnerType.SUPPLIER)

    # Nouveaux champs pour les clients
    siret = Column(String(14), nullable=True)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    # ...
```

**Avantages :**
- Pas de nouvelle table
- Réutilisation du code existant

**Inconvénients :**
- Mélange des concepts (transporteurs et clients)
- Champs non pertinents selon le type
- Complexification des requêtes

---

### Option C : Clients optionnels (Mode mixte)

Permettre la saisie libre OU la sélection d'un client existant.

**Avantages :**
- Flexibilité maximale
- Transition en douceur

**Inconvénients :**
- Ne répond pas au besoin de validation stricte
- Données potentiellement incohérentes

---

## 3. Recommandation : Option A avec validation

### 3.1 Schéma de données proposé

```
┌─────────────────┐       ┌───────────────────────┐       ┌─────────────────┐
│    Customer     │       │    CustomerQuote      │       │ CustomerQuoteItem│
├─────────────────┤       ├───────────────────────┤       ├─────────────────┤
│ id          PK  │──────>│ id               PK   │──────>│ id          PK  │
│ code            │       │ customer_id      FK   │       │ quote_id    FK  │
│ siret           │       │ reference            │       │ ...             │
│ company_name    │       │ status               │       └─────────────────┘
│ trade_name      │       │ total                │
│ contact_name    │       │ valid_until          │
│ contact_email   │       │ created_at           │
│ contact_phone   │       └───────────────────────┘
│ address_line1   │
│ postal_code     │
│ city            │
│ country         │
│ payment_terms   │
│ default_margin  │
│ is_active       │
└─────────────────┘
```

### 3.2 Modification du modèle CustomerQuote

```python
class CustomerQuote(Base):
    # ... champs existants ...

    # Nouveau : Lien vers Customer (obligatoire)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)

    # Champs dénormalisés (snapshot au moment de la création)
    customer_name = Column(String)        # Copie de customer.contact_name
    customer_company = Column(String)     # Copie de customer.company_name
    customer_email = Column(String)       # Copie de customer.contact_email

    # Relation
    customer = relationship("Customer", back_populates="quotes")
```

**Note :** Les champs `customer_name`, `customer_company`, `customer_email` sont conservés comme "snapshot" pour garder l'historique même si le client est modifié ultérieurement.

---

## 4. Interface utilisateur proposée

### 4.1 Composant d'autocomplete client

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  👤 Informations Client                                        [✏️ Modifier]│
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  Rechercher un client * :                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🔍 Tapez un nom, email ou SIRET...                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  📍 SARL ABC (CLI-001)                                              │   │
│  │     Contact: Jean Dupont | contact@abc.fr                           │   │
│  │     SIRET: 123 456 789 00012                                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  📍 ABC Transport (CLI-042)                              ◀── Actif  │   │
│  │     Contact: Marie Martin | info@abc-transport.fr                   │   │
│  │     SIRET: 987 654 321 00034                                        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  ➕ Créer un nouveau client "ABC"                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Après sélection d'un client

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  👤 Informations Client                              [🔄 Changer] [✏️ Éditer]│
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────┐                                                            │   │
│  │  │ ABC │  SARL ABC                                      CLI-001     │   │
│  │  └─────┘  Jean Dupont                                               │   │
│  │                                                                     │   │
│  │  📧 contact@abc.fr                                                  │   │
│  │  📞 01 23 45 67 89                                                  │   │
│  │  📍 123 rue de Paris, 75001 Paris, France                           │   │
│  │                                                                     │   │
│  │  💳 Paiement : 30 jours | Marge par défaut : 15%                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Date de validité du devis :                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 28/02/2026                                                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 État d'erreur (client obligatoire)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  👤 Informations Client                                        [✏️ Modifier]│
│  ───────────────────────────────────────────────────────────────────────    │
│                                                                             │
│  Rechercher un client * :                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 🔍 XYZ Corp                                                     ⚠️  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│  ⚠️ Aucun client trouvé pour "XYZ Corp". Veuillez sélectionner un client   │
│     existant ou créer un nouveau client.                                    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ➕ Créer le client "XYZ Corp"                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Modal création de client

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Créer un nouveau client                                              [X]   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INFORMATIONS SOCIÉTÉ                                                       │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Raison sociale *           Nom commercial                                  │
│  ┌───────────────────────┐  ┌───────────────────────┐                      │
│  │ SARL ABC              │  │ ABC Logistique        │                      │
│  └───────────────────────┘  └───────────────────────┘                      │
│                                                                             │
│  SIRET                      Code client                                     │
│  ┌───────────────────────┐  ┌───────────────────────┐                      │
│  │ 123 456 789 00012     │  │ CLI-XXX (auto)        │                      │
│  └───────────────────────┘  └───────────────────────┘                      │
│                                                                             │
│  CONTACT PRINCIPAL                                                          │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Nom du contact             Email *                                         │
│  ┌───────────────────────┐  ┌───────────────────────┐                      │
│  │ Jean Dupont           │  │ contact@abc.fr        │                      │
│  └───────────────────────┘  └───────────────────────┘                      │
│                                                                             │
│  Téléphone                                                                  │
│  ┌───────────────────────┐                                                 │
│  │ 01 23 45 67 89        │                                                 │
│  └───────────────────────┘                                                 │
│                                                                             │
│  ADRESSE                                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Adresse ligne 1                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 123 rue de Paris                                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Code postal          Ville                   Pays                          │
│  ┌───────────────┐   ┌───────────────────┐   ┌───────────────────┐         │
│  │ 75001         │   │ Paris             │   │ France       ▼    │         │
│  └───────────────┘   └───────────────────┘   └───────────────────┘         │
│                                                                             │
│  CONDITIONS COMMERCIALES                                                    │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  Délai de paiement          Marge par défaut                                │
│  ┌───────────────────────┐  ┌───────────────────────┐                      │
│  │ 30 jours         ▼    │  │ 15 %                  │                      │
│  └───────────────────────┘  └───────────────────────┘                      │
│                                                                             │
│  Notes                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Client régulier, bon payeur                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────────────  │
│                                                                             │
│  ┌───────────────┐                              ┌───────────────────────┐   │
│  │   Annuler     │                              │   Créer et sélectionner│   │
│  └───────────────┘                              └───────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. API Endpoints

### 5.1 Gestion des clients

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/v1/customers` | Lister les clients |
| `GET` | `/api/v1/customers/{id}` | Détail d'un client |
| `POST` | `/api/v1/customers` | Créer un client |
| `PUT` | `/api/v1/customers/{id}` | Modifier un client |
| `DELETE` | `/api/v1/customers/{id}` | Supprimer un client |

### 5.2 Autocomplete clients

```bash
GET /api/v1/customers/search?q={query}&limit={limit}

# Exemples
GET /api/v1/customers/search?q=abc&limit=10
GET /api/v1/customers/search?q=123456789&limit=5  # Recherche par SIRET
GET /api/v1/customers/search?q=contact@abc.fr     # Recherche par email
```

**Réponse :**
```json
{
  "results": [
    {
      "id": "uuid",
      "code": "CLI-001",
      "company_name": "SARL ABC",
      "trade_name": "ABC Logistique",
      "contact_name": "Jean Dupont",
      "contact_email": "contact@abc.fr",
      "siret": "12345678900012",
      "city": "Paris",
      "is_active": true
    }
  ],
  "total": 1
}
```

### 5.3 Validation à la création de devis

```bash
POST /api/v1/customer-quotes
Content-Type: application/json

{
  "customer_id": "uuid-du-client"  # Obligatoire
}
```

**Réponse (erreur 400) :**
```json
{
  "detail": "Le champ customer_id est obligatoire. Veuillez sélectionner un client existant."
}
```

**Réponse (erreur 404) :**
```json
{
  "detail": "Client non trouvé. L'ID 'xxx' ne correspond à aucun client actif."
}
```

---

## 6. Composants Frontend

### 6.1 Nouveaux composants

```
frontend/src/
├── components/
│   ├── customer/
│   │   ├── CustomerAutocomplete.tsx    # Champ autocomplete
│   │   ├── CustomerCard.tsx            # Affichage client sélectionné
│   │   ├── CustomerCreateModal.tsx     # Modal création client
│   │   └── CustomerList.tsx            # Liste des clients (admin)
│   │
│   └── customer-quote/
│       └── editor/
│           └── CustomerSection.tsx     # Section client dans l'éditeur
│
├── services/
│   └── customerService.ts              # API calls
│
└── types/
    └── customer.ts                     # Types TypeScript
```

### 6.2 Types TypeScript

```typescript
// types/customer.ts

export interface Customer {
  id: string;
  code: string;
  siret?: string;
  company_name: string;
  trade_name?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  address_line1?: string;
  address_line2?: string;
  postal_code?: string;
  city?: string;
  country: string;
  payment_terms: number;
  default_margin: number;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface CustomerSearchResult {
  id: string;
  code: string;
  company_name: string;
  trade_name?: string;
  contact_name?: string;
  contact_email?: string;
  siret?: string;
  city?: string;
  is_active: boolean;
}

export interface CustomerCreate {
  company_name: string;
  trade_name?: string;
  siret?: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  address_line1?: string;
  address_line2?: string;
  postal_code?: string;
  city?: string;
  country?: string;
  payment_terms?: number;
  default_margin?: number;
  notes?: string;
}
```

---

## 7. Règles de validation

### 7.1 Validation backend

| Règle | Champ | Description |
|-------|-------|-------------|
| Obligatoire | `customer_id` | Un client doit être sélectionné |
| Existence | `customer_id` | Le client doit exister dans la table `customers` |
| Actif | `customer.is_active` | Le client doit être actif |
| Format | `siret` | 14 chiffres (optionnel) |
| Unicité | `siret` | Un seul client par SIRET |
| Unicité | `code` | Code client unique |

### 7.2 Validation frontend

```typescript
// Avant soumission du devis
const validateQuote = (quote: CustomerQuoteCreate): ValidationResult => {
  const errors: string[] = [];

  if (!quote.customer_id) {
    errors.push("Veuillez sélectionner un client");
  }

  // La validation d'existence est faite côté backend

  return {
    isValid: errors.length === 0,
    errors
  };
};
```

---

## 8. Migration des données

### 8.1 Script de migration

```python
# alembic/versions/xxx_add_customers_table.py

def upgrade():
    # 1. Créer la table customers
    op.create_table(
        'customers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('siret', sa.String(14), nullable=True),
        sa.Column('company_name', sa.String(), nullable=False),
        # ... autres colonnes
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.UniqueConstraint('siret')
    )

    # 2. Ajouter la colonne customer_id à customer_quotes (nullable d'abord)
    op.add_column('customer_quotes',
        sa.Column('customer_id', sa.String(), nullable=True)
    )

    # 3. Créer les clients à partir des devis existants
    # (script de migration des données)

    # 4. Rendre customer_id obligatoire
    # op.alter_column('customer_quotes', 'customer_id', nullable=False)

def downgrade():
    op.drop_column('customer_quotes', 'customer_id')
    op.drop_table('customers')
```

### 8.2 Migration des devis existants

Pour les devis existants sans `customer_id` :
- Option 1 : Créer automatiquement un client à partir des données du devis
- Option 2 : Laisser `customer_id` nullable temporairement
- Option 3 : Assigner un client "Inconnu" par défaut

---

## 9. Estimation

| Tâche | Effort |
|-------|--------|
| **Backend** | |
| Modèle Customer + migration | ~1h |
| API CRUD Customers | ~2h |
| API Autocomplete | ~1h |
| Modification CustomerQuote (customer_id) | ~1h |
| Validation et tests | ~1h |
| **Frontend** | |
| CustomerAutocomplete component | ~2h |
| CustomerCard component | ~1h |
| CustomerCreateModal | ~2h |
| CustomerSection dans l'éditeur | ~1h30 |
| CustomerService (API) | ~30min |
| Page admin Customers (optionnel) | ~2h |
| **Tests & Documentation** | |
| Tests unitaires | ~2h |
| Documentation | ~1h |
| **Total** | **~17-19h** |

---

## 10. Questions ouvertes

1. **Import de clients** : Faut-il prévoir un import CSV/Excel des clients ?

2. **Doublons** : Comment gérer les doublons potentiels (même société, noms différents) ?

3. **Historique** : Garder l'historique des modifications client ?

4. **Droits d'accès** : Qui peut créer/modifier des clients ?

5. **Synchronisation externe** : Lien avec un ERP ou CRM existant ?

---

## 11. Décision

Quelle option choisissez-vous ?

- [ ] **Option A** : Nouvelle table `Customers` (recommandée)
- [ ] **Option B** : Extension de la table `Partners`
- [ ] **Option C** : Mode mixte (optionnel)

Voulez-vous :
- [ ] Validation stricte (client obligatoire)
- [ ] Validation souple (client optionnel mais recommandé)

Fonctionnalités supplémentaires :
- [ ] Import CSV des clients
- [ ] Page d'administration des clients
- [ ] Historique des modifications
