# Propositions d'Architecture - Application de Devis Transport

## Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Proposition 1 : Architecture Microservices](#proposition-1--architecture-microservices)
3. [Proposition 2 : Architecture Modulaire Monolithique](#proposition-2--architecture-modulaire-monolithique)
4. [Proposition 3 : Architecture Serverless Event-Driven](#proposition-3--architecture-serverless-event-driven)
5. [Comparatif des architectures](#comparatif-des-architectures)
6. [Recommandation](#recommandation)
7. [Détails techniques communs](#détails-techniques-communs)

---

## Vue d'ensemble

### Objectifs principaux
- **Modularité** : Modules autonomes et interopérables
- **Flexibilité d'intégration** : Compatible ERP, CRM, SaaS
- **Multi-environnement** : Cloud, on-premise, hybride

### Les 3 modules fonctionnels
1. **Module Devis Partenaires** : Collecte et validation des devis transporteurs
2. **Module Correspondance** : Moteur de recherche et sélection des offres
3. **Module Génération** : Création et envoi des devis clients

---

## Proposition 1 : Architecture Microservices

### Schéma

```
                                    ┌─────────────────────────┐
                                    │      API Gateway        │
                                    │   (Kong / Traefik)      │
                                    └───────────┬─────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
                    ▼                           ▼                           ▼
    ┌───────────────────────────┐ ┌───────────────────────────┐ ┌───────────────────────────┐
    │  Partner Quotes Service   │ │   Matching Engine Service │ │   Quote Generator Service │
    │  ─────────────────────    │ │   ─────────────────────   │ │   ─────────────────────   │
    │  • REST/GraphQL API       │ │  • Algorithmes de tri     │ │  • Templates Jinja2       │
    │  • File Parser            │ │  • Cache Redis            │ │  • PDF Generation         │
    │  • Validation Schema      │ │  • Plugin System          │ │  • Connecteurs externes   │
    │  • Webhooks               │ │                           │ │                           │
    └───────────┬───────────────┘ └───────────┬───────────────┘ └───────────┬───────────────┘
                │                             │                             │
                ▼                             │                             │
    ┌───────────────────────────┐             │                             │
    │     PostgreSQL / MongoDB  │◄────────────┘                             │
    │     (Quotes Database)     │                                           │
    └───────────────────────────┘                                           │
                                                                            ▼
    ┌───────────────────────────┐                               ┌───────────────────────────┐
    │        Redis Cache        │                               │     Message Broker        │
    │  (Sessions + Matching)    │                               │   (RabbitMQ / Kafka)      │
    └───────────────────────────┘                               └───────────────────────────┘
                                                                            │
                                        ┌───────────────────────────────────┼───────────────┐
                                        ▼                                   ▼               ▼
                            ┌─────────────────────┐           ┌─────────────────┐ ┌─────────────────┐
                            │   Email Service     │           │   CRM Webhook   │ │  ERP Connector  │
                            │   (SendGrid)        │           │   (Salesforce)  │ │  (SAP)          │
                            └─────────────────────┘           └─────────────────┘ └─────────────────┘
```

### Stack technique recommandée

| Composant | Technologie |
|-----------|-------------|
| API Gateway | Kong / Traefik / AWS API Gateway |
| Services | Node.js (NestJS) ou Python (FastAPI) |
| Base de données | PostgreSQL + MongoDB (polyglot) |
| Cache | Redis Cluster |
| Message Broker | RabbitMQ ou Apache Kafka |
| Conteneurisation | Docker + Kubernetes |
| Service Mesh | Istio (optionnel) |

### Structure des services

```
transport-quote-platform/
├── services/
│   ├── partner-quotes-service/
│   │   ├── src/
│   │   │   ├── api/
│   │   │   │   ├── rest/
│   │   │   │   └── graphql/
│   │   │   ├── domain/
│   │   │   │   ├── entities/
│   │   │   │   ├── repositories/
│   │   │   │   └── services/
│   │   │   ├── infrastructure/
│   │   │   │   ├── database/
│   │   │   │   ├── messaging/
│   │   │   │   └── file-parser/
│   │   │   └── config/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   ├── matching-engine-service/
│   │   ├── src/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   │   ├── strategies/
│   │   │   │   │   ├── price-strategy.ts
│   │   │   │   │   ├── time-strategy.ts
│   │   │   │   │   └── rating-strategy.ts
│   │   │   │   └── plugins/
│   │   │   ├── infrastructure/
│   │   │   │   └── cache/
│   │   │   └── config/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── package.json
│   │
│   └── quote-generator-service/
│       ├── src/
│       │   ├── api/
│       │   ├── domain/
│       │   │   ├── templates/
│       │   │   └── generators/
│       │   ├── infrastructure/
│       │   │   ├── connectors/
│       │   │   │   ├── email/
│       │   │   │   ├── crm/
│       │   │   │   └── payment/
│       │   │   └── storage/
│       │   └── config/
│       ├── tests/
│       ├── Dockerfile
│       └── package.json
│
├── shared/
│   ├── sdk-python/
│   ├── sdk-javascript/
│   └── sdk-java/
│
├── infrastructure/
│   ├── kubernetes/
│   │   ├── base/
│   │   └── overlays/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── production/
│   ├── terraform/
│   └── docker-compose.yml
│
├── api-gateway/
│   └── kong.yml
│
└── docs/
    ├── openapi/
    └── architecture/
```

### Avantages
- **Scalabilité indépendante** : Chaque service scale selon ses besoins
- **Déploiement indépendant** : Mise à jour sans downtime global
- **Polyglot** : Liberté de technologie par service
- **Résilience** : Isolation des pannes

### Inconvénients
- **Complexité opérationnelle** : Orchestration, monitoring, debugging distribué
- **Latence réseau** : Communication inter-services
- **Coût initial** : Infrastructure plus lourde

---

## Proposition 2 : Architecture Modulaire Monolithique

### Schéma

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            Application Monolithique                              │
│                                                                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   API Layer     │    │   API Layer     │    │   API Layer     │             │
│  │   /v1/partners  │    │   /v1/match     │    │   /v1/generate  │             │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘             │
│           │                      │                      │                       │
│  ┌────────▼────────┐    ┌────────▼────────┐    ┌────────▼────────┐             │
│  │                 │    │                 │    │                 │             │
│  │  Partner Module │◄──►│ Matching Module │◄──►│ Generator Module│             │
│  │                 │    │                 │    │                 │             │
│  │  • QuoteService │    │ • MatchService  │    │ • TemplateEngine│             │
│  │  • FileParser   │    │ • Strategies    │    │ • PDFGenerator  │             │
│  │  • Validator    │    │ • CacheManager  │    │ • Connectors    │             │
│  │                 │    │                 │    │                 │             │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘             │
│           │                      │                      │                       │
│           └──────────────────────┼──────────────────────┘                       │
│                                  │                                              │
│  ┌───────────────────────────────▼───────────────────────────────────────────┐ │
│  │                        Shared Infrastructure                               │ │
│  │                                                                            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │  Database   │  │    Cache    │  │   Events    │  │    Auth     │      │ │
│  │  │  Adapter    │  │   Manager   │  │ Dispatcher  │  │   Module    │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  │                                                                            │ │
│  └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                    │                      │                      │
                    ▼                      ▼                      ▼
        ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
        │    PostgreSQL     │  │      Redis        │  │    RabbitMQ       │
        └───────────────────┘  └───────────────────┘  └───────────────────┘
```

### Stack technique recommandée

| Composant | Technologie |
|-----------|-------------|
| Framework | NestJS (Node.js) ou Django (Python) |
| Base de données | PostgreSQL |
| ORM | Prisma / TypeORM / SQLAlchemy |
| Cache | Redis |
| Events | EventEmitter interne + RabbitMQ externe |
| API Docs | Swagger/OpenAPI |

### Structure du projet

```
transport-quote-app/
├── src/
│   ├── modules/
│   │   ├── partners/
│   │   │   ├── controllers/
│   │   │   │   ├── rest.controller.ts
│   │   │   │   └── graphql.resolver.ts
│   │   │   ├── services/
│   │   │   │   ├── quote.service.ts
│   │   │   │   ├── file-parser.service.ts
│   │   │   │   └── validator.service.ts
│   │   │   ├── entities/
│   │   │   │   └── partner-quote.entity.ts
│   │   │   ├── dto/
│   │   │   ├── partners.module.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── matching/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   │   ├── matching.service.ts
│   │   │   │   └── cache.service.ts
│   │   │   ├── strategies/
│   │   │   │   ├── strategy.interface.ts
│   │   │   │   ├── price.strategy.ts
│   │   │   │   ├── time.strategy.ts
│   │   │   │   └── rating.strategy.ts
│   │   │   ├── plugins/
│   │   │   │   └── plugin-loader.ts
│   │   │   ├── matching.module.ts
│   │   │   └── index.ts
│   │   │
│   │   ├── generator/
│   │   │   ├── controllers/
│   │   │   ├── services/
│   │   │   │   ├── template.service.ts
│   │   │   │   ├── pdf.service.ts
│   │   │   │   └── notification.service.ts
│   │   │   ├── connectors/
│   │   │   │   ├── connector.interface.ts
│   │   │   │   ├── email/
│   │   │   │   │   ├── sendgrid.connector.ts
│   │   │   │   │   └── smtp.connector.ts
│   │   │   │   ├── crm/
│   │   │   │   │   ├── salesforce.connector.ts
│   │   │   │   │   └── hubspot.connector.ts
│   │   │   │   └── payment/
│   │   │   │       └── stripe.connector.ts
│   │   │   ├── templates/
│   │   │   ├── generator.module.ts
│   │   │   └── index.ts
│   │   │
│   │   └── auth/
│   │       ├── guards/
│   │       ├── strategies/
│   │       │   ├── oauth2.strategy.ts
│   │       │   └── api-key.strategy.ts
│   │       └── auth.module.ts
│   │
│   ├── shared/
│   │   ├── database/
│   │   ├── cache/
│   │   ├── events/
│   │   ├── utils/
│   │   └── interfaces/
│   │
│   ├── config/
│   │   ├── database.config.ts
│   │   ├── cache.config.ts
│   │   └── app.config.ts
│   │
│   ├── app.module.ts
│   └── main.ts
│
├── sdk/
│   ├── python/
│   ├── javascript/
│   └── java/
│
├── templates/
│   └── quotes/
│
├── test/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── docs/
│   └── openapi.yaml
│
└── package.json
```

### Pattern d'export de modules

Chaque module peut être extrait et publié comme package NPM indépendant :

```typescript
// modules/partners/index.ts
export { PartnersModule } from './partners.module';
export { QuoteService } from './services/quote.service';
export { PartnerQuote } from './entities/partner-quote.entity';
export * from './dto';

// Usage externe possible
import { PartnersModule } from '@transport-quote/partners-module';
```

### Avantages
- **Simplicité de déploiement** : Une seule application
- **Communication directe** : Pas de latence réseau entre modules
- **Debugging facile** : Stack trace unique
- **Coût réduit** : Infrastructure minimale

### Inconvénients
- **Scalabilité globale** : Tout scale ensemble
- **Couplage potentiel** : Discipline requise pour maintenir l'isolation
- **Déploiement global** : Mise à jour = redéploiement complet

---

## Proposition 3 : Architecture Serverless Event-Driven

### Schéma

```
                                    ┌─────────────────────────┐
                                    │      API Gateway        │
                                    │   (AWS API Gateway)     │
                                    └───────────┬─────────────┘
                                                │
            ┌───────────────────────────────────┼───────────────────────────────────┐
            │                                   │                                   │
            ▼                                   ▼                                   ▼
┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
│   Lambda: Partners    │       │   Lambda: Matching    │       │   Lambda: Generator   │
│   ─────────────────   │       │   ─────────────────   │       │   ─────────────────   │
│   • POST /partners    │       │   • POST /match       │       │   • POST /generate    │
│   • GET /partners     │       │   • GET /match        │       │   • GET /quote/{id}   │
│   • Webhook handler   │       │                       │       │                       │
└───────────┬───────────┘       └───────────┬───────────┘       └───────────┬───────────┘
            │                               │                               │
            │                               │                               │
            ▼                               ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
│   DynamoDB            │       │   ElastiCache         │       │      S3               │
│   (Quotes Store)      │       │   (Redis)             │       │   (Templates + PDFs)  │
└───────────────────────┘       └───────────────────────┘       └───────────────────────┘
            │                                                               │
            │                                                               │
            ▼                                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    EventBridge                                           │
│                                                                                          │
│   Events:                                                                                │
│   • quote.created     • quote.updated     • match.completed     • quote.generated       │
│   • quote.sent        • payment.received                                                 │
│                                                                                          │
└────────────────────────────────────────────────┬────────────────────────────────────────┘
                                                 │
        ┌────────────────────────────────────────┼────────────────────────────────────────┐
        │                                        │                                        │
        ▼                                        ▼                                        ▼
┌───────────────────┐                ┌───────────────────┐                ┌───────────────────┐
│  Lambda: Email    │                │  Lambda: CRM      │                │  Lambda: Analytics│
│  Notification     │                │  Sync             │                │  Processor        │
└───────────────────┘                └───────────────────┘                └───────────────────┘
        │                                        │                                        │
        ▼                                        ▼                                        ▼
┌───────────────────┐                ┌───────────────────┐                ┌───────────────────┐
│    SES / SNS      │                │    Salesforce     │                │    CloudWatch     │
└───────────────────┘                └───────────────────┘                └───────────────────┘
```

### Stack technique recommandée (AWS)

| Composant | Service AWS | Alternative Azure/GCP |
|-----------|-------------|----------------------|
| Compute | Lambda | Azure Functions / Cloud Functions |
| API | API Gateway | Azure API Management / Cloud Endpoints |
| Database | DynamoDB | Cosmos DB / Firestore |
| Cache | ElastiCache | Azure Cache / Memorystore |
| Events | EventBridge | Event Grid / Pub/Sub |
| Storage | S3 | Blob Storage / Cloud Storage |
| Auth | Cognito | Azure AD B2C / Firebase Auth |
| Queue | SQS | Service Bus / Cloud Tasks |

### Structure du projet

```
transport-quote-serverless/
├── functions/
│   ├── partners/
│   │   ├── create-quote/
│   │   │   ├── handler.ts
│   │   │   ├── schema.ts
│   │   │   └── index.ts
│   │   ├── list-quotes/
│   │   │   └── handler.ts
│   │   ├── import-file/
│   │   │   └── handler.ts
│   │   └── webhook-handler/
│   │       └── handler.ts
│   │
│   ├── matching/
│   │   ├── find-matches/
│   │   │   ├── handler.ts
│   │   │   └── strategies/
│   │   └── cache-invalidator/
│   │       └── handler.ts
│   │
│   ├── generator/
│   │   ├── generate-quote/
│   │   │   └── handler.ts
│   │   ├── send-notification/
│   │   │   └── handler.ts
│   │   └── pdf-renderer/
│   │       └── handler.ts
│   │
│   └── connectors/
│       ├── crm-sync/
│       │   └── handler.ts
│       └── payment-webhook/
│           └── handler.ts
│
├── layers/
│   ├── common/
│   │   ├── nodejs/
│   │   │   └── node_modules/
│   │   └── layer.json
│   └── pdf-tools/
│       └── ...
│
├── shared/
│   ├── types/
│   ├── utils/
│   ├── validators/
│   └── events/
│       ├── quote-events.ts
│       └── schemas/
│
├── infrastructure/
│   ├── cdk/
│   │   ├── lib/
│   │   │   ├── api-stack.ts
│   │   │   ├── database-stack.ts
│   │   │   ├── events-stack.ts
│   │   │   └── functions-stack.ts
│   │   └── bin/
│   │       └── app.ts
│   └── serverless.yml (alternative)
│
├── sdk/
│   ├── python/
│   ├── javascript/
│   └── java/
│
├── templates/
│   └── quotes/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── package.json
```

### Définition des événements (EventBridge)

```typescript
// shared/events/quote-events.ts
export interface QuoteCreatedEvent {
  source: 'transport-quote.partners';
  'detail-type': 'quote.created';
  detail: {
    quoteId: string;
    partnerId: string;
    transportMode: string;
    origin: string;
    destination: string;
    cost: number;
    createdAt: string;
  };
}

export interface MatchCompletedEvent {
  source: 'transport-quote.matching';
  'detail-type': 'match.completed';
  detail: {
    requestId: string;
    customerId: string;
    matches: Array<{
      quoteId: string;
      score: number;
    }>;
  };
}

export interface QuoteGeneratedEvent {
  source: 'transport-quote.generator';
  'detail-type': 'quote.generated';
  detail: {
    quoteId: string;
    customerId: string;
    pdfUrl: string;
    status: 'pending' | 'sent';
  };
}
```

### Avantages
- **Scalabilité automatique** : Scale to zero, scale infini
- **Coût à l'usage** : Pas de serveur idle
- **Haute disponibilité** : Gérée par le cloud provider
- **Découplage natif** : Event-driven par design

### Inconvénients
- **Cold starts** : Latence initiale
- **Vendor lock-in** : Dépendance au provider cloud
- **Debugging complexe** : Traces distribuées
- **Limites** : Timeout, taille payload

---

## Comparatif des architectures

| Critère | Microservices | Monolithique Modulaire | Serverless |
|---------|---------------|------------------------|------------|
| **Complexité initiale** | Élevée | Faible | Moyenne |
| **Scalabilité** | Excellente | Moyenne | Excellente |
| **Coût initial** | Élevé | Faible | Faible |
| **Coût à l'échelle** | Moyen | Élevé | Faible |
| **Latence** | Moyenne | Faible | Variable |
| **Indépendance modules** | Excellente | Bonne | Excellente |
| **Déploiement on-premise** | Bon | Excellent | Limité |
| **Time-to-market** | Long | Court | Moyen |
| **Maintenance** | Complexe | Simple | Moyenne |
| **Vendor lock-in** | Faible | Faible | Élevé |

---

## Recommandation

### Scénario 1 : Startup / MVP
**→ Proposition 2 (Monolithique Modulaire)**

- Démarrage rapide
- Infrastructure simple
- Migration vers microservices possible ultérieurement

### Scénario 2 : Scale-up / Volume élevé
**→ Proposition 1 (Microservices)**

- Scalabilité indépendante
- Équipes autonomes par service
- Résilience

### Scénario 3 : Cloud-native / SaaS
**→ Proposition 3 (Serverless)**

- Coût optimisé
- Pas de gestion d'infrastructure
- Scalabilité automatique

### Approche hybride recommandée

```
Phase 1 : Monolithique Modulaire
    │
    │  Validation du produit
    │  Itérations rapides
    │
    ▼
Phase 2 : Extraction progressive
    │
    │  Module le plus sollicité → Microservice
    │  (Généralement le Matching Engine)
    │
    ▼
Phase 3 : Architecture cible
    │
    │  Microservices complets
    │  ou Serverless selon les besoins
    │
    ▼
```

---

## Détails techniques communs

### Schéma de données (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PartnerQuote",
  "type": "object",
  "required": ["transport_mode", "origin", "destination", "cost"],
  "properties": {
    "id": {
      "type": "string",
      "format": "uuid"
    },
    "partner_id": {
      "type": "string"
    },
    "transport_mode": {
      "type": "string",
      "enum": ["road", "rail", "sea", "air", "multimodal"]
    },
    "volume": {
      "type": "number",
      "minimum": 0,
      "description": "Volume in cubic meters"
    },
    "weight": {
      "type": "number",
      "minimum": 0,
      "description": "Weight in kilograms"
    },
    "origin": {
      "type": "object",
      "properties": {
        "postal_code": { "type": "string" },
        "city": { "type": "string" },
        "country": { "type": "string" }
      },
      "required": ["country"]
    },
    "destination": {
      "type": "object",
      "properties": {
        "postal_code": { "type": "string" },
        "city": { "type": "string" },
        "country": { "type": "string" }
      },
      "required": ["country"]
    },
    "cost": {
      "type": "number",
      "minimum": 0
    },
    "currency": {
      "type": "string",
      "default": "EUR"
    },
    "delivery_time": {
      "type": "string",
      "pattern": "^\\d+[hd]$",
      "description": "e.g., 48h, 5d"
    },
    "valid_until": {
      "type": "string",
      "format": "date-time"
    },
    "metadata": {
      "type": "object",
      "additionalProperties": true
    }
  }
}
```

### Spécification OpenAPI (extrait)

```yaml
openapi: 3.0.3
info:
  title: Transport Quote API
  version: 1.0.0
  description: API de génération de devis transport

servers:
  - url: https://api.transport-quote.com/v1
    description: Production
  - url: https://sandbox.transport-quote.com/v1
    description: Sandbox

paths:
  /partners/quotes:
    post:
      summary: Créer un devis partenaire
      tags: [Partners]
      security:
        - bearerAuth: []
        - apiKey: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PartnerQuoteInput'
      responses:
        '201':
          description: Devis créé
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PartnerQuote'
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'

  /quotes/match:
    post:
      summary: Rechercher les meilleures offres
      tags: [Matching]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MatchRequest'
      responses:
        '200':
          description: Offres trouvées
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MatchResponse'

  /quotes/generate:
    post:
      summary: Générer un devis client
      tags: [Generator]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/GenerateRequest'
      responses:
        '201':
          description: Devis généré
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/GeneratedQuote'

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
    apiKey:
      type: apiKey
      in: header
      name: X-API-Key

  schemas:
    PartnerQuoteInput:
      type: object
      required:
        - transport_mode
        - origin
        - destination
        - cost
      properties:
        transport_mode:
          type: string
          enum: [road, rail, sea, air, multimodal]
        volume:
          type: number
        weight:
          type: number
        origin:
          type: string
        destination:
          type: string
        cost:
          type: number
        delivery_time:
          type: string

    MatchRequest:
      type: object
      required:
        - origin
        - destination
      properties:
        volume:
          type: number
        weight:
          type: number
        origin:
          type: string
        destination:
          type: string
        max_cost:
          type: number
        sort_by:
          type: string
          enum: [price, delivery_time, rating]
          default: price
        limit:
          type: integer
          default: 5
          maximum: 20

    MatchResponse:
      type: object
      properties:
        request_id:
          type: string
        matches:
          type: array
          items:
            $ref: '#/components/schemas/MatchedQuote'

    MatchedQuote:
      type: object
      properties:
        quote_id:
          type: string
        partner_name:
          type: string
        cost:
          type: number
        delivery_time:
          type: string
        score:
          type: number

    GeneratedQuote:
      type: object
      properties:
        quote_id:
          type: string
        pdf_url:
          type: string
        status:
          type: string
          enum: [pending, sent]
```

### Pattern de stratégie (Matching Engine)

```typescript
// Interface commune
interface MatchingStrategy {
  name: string;
  calculate(quotes: Quote[], request: MatchRequest): ScoredQuote[];
}

// Stratégie par prix
class PriceStrategy implements MatchingStrategy {
  name = 'price';

  calculate(quotes: Quote[], request: MatchRequest): ScoredQuote[] {
    return quotes
      .filter(q => !request.maxCost || q.cost <= request.maxCost)
      .map(q => ({
        ...q,
        score: 1 - (q.cost / Math.max(...quotes.map(x => x.cost)))
      }))
      .sort((a, b) => b.score - a.score);
  }
}

// Stratégie par délai
class DeliveryTimeStrategy implements MatchingStrategy {
  name = 'delivery_time';

  calculate(quotes: Quote[], request: MatchRequest): ScoredQuote[] {
    const parseTime = (t: string) => {
      const value = parseInt(t);
      return t.endsWith('d') ? value * 24 : value;
    };

    return quotes
      .map(q => ({
        ...q,
        score: 1 - (parseTime(q.deliveryTime) /
                    Math.max(...quotes.map(x => parseTime(x.deliveryTime))))
      }))
      .sort((a, b) => b.score - a.score);
  }
}

// Registre des stratégies
class StrategyRegistry {
  private strategies = new Map<string, MatchingStrategy>();

  register(strategy: MatchingStrategy) {
    this.strategies.set(strategy.name, strategy);
  }

  get(name: string): MatchingStrategy {
    const strategy = this.strategies.get(name);
    if (!strategy) throw new Error(`Strategy ${name} not found`);
    return strategy;
  }
}
```

### Configuration par variables d'environnement

```bash
# .env.example

# Application
NODE_ENV=production
PORT=3000
API_VERSION=v1

# Database
DATABASE_URL=postgresql://user:pass@host:5432/transport_quotes
DATABASE_POOL_SIZE=20

# Cache
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600

# Message Broker
RABBITMQ_URL=amqp://localhost:5672
KAFKA_BROKERS=localhost:9092

# Authentication
JWT_SECRET=your-secret-key
OAUTH2_CLIENT_ID=xxx
OAUTH2_CLIENT_SECRET=xxx

# External Services
SENDGRID_API_KEY=xxx
SALESFORCE_CLIENT_ID=xxx
STRIPE_SECRET_KEY=xxx

# Storage
S3_BUCKET=transport-quote-templates
S3_REGION=eu-west-1

# Monitoring
PROMETHEUS_PORT=9090
LOG_LEVEL=info
```

### Monitoring et observabilité

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "6831:6831/udp"

volumes:
  grafana-data:
```

---

## Réutilisabilité des modules dans d'autres applications

### Vue d'ensemble

| Architecture | Réutilisabilité | Mode de réutilisation | Effort |
|--------------|-----------------|----------------------|--------|
| **Microservices** | Excellente | API / Conteneur | Faible |
| **Monolithique Modulaire** | Bonne | Package NPM/PyPI | Moyen |
| **Serverless** | Limitée | Code source | Élevé |

---

### Proposition 1 (Microservices) : Réutilisation native

Les microservices sont **intrinsèquement réutilisables** car chaque service est une application autonome.

#### Modes de réutilisation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Application A (Transport)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │  Partners   │  │  Matching   │  │  Generator  │                 │
│  │  Service    │  │  Service    │  │  Service    │                 │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │
└─────────┼────────────────┼────────────────┼─────────────────────────┘
          │                │                │
          │    Réutilisation via API        │
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────────────────┐
│                    Application B (Logistique)                        │
│                                                                      │
│  • Utilise le Matching Service existant                             │
│  • Consomme l'API Partners pour ses propres partenaires             │
│  • Génère ses devis via le Generator Service                        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### Option 1 : Consommation via API (recommandé)

```typescript
// Dans Application B - Consommation du Matching Service existant
import axios from 'axios';

class ExternalMatchingClient {
  constructor(private baseUrl: string, private apiKey: string) {}

  async findMatches(request: MatchRequest): Promise<MatchResponse> {
    const response = await axios.post(
      `${this.baseUrl}/v1/quotes/match`,
      request,
      { headers: { 'X-API-Key': this.apiKey } }
    );
    return response.data;
  }
}

// Usage
const matchingClient = new ExternalMatchingClient(
  'https://matching.transport-quote.com',
  process.env.MATCHING_API_KEY
);
```

#### Option 2 : Déploiement d'une instance dédiée

```yaml
# docker-compose.app-b.yml
version: '3.8'

services:
  # Instance dédiée du Matching Service pour App B
  matching-service:
    image: transport-quote/matching-service:latest
    environment:
      - DATABASE_URL=${APP_B_DATABASE_URL}
      - REDIS_URL=${APP_B_REDIS_URL}
    ports:
      - "3002:3000"
```

#### Option 3 : Multi-tenant (même instance, données isolées)

```typescript
// Configuration multi-tenant
const config = {
  tenants: {
    'transport-app': { dbSchema: 'transport', cachePrefix: 'tr' },
    'logistics-app': { dbSchema: 'logistics', cachePrefix: 'lg' },
  }
};
```

---

### Proposition 2 (Monolithique Modulaire) : Extraction en packages

Les modules doivent être **extraits et publiés** comme packages indépendants pour être réutilisés.

#### Architecture pour la réutilisabilité

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Monorepo                                     │
│                                                                      │
│  packages/                                                           │
│  ├── @tq/core              # Types, interfaces, utilitaires         │
│  ├── @tq/partners-module   # Module partenaires (extractible)       │
│  ├── @tq/matching-module   # Module matching (extractible)          │
│  ├── @tq/generator-module  # Module génération (extractible)        │
│  └── @tq/connectors        # Connecteurs (email, CRM, etc.)         │
│                                                                      │
│  apps/                                                               │
│  ├── transport-quote-app   # Application principale                 │
│  └── logistics-app         # Autre app utilisant les mêmes modules  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### Structure d'un module réutilisable

```
packages/matching-module/
├── src/
│   ├── index.ts                 # Point d'entrée public
│   ├── matching.module.ts       # Module NestJS/Angular
│   ├── services/
│   │   ├── matching.service.ts
│   │   └── cache.service.ts
│   ├── strategies/
│   │   ├── strategy.interface.ts
│   │   ├── price.strategy.ts
│   │   └── time.strategy.ts
│   ├── interfaces/
│   │   ├── match-request.ts
│   │   └── match-response.ts
│   └── adapters/
│       ├── database.adapter.ts  # Interface abstraite
│       └── cache.adapter.ts     # Interface abstraite
├── package.json
├── tsconfig.json
└── README.md
```

#### Pattern Adapter pour découpler les dépendances

```typescript
// packages/matching-module/src/adapters/database.adapter.ts
export interface QuoteDatabaseAdapter {
  findQuotes(criteria: QuoteCriteria): Promise<Quote[]>;
  getQuoteById(id: string): Promise<Quote | null>;
}

// packages/matching-module/src/adapters/cache.adapter.ts
export interface CacheAdapter {
  get<T>(key: string): Promise<T | null>;
  set<T>(key: string, value: T, ttl?: number): Promise<void>;
  invalidate(pattern: string): Promise<void>;
}

// packages/matching-module/src/matching.module.ts
@Module({})
export class MatchingModule {
  static forRoot(options: MatchingModuleOptions): DynamicModule {
    return {
      module: MatchingModule,
      providers: [
        { provide: 'DATABASE_ADAPTER', useClass: options.databaseAdapter },
        { provide: 'CACHE_ADAPTER', useClass: options.cacheAdapter },
        MatchingService,
      ],
      exports: [MatchingService],
    };
  }
}
```

#### Utilisation dans une autre application

```typescript
// apps/logistics-app/src/app.module.ts
import { MatchingModule } from '@tq/matching-module';
import { PostgresQuoteAdapter } from './adapters/postgres-quote.adapter';
import { RedisCacheAdapter } from './adapters/redis-cache.adapter';

@Module({
  imports: [
    MatchingModule.forRoot({
      databaseAdapter: PostgresQuoteAdapter,
      cacheAdapter: RedisCacheAdapter,
    }),
  ],
})
export class AppModule {}
```

#### Publication sur NPM (privé ou public)

```json
// packages/matching-module/package.json
{
  "name": "@transport-quote/matching-module",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "peerDependencies": {
    "@nestjs/common": "^10.0.0",
    "@nestjs/core": "^10.0.0"
  },
  "publishConfig": {
    "registry": "https://npm.pkg.github.com"
  }
}
```

---

### Proposition 3 (Serverless) : Réutilisation du code source

La réutilisation est **limitée** car les fonctions sont couplées à l'infrastructure cloud.

#### Ce qui est réutilisable

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Réutilisable                                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  shared/                                                     │    │
│  │  ├── types/          # Interfaces et types                  │    │
│  │  ├── validators/     # Logique de validation                │    │
│  │  ├── strategies/     # Algorithmes de matching              │    │
│  │  └── utils/          # Fonctions utilitaires                │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      NON Réutilisable (vendor-specific)             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  • Handlers Lambda                                           │    │
│  │  • Configuration EventBridge                                 │    │
│  │  • Intégration DynamoDB                                      │    │
│  │  • Infrastructure CDK/Terraform                              │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

#### Pattern pour maximiser la réutilisabilité

```typescript
// shared/core/matching-engine.ts (RÉUTILISABLE)
export class MatchingEngine {
  constructor(private strategies: Map<string, MatchingStrategy>) {}

  match(quotes: Quote[], request: MatchRequest): ScoredQuote[] {
    const strategy = this.strategies.get(request.sortBy)
      ?? this.strategies.get('price');
    return strategy.calculate(quotes, request);
  }
}

// functions/matching/handler.ts (NON RÉUTILISABLE - AWS spécifique)
import { APIGatewayProxyHandler } from 'aws-lambda';
import { MatchingEngine } from '../../shared/core/matching-engine';
import { DynamoDBQuoteRepository } from './dynamodb-repository';

export const handler: APIGatewayProxyHandler = async (event) => {
  const repository = new DynamoDBQuoteRepository();
  const engine = new MatchingEngine(strategies);

  const quotes = await repository.findAll();
  const request = JSON.parse(event.body);
  const results = engine.match(quotes, request);

  return { statusCode: 200, body: JSON.stringify(results) };
};
```

#### Extraction vers une architecture portable

```typescript
// Pour réutiliser dans une autre app (Express, NestJS, etc.)
import { MatchingEngine, strategies } from '@tq/matching-core';

// Express
app.post('/match', async (req, res) => {
  const engine = new MatchingEngine(strategies);
  const quotes = await postgresRepository.findAll();
  const results = engine.match(quotes, req.body);
  res.json(results);
});
```

---

### Recommandations pour maximiser la réutilisabilité

#### 1. Séparer la logique métier de l'infrastructure

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Architecture en couches                       │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Couche Présentation (API)        [Spécifique à l'app]      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Couche Application (Use Cases)   [Réutilisable]            │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Couche Domaine (Entités, Rules)  [Très réutilisable]       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  Couche Infrastructure (DB, Cache) [Spécifique à l'app]     │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### 2. Utiliser des interfaces (Ports & Adapters)

```typescript
// Port (interface) - Réutilisable
export interface QuoteRepository {
  save(quote: Quote): Promise<Quote>;
  findById(id: string): Promise<Quote | null>;
  findByCriteria(criteria: QuoteCriteria): Promise<Quote[]>;
}

// Adapter PostgreSQL - Spécifique
export class PostgresQuoteRepository implements QuoteRepository {
  // Implémentation PostgreSQL
}

// Adapter DynamoDB - Spécifique
export class DynamoDBQuoteRepository implements QuoteRepository {
  // Implémentation DynamoDB
}

// Adapter In-Memory - Pour les tests
export class InMemoryQuoteRepository implements QuoteRepository {
  // Implémentation en mémoire
}
```

#### 3. Versionner les contrats d'API

```typescript
// Contrats stables = réutilisation facile
export interface MatchRequestV1 {
  version: '1.0';
  origin: string;
  destination: string;
  volume?: number;
  weight?: number;
}

export interface MatchRequestV2 extends MatchRequestV1 {
  version: '2.0';
  transportModes?: TransportMode[];
  constraints?: MatchConstraints;
}
```

---

### Tableau de décision

| Besoin | Architecture recommandée |
|--------|-------------------------|
| Réutilisation par **API** (multi-apps, multi-équipes) | Microservices |
| Réutilisation par **package** (même stack technique) | Monolithique Modulaire |
| Réutilisation de la **logique métier** uniquement | Serverless (avec extraction core) |
| Réutilisation **on-premise + cloud** | Microservices (conteneurs) |
| **MVP rapide** puis réutilisation future | Monolithique → extraction progressive |

---

## Prochaines étapes

1. **Choix de l'architecture** selon le contexte business
2. **POC** sur le module le plus critique (généralement Matching)
3. **Définition des contrats d'API** avec les partenaires
4. **Mise en place CI/CD** et environnement de sandbox
5. **Développement itératif** module par module
