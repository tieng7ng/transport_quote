# Spécification : Historique des Actions Utilisateurs

## Décision retenue : Table d'audit PostgreSQL (Proposition 1)

Stocker chaque action dans une table dédiée `user_activity_logs` directement en base de données.
Le logging est appelé manuellement dans chaque route FastAPI concernée, dans la même transaction.

---

## Décisions de politique

| #   | Question            | Décision                                                                                         |
| --- | ------------------- | ------------------------------------------------------------------------------------------------ |
| 1   | Durée de rétention  | **1 an** — suppression automatique au-delà                                                       |
| 2   | Visibilité par rôle | **ADMIN et SUPER_ADMIN uniquement**                                                              |
| 3   | Export              | **CSV et PDF** via modale de configuration                                                       |
| 4   | Alertes             | **Badge + modale** dans l'interface — échecs de connexion + actions suspectes                    |
| 5   | RGPD                | Stockage autorisé sur base d'intérêt légitime — clause à ajouter en politique de confidentialité |

---

## Modèle de données

### Table `user_activity_logs`

```sql
CREATE TABLE user_activity_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    user_login  VARCHAR(100),     -- snapshot au moment de l'action
    user_role   VARCHAR(50),      -- snapshot du rôle
    action      VARCHAR(100),     -- ex: "search.performed", "quote.status_changed"
    resource    VARCHAR(50),      -- ex: "customer_quote", "partner"
    resource_id VARCHAR(100),
    details     JSONB,            -- données contextuelles libres
    ip_address  VARCHAR(45),
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_activity_user_id   ON user_activity_logs(user_id);
CREATE INDEX idx_activity_action    ON user_activity_logs(action);
CREATE INDEX idx_activity_created_at ON user_activity_logs(created_at DESC);
CREATE INDEX idx_activity_resource  ON user_activity_logs(resource, resource_id);
```

### Table `security_alerts`

```sql
CREATE TABLE security_alerts (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type          VARCHAR(50),    -- "login_failures" | "suspicious_activity"
    severity      VARCHAR(20),    -- "critical" | "medium"
    details       JSONB,
    seen_at       TIMESTAMP WITH TIME ZONE,
    resolved_by   UUID REFERENCES users(id),      -- qui a traité l'alerte
    resolved_at   TIMESTAMP WITH TIME ZONE,
    resolution    VARCHAR(100),                   -- "account_disabled" | "ignored"
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Catalogue des actions

| Action                  | Ressource        | Déclencheur                        |
| ----------------------- | ---------------- | ---------------------------------- |
| `auth.login_success`    | `user`           | POST /auth/login (succès)          |
| `auth.login_failed`     | `user`           | POST /auth/login (échec)           |
| `auth.logout`           | `user`           | POST /auth/logout                  |
| `auth.password_changed` | `user`           | POST /auth/change-password         |
| `search.performed`      | `search`         | POST /matching/search              |
| `quote.created`         | `customer_quote` | POST /customer-quotes              |
| `quote.updated`         | `customer_quote` | PUT /customer-quotes/{id}          |
| `quote.status_changed`  | `customer_quote` | PATCH /customer-quotes/{id}/status |
| `quote.deleted`         | `customer_quote` | DELETE /customer-quotes/{id}       |
| `import.started`        | `import_job`     | POST /imports                      |
| `import.completed`      | `import_job`     | Fin de traitement                  |
| `import.failed`         | `import_job`     | Erreur de traitement               |
| `user.created`          | `user`           | POST /users                        |
| `user.updated`          | `user`           | PUT /users/{id}                    |
| `user.deactivated`      | `user`           | DELETE /users/{id}                 |
| `partner.created`       | `partner`        | POST /partners                     |
| `partner.updated`       | `partner`        | PUT /partners/{id}                 |

### Exemples de contenu du champ `details`

**Recherche :**
```json
{ "origin_city": "Paris", "origin_country": "FR", "dest_city": "Lyon",
  "dest_country": "FR", "transport_mode": "ROAD", "weight_kg": 500, "results_count": 8 }
```

**Changement de statut d'un devis :**
```json
{ "reference": "DEV-2026-042", "previous_status": "READY", "new_status": "SENT", "customer": "ACME Corp" }
```

**Import :**
```json
{ "filename": "tarifs_geodis.xlsx", "partner": "GEODIS", "rows_imported": 342, "rows_failed": 5 }
```

**Connexion échouée :**
```json
{ "attempted_login": "johndoe", "reason": "invalid_credentials" }
```

---

## Architecture

```
Route FastAPI
    └── log_activity(db, action, user, details, request)
            └── INSERT dans user_activity_logs
                    └── PostgreSQL (même transaction que l'action métier)
```

---

## Implémentation backend

### Fichiers à créer

| Fichier                                    | Rôle                                |
| ------------------------------------------ | ----------------------------------- |
| `backend/app/models/activity_log.py`       | Modèle SQLAlchemy `UserActivityLog` |
| `backend/app/models/security_alert.py`     | Modèle SQLAlchemy `SecurityAlert`   |
| `backend/app/services/activity_service.py` | Fonction `log_activity()`           |
| `backend/app/services/alert_service.py`    | Détection des alertes de sécurité   |
| `backend/app/api/activity_logs.py`         | Endpoints consultation + export     |
| `backend/app/api/stats.py`                 | Endpoints statistiques              |
| `backend/app/api/alerts.py`                | Endpoints alertes + SSE stream      |

### Modèle SQLAlchemy

```python
# backend/app/models/activity_log.py
class UserActivityLog(Base):
    __tablename__ = "user_activity_logs"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_login = Column(String(100))
    user_role  = Column(String(50))
    action     = Column(String(100), nullable=False)
    resource   = Column(String(50))
    resource_id = Column(String(100))
    details    = Column(JSONB, default=dict)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

### Service de logging

```python
# backend/app/services/activity_service.py
def log_activity(
    db: Session,
    action: str,
    user: User | None = None,
    resource: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    request: Request | None = None,
):
    db.add(UserActivityLog(
        user_id    = user.id if user else None,
        user_login = user.login if user else None,
        user_role  = user.role.value if user else None,
        action     = action,
        resource   = resource,
        resource_id = str(resource_id) if resource_id else None,
        details    = details or {},
        ip_address = _get_ip(request) if request else None,
    ))
    # Pas de commit ici — il se fait avec la transaction principale de la route
```

### Intégration dans les routes existantes

```python
# Exemple dans api/auth.py
@router.post("/login")
async def login(...):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        log_activity(db, "auth.login_failed",
            details={"attempted_login": form_data.username, "reason": "invalid_credentials"},
            request=request)
        db.commit()
        raise HTTPException(401)
    log_activity(db, "auth.login_success", user=user, resource="user",
        resource_id=user.id, request=request)
    db.commit()
    return generate_tokens(user)

# Exemple dans api/matching.py
@router.post("/search")
async def search(criteria: SearchCriteria, current_user=Depends(get_current_user), db=Depends(get_db)):
    results = matching_service.search(db, criteria)
    log_activity(db, "search.performed", user=current_user,
        details={**criteria.dict(), "results_count": len(results)},
        request=request)
    db.commit()
    return results
```

### Endpoints API

```
GET  /api/v1/activity-logs                → liste paginée, filtrable (user, action, date)
GET  /api/v1/activity-logs/export         → export CSV ou PDF (?format=csv|pdf)
GET  /api/v1/stats/overview               → KPIs globaux vs période précédente
GET  /api/v1/stats/activity               → activité journalière (courbe)
GET  /api/v1/stats/searches               → top routes, modes, taux résultat nul
GET  /api/v1/stats/quotes                 → entonnoir de conversion, activité par commercial
GET  /api/v1/stats/imports                → taux de succès, volumes par partenaire
GET  /api/v1/stats/security               → échecs de connexion, IPs suspectes
GET  /api/v1/alerts                       → liste des alertes non lues
GET  /api/v1/alerts/stream                → SSE — push des nouvelles alertes en temps réel
PATCH /api/v1/alerts/{id}/seen            → marquer une alerte comme lue
PATCH /api/v1/alerts/{id}/resolve         → résoudre avec action ("account_disabled" | "ignored")
```

Tous les endpoints sont protégés par `require_roles([Role.ADMIN, Role.SUPER_ADMIN])`.
Les paramètres `?from=YYYY-MM-DD&to=YYYY-MM-DD` sont acceptés sur tous les endpoints de stats.

### Rétention automatique (1 an)

Job Python planifié quotidiennement (ou via `pg_cron`) :

```python
# services/activity_service.py
def purge_old_logs(db: Session):
    db.execute(
        "DELETE FROM user_activity_logs WHERE created_at < NOW() - INTERVAL '1 year'"
    )
    db.commit()
```

---

## Statistiques et indicateurs

### Catalogue des indicateurs

#### Activité globale
| Indicateur                | Description                                                    |
| ------------------------- | -------------------------------------------------------------- |
| Utilisateurs actifs       | Nombre d'utilisateurs ayant au moins une action sur la période |
| Connexions par jour       | Courbe sur 30/60/90 jours                                      |
| Pic d'utilisation         | Heures et jours de la semaine les plus actifs                  |
| Taux d'échec de connexion | Ratio login_failed / login_success par utilisateur et global   |

#### Recherches
| Indicateur                  | Description                                          |
| --------------------------- | ---------------------------------------------------- |
| Nombre de recherches        | Par jour / semaine / mois, par utilisateur, par mode |
| Routes les plus recherchées | Top 10 des paires origine → destination              |
| Taux de résultat nul        | % de recherches sans aucun résultat retourné         |
| Mode de transport préféré   | Répartition ROAD / SEA / AIR / RAIL / MULTIMODAL     |

#### Devis
| Indicateur                       | Description                                     |
| -------------------------------- | ----------------------------------------------- |
| Devis créés / envoyés / acceptés | Par période et par utilisateur                  |
| Taux de conversion               | % DRAFT → SENT, % SENT → ACCEPTED               |
| Temps moyen de traitement        | Durée moyenne entre création et envoi           |
| Activité par commercial          | Classement des COMMERCIAL par nombre de devis   |
| Devis abandonnés                 | Devis en DRAFT sans modification depuis X jours |

#### Imports
| Indicateur       | Description                        |
| ---------------- | ---------------------------------- |
| Imports réalisés | Nombre par période, par partenaire |
| Taux de succès   | % COMPLETED vs FAILED              |
| Lignes importées | Total et moyenne par import        |

#### Sécurité
| Indicateur                       | Description                                    |
| -------------------------------- | ---------------------------------------------- |
| Tentatives de connexion échouées | Par utilisateur et par IP                      |
| Activité suspecte                | Volume anormal d'actions par utilisateur       |
| Actions d'administration         | Volume d'actions ADMIN/SUPER_ADMIN par période |

### Vues SQL

```sql
-- Activité journalière
CREATE VIEW daily_activity AS
SELECT DATE(created_at) AS day, action,
    COUNT(*) AS total, COUNT(DISTINCT user_id) AS unique_users
FROM user_activity_logs
GROUP BY DATE(created_at), action;

-- Routes les plus recherchées
CREATE VIEW top_search_routes AS
SELECT
    details->>'origin_city'    AS origin,
    details->>'dest_city'      AS destination,
    details->>'transport_mode' AS mode,
    COUNT(*) AS search_count,
    AVG((details->>'results_count')::int) AS avg_results
FROM user_activity_logs
WHERE action = 'search.performed'
-- Note : GROUP BY sur les expressions, pas les alias (plus robuste)
GROUP BY details->>'origin_city', details->>'dest_city', details->>'transport_mode'
ORDER BY search_count DESC;

-- Performance devis par commercial
CREATE VIEW quote_performance_by_user AS
SELECT user_login, user_role,
    COUNT(*) FILTER (WHERE action = 'quote.created') AS quotes_created,
    COUNT(*) FILTER (WHERE action = 'quote.status_changed'
        AND details->>'new_status' = 'SENT')         AS quotes_sent,
    COUNT(*) FILTER (WHERE action = 'quote.status_changed'
        AND details->>'new_status' = 'ACCEPTED')     AS quotes_accepted
FROM user_activity_logs
WHERE action IN ('quote.created', 'quote.status_changed')
GROUP BY user_login, user_role;

-- Taux d'échec de connexion
CREATE VIEW login_failure_rate AS
SELECT DATE(created_at) AS day, details->>'attempted_login' AS login, ip_address,
    COUNT(*) FILTER (WHERE action = 'auth.login_failed') AS failures,
    COUNT(*) FILTER (WHERE action = 'auth.login_success') AS successes
FROM user_activity_logs
WHERE action IN ('auth.login_failed', 'auth.login_success')
GROUP BY day, login, ip_address;
```

---

## Interface frontend

### Pages à créer

| Page               | Route               | Accès              |
| ------------------ | ------------------- | ------------------ |
| `ActivityLogs.tsx` | `/admin/activity`   | ADMIN, SUPER_ADMIN |
| `Statistics.tsx`   | `/admin/statistics` | ADMIN, SUPER_ADMIN |

### Page Historique des activités

```
┌─────────────────────────────────────────────────────────────────┐
│  Historique des activités                          [Exporter]   │
├──────────────────────────────────────────────────────────────────┤
│  Utilisateur [Tous ▾]  Action [Toutes ▾]  Du [__/__] Au [__/__] │
├──────────────┬───────────────┬──────────────────────┬───────────┤
│  Date/Heure  │ Utilisateur   │ Action               │ Détails   │
├──────────────┼───────────────┼──────────────────────┼───────────┤
│ 23/02 14:32  │ j.martin      │ Recherche effectuée  │ [+]       │
│ 23/02 14:28  │ j.martin      │ Devis créé           │ [+]       │
│ 23/02 09:15  │ a.dupont      │ Connexion            │ [+]       │
│ 22/02 17:44  │ admin         │ Utilisateur créé     │ [+]       │
├──────────────┴───────────────┴──────────────────────┴───────────┤
│  Page 1/12    [< Précédent]  [Suivant >]                         │
└─────────────────────────────────────────────────────────────────┘
```

### Page Statistiques

```
┌─────────────────────────────────────────────────────────────────────┐
│  Statistiques & Indicateurs          Période : [Ce mois ▾]          │
├──────────────┬──────────────┬──────────────┬────────────────────────┤
│ 12           │ 438          │ 67           │ 34,3 %                  │
│ Utilisateurs │ Recherches   │ Devis créés  │ Taux de conversion      │
│ actifs ↑ +2  │ ↓ -5%        │ ↑ +12%       │ ↑ +1,2 pt              │
├──────────────┴──────────────┴──────────────┴────────────────────────┤
│  Activité journalière                                                │
│  ▂▃▄▅▆▇█▇▆▅▄▅▆▇▆▅▄▃▄▅▆  ← courbe sur 30 jours                    │
├─────────────────────────────┬───────────────────────────────────────┤
│  Top 5 routes recherchées   │  Entonnoir devis                      │
│  Paris → Lyon      (87)     │  DRAFT    ████████████████  67        │
│  Lyon  → Marseille (54)     │  READY    ████████████      52        │
│  Paris → Bordeaux  (41)     │  SENT     ████████          35        │
│  Lille → Paris     (38)     │  ACCEPTED ████              23        │
│  Paris → Nantes    (29)     │  REJECTED ██                 9        │
├─────────────────────────────┼───────────────────────────────────────┤
│  Modes de transport         │  Activité par commercial               │
│  ROAD  ████████████  62%    │  j.martin   ██████████  24 devis      │
│  SEA   █████         22%    │  a.dupont   ████████    19 devis      │
│  AIR   ████          11%    │  m.leclerc  ████         9 devis      │
└─────────────────────────────┴───────────────────────────────────────┘
```

**Librairie de graphiques :** Recharts (léger, natif React)

### Modale d'export

```
        ┌──────────────────────────────────────────┐
        │  Exporter l'historique              [✕]  │
        │  ─────────────────────────────────────── │
        │  Format                                   │
        │  ( ) CSV   (•) PDF                        │
        │                                           │
        │  Période                                  │
        │  Du [23/01/2026]  Au [23/02/2026]         │
        │                                           │
        │  Filtres inclus                           │
        │  [x] Utilisateur : j.martin              │
        │  [x] Actions : toutes                     │
        │                                           │
        │  Contenu du PDF                           │
        │  [x] En-tête avec logo et période         │
        │  [x] Tableau des actions                  │
        │  [ ] Graphiques (activité journalière)    │
        │                                           │
        │  Estimation : ~342 lignes                 │
        │                                           │
        │        [Annuler]  [Télécharger]           │
        └──────────────────────────────────────────┘
```

**Export CSV :** colonnes `date_heure, utilisateur, role, action, ressource, ressource_id, details, ip`
**Export PDF :** via ReportLab (déjà dans le projet) avec en-tête logo + période + tableau paginé

---

## Interface — Alertes de sécurité

Badge rouge sur l'icône de notification dans la navbar, visible ADMIN/SUPER_ADMIN uniquement.

### Règles de déclenchement

| Type                | Règle                                                     |
| ------------------- | --------------------------------------------------------- |
| Échecs de connexion | ≥ 5 échecs sur un même login ou une même IP en 10 minutes |
| Activité suspecte   | ≥ 50 actions d'un même utilisateur en 5 minutes           |

### Navbar avec badge

```
┌─────────────────────────────────────────────────────────────────┐
│  Transport Quote    Recherche  Devis  Imports  Admin   🔔 ②  👤 │
└─────────────────────────────────────────────────────────────────┘
```

### Modale d'alertes

```
        ┌──────────────────────────────────────────────┐
        │  Alertes de sécurité                  [✕]   │
        │  ──────────────────────────────────────────  │
        │  🔴 Échecs de connexion        il y a 3 min  │
        │  "j.dupont" a échoué 8 fois en 10 minutes.   │
        │  IP source : 82.45.12.201                    │
        │  [Voir les détails]  [Désactiver le compte]  │
        │  ──────────────────────────────────────────  │
        │  🟠 Activité suspecte          il y a 12 min │
        │  "m.leclerc" a effectué 73 actions en 5 min. │
        │  [Voir les détails]  [Ignorer]               │
        │  ──────────────────────────────────────────  │
        │              [Tout marquer comme lu]         │
        └──────────────────────────────────────────────┘
```

### Implémentation technique

**Détection :** job Python toutes les 2 minutes

```python
# services/alert_service.py
def check_login_failures(db: Session) -> list:
    return db.execute("""
        SELECT details->>'attempted_login' AS login, ip_address, COUNT(*) AS failures
        FROM user_activity_logs
        WHERE action = 'auth.login_failed'
          AND created_at > NOW() - INTERVAL '10 minutes'
        GROUP BY login, ip_address
        HAVING COUNT(*) >= 5
    """).fetchall()
```

**Distribution :** endpoint SSE `GET /alerts/stream` — le frontend s'y abonne et reçoit les nouvelles alertes en temps réel.

---

## Plan d'implémentation

### Étape 1 — Base de données ✅
- [x] Créer `models/activity_log.py` et `models/security_alert.py`
- [x] Générer et appliquer la migration Alembic
- [x] Créer les vues SQL (`daily_activity`, `top_search_routes`, `quote_performance_by_user`, `login_failure_rate`)

> Appliquer la migration sur le serveur :
> ```bash
> docker compose run --rm backend alembic upgrade head
> ```

### Étape 2 — Service de logging ✅
- [x] Créer `services/activity_service.py` avec `log_activity()` et `purge_old_logs()`
- [x] Créer `services/alert_service.py` avec `check_login_failures()`, `check_suspicious_activity()`, `alert_check_loop()`, `daily_purge_loop()`

### Étape 3 — Intégration dans les routes ✅
- [x] `api/auth.py` : login succès/échec (avec raison), logout, changement de mot de passe
- [x] `api/matching.py` : recherches (critères + nombre de résultats)
- [x] `api/customer_quotes.py` : création, modification, changement de statut, suppression
- [x] `api/imports.py` : démarrage d'import (filename, partner, taille)
- [x] `api/users.py` : création, modification, changement de rôle, désactivation
- [x] `api/partners.py` : création, modification

### Étape 4 — Endpoints API ✅
- [x] `api/activity_logs.py` : GET liste paginnée, GET export CSV
- [x] `api/stats.py` : overview, activity, searches, quotes, imports, security
- [x] `api/alerts.py` : liste, SSE stream, PATCH seen, PATCH resolve
- [x] Enregistrer les nouveaux routers dans `main.py` et `api/__init__.py`
- [x] `main.py` migré vers le pattern `lifespan` (FastAPI 0.93+)

### Étape 5 — Frontend ✅
- [x] Service `activityService.ts` : getLogs, exportCsv, getOverview, dailyActivity, searchStats, quoteStats, securityStats, getAlerts, markSeen, resolveAlert
- [x] Page `ActivityLogs.tsx` avec tableau filtrable (login, action, date), couleurs par action, détails JSON expandable, pagination, export CSV
- [x] Page `Statistics.tsx` avec KPIs, top routes, activité par commercial, modes de transport, sécurité — sélecteur 7/30/90 jours
- [x] Composant `AlertBadge` dans la navbar avec badge rouge (non lus), panneau dropdown, actions Désactiver/Ignorer, rafraîchissement automatique 30s
- [x] Ajout des routes `/admin/activity` et `/admin/statistics` dans `App.tsx` (protégées ADMIN+)
- [x] Ajout des entrées **Historique** et **Statistiques** dans la navigation latérale (`Sidebar.tsx`)
- [x] `AlertBadge` intégré dans la navbar `Layout.tsx` (visible ADMIN et SUPER_ADMIN)

### Étape 6 — Jobs planifiés ✅
- [ ] Job de purge des logs à 1 an (quotidien)
- [ ] Job de détection des alertes (toutes les 2 minutes)

Les deux jobs sont des tâches asyncio démarrées via le `lifespan` de FastAPI (`@app.on_event` est déprécié depuis FastAPI 0.93) :

```python
# backend/app/main.py
import asyncio
from contextlib import asynccontextmanager
from app.core.database import SessionLocal

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage des jobs de fond au lancement de l'application
    asyncio.create_task(alert_check_loop())   # toutes les 2 minutes
    asyncio.create_task(daily_purge_loop())   # quotidien à minuit
    yield
    # Nettoyage éventuel à l'arrêt (ici non nécessaire)

app = FastAPI(lifespan=lifespan)
```

```python
# backend/app/services/alert_service.py
from app.core.database import SessionLocal
from app.models.security_alert import SecurityAlert

async def alert_check_loop():
    while True:
        await asyncio.sleep(120)  # 2 minutes
        db = SessionLocal()
        try:
            _process_login_failure_alerts(db)
            _process_suspicious_activity_alerts(db)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

def _process_login_failure_alerts(db: Session) -> None:
    """Crée une alerte pour chaque compte avec trop d'échecs récents,
    en évitant les doublons si une alerte non résolue existe déjà."""
    rows = db.execute(text("""
        SELECT details->>'attempted_login' AS login,
               ip_address,
               COUNT(*) AS failures
        FROM user_activity_logs
        WHERE action = 'auth.login_failed'
          AND created_at > NOW() - INTERVAL '10 minutes'
        GROUP BY details->>'attempted_login', ip_address
        HAVING COUNT(*) >= 5
    """)).fetchall()

    for row in rows:
        # Dédoublonnage : ne pas recréer une alerte non résolue existante
        already_exists = db.execute(text("""
            SELECT id FROM security_alerts
            WHERE type = 'login_failures'
              AND details->>'login' = :login
              AND resolved_at IS NULL
              AND created_at > NOW() - INTERVAL '30 minutes'
        """), {"login": row.login}).fetchone()

        if not already_exists:
            db.add(SecurityAlert(
                type="login_failures",
                severity="critical" if row.failures >= 10 else "medium",
                details={"login": row.login, "ip_address": row.ip_address, "failures": row.failures},
            ))

def _process_suspicious_activity_alerts(db: Session) -> None:
    """Crée une alerte si un utilisateur dépasse 50 actions en 5 minutes."""
    rows = db.execute(text("""
        SELECT user_id, user_login, COUNT(*) AS action_count
        FROM user_activity_logs
        WHERE created_at > NOW() - INTERVAL '5 minutes'
          AND user_id IS NOT NULL
        GROUP BY user_id, user_login
        HAVING COUNT(*) >= 50
    """)).fetchall()

    for row in rows:
        already_exists = db.execute(text("""
            SELECT id FROM security_alerts
            WHERE type = 'suspicious_activity'
              AND details->>'user_login' = :login
              AND resolved_at IS NULL
              AND created_at > NOW() - INTERVAL '30 minutes'
        """), {"login": row.user_login}).fetchone()

        if not already_exists:
            db.add(SecurityAlert(
                type="suspicious_activity",
                severity="medium",
                details={"user_login": row.user_login, "action_count": row.action_count},
            ))
```

```python
# backend/app/services/activity_service.py
async def daily_purge_loop():
    while True:
        now = datetime.now(timezone.utc)
        next_midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        await asyncio.sleep((next_midnight - now).total_seconds())
        db = SessionLocal()
        try:
            purge_old_logs(db)
        except Exception:
            db.rollback()
        finally:
            db.close()
```
