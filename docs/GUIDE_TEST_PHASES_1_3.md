# Guide de Test - Phases 1 à 3

Ce guide décrit comment tester les fonctionnalités implémentées dans les phases 1 à 3.

---

## 1. Démarrage de l'environnement

### 1.1 Prérequis

- Docker et Docker Compose installés
- Python 3.12+ (pour le développement local)

### 1.2 Démarrage avec Docker

```bash
# Depuis la racine du projet
cd /Users/tiengd/Documents/tuto/transport_quote

# Démarrer PostgreSQL et Redis
docker-compose up -d postgres redis

# Vérifier que les conteneurs tournent
docker-compose ps
```

### 1.3 Démarrage du Backend (développement)

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou: venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env
cp .env.example .env

# Exécuter les migrations
alembic upgrade head

# Lancer le serveur
uvicorn app.main:app --reload --port 3000
```

### 1.4 Vérification

```bash
# Health check
curl http://localhost:3000/health

# Réponse attendue:
# {"status":"healthy"}
```

---

## 2. Documentation API Interactive

Une fois le serveur lancé, accédez à :

- **Swagger UI** : http://localhost:3000/docs
- **ReDoc** : http://localhost:3000/redoc

---

## 3. Tests Phase 2 : API Partenaires

### 3.1 Créer un partenaire

```bash
curl -X POST http://localhost:3000/api/v1/partners \
  -H "Content-Type: application/json" \
  -d '{
    "code": "BESSON",
    "name": "Transport Besson",
    "email": "contact@besson.fr"
  }'
```

**Réponse attendue :**
```json
{
  "id": "uuid-généré",
  "code": "BESSON",
  "name": "Transport Besson",
  "email": "contact@besson.fr",
  "rating": 0.0,
  "is_active": true,
  "created_at": "2026-01-24T...",
  "updated_at": "2026-01-24T..."
}
```

### 3.2 Lister les partenaires

```bash
curl http://localhost:3000/api/v1/partners
```

### 3.3 Récupérer un partenaire

```bash
curl http://localhost:3000/api/v1/partners/{id}
```

### 3.4 Modifier un partenaire

```bash
curl -X PUT http://localhost:3000/api/v1/partners/{id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Transport Besson SARL",
    "rating": 4.5
  }'
```

### 3.5 Supprimer un partenaire

```bash
curl -X DELETE http://localhost:3000/api/v1/partners/{id}
```

---

## 4. Tests Phase 2 : API Tarifs (Quotes)

### 4.1 Créer un tarif manuellement

```bash
curl -X POST http://localhost:3000/api/v1/quotes \
  -H "Content-Type: application/json" \
  -d '{
    "partner_id": "{id-partenaire}",
    "transport_mode": "ROAD",
    "origin_city": "Paris",
    "origin_country": "FR",
    "dest_city": "Lyon",
    "dest_country": "FR",
    "weight_min": 0,
    "weight_max": 1000,
    "cost": 150.00,
    "currency": "EUR",
    "delivery_time": "24h"
  }'
```

### 4.2 Lister les tarifs

```bash
# Tous les tarifs
curl http://localhost:3000/api/v1/quotes

# Filtrer par partenaire
curl "http://localhost:3000/api/v1/quotes?partner_id={id}"

# Filtrer par mode de transport
curl "http://localhost:3000/api/v1/quotes?transport_mode=ROAD"
```

### 4.3 Récupérer un tarif

```bash
curl http://localhost:3000/api/v1/quotes/{id}
```

### 4.4 Supprimer un tarif

```bash
curl -X DELETE http://localhost:3000/api/v1/quotes/{id}
```

---

## 5. Tests Phase 3 : Import de fichiers

### 5.1 Préparer un fichier de test CSV

Créer un fichier `test_tarifs.csv` :

```csv
mode,origine,pays_origine,destination,pays_dest,poids_min,poids_max,prix,delai
ROAD,Paris,FR,Lyon,FR,0,500,120.50,24h
ROAD,Paris,FR,Marseille,FR,0,500,180.00,48h
ROAD,Lyon,FR,Bordeaux,FR,0,1000,220.00,48h
RAIL,Paris,FR,Milan,IT,0,5000,350.00,72h
```

### 5.2 Uploader le fichier

```bash
curl -X POST http://localhost:3000/api/v1/imports \
  -F "partner_id={id-partenaire}" \
  -F "file=@test_tarifs.csv"
```

**Réponse attendue :**
```json
{
  "id": "job-uuid",
  "partner_id": "{id-partenaire}",
  "filename": "test_tarifs.csv",
  "file_type": "CSV",
  "status": "PENDING",
  "total_rows": 0,
  "success_count": 0,
  "error_count": 0,
  "errors": null,
  "created_at": "2026-01-24T...",
  "completed_at": null
}
```

### 5.3 Vérifier le statut de l'import

```bash
curl http://localhost:3000/api/v1/imports/{job-id}
```

**Après traitement :**
```json
{
  "id": "job-uuid",
  "status": "COMPLETED",
  "total_rows": 4,
  "success_count": 4,
  "error_count": 0,
  "errors": []
}
```

### 5.4 Vérifier les tarifs importés

```bash
curl "http://localhost:3000/api/v1/quotes?partner_id={id-partenaire}"
```

---

## 6. Test avec fichier Excel

### 6.1 Préparer un fichier Excel

Créer un fichier `test_tarifs.xlsx` avec les colonnes :

| mode | origine | pays_origine | destination | pays_dest | poids_min | poids_max | prix | delai |
|------|---------|--------------|-------------|-----------|-----------|-----------|------|-------|
| ROAD | Paris | FR | Brussels | BE | 0 | 500 | 150.00 | 48h |
| AIR | Paris | FR | London | GB | 0 | 100 | 280.00 | 24h |

### 6.2 Uploader le fichier Excel

```bash
curl -X POST http://localhost:3000/api/v1/imports \
  -F "partner_id={id-partenaire}" \
  -F "file=@test_tarifs.xlsx"
```

---

## 7. Scénario de test complet

```bash
#!/bin/bash
# Script de test complet

BASE_URL="http://localhost:3000/api/v1"

echo "=== 1. Création du partenaire ==="
PARTNER=$(curl -s -X POST $BASE_URL/partners \
  -H "Content-Type: application/json" \
  -d '{"code":"TEST001","name":"Test Transport","email":"test@example.com"}')
PARTNER_ID=$(echo $PARTNER | jq -r '.id')
echo "Partenaire créé: $PARTNER_ID"

echo ""
echo "=== 2. Création d'un tarif manuel ==="
QUOTE=$(curl -s -X POST $BASE_URL/quotes \
  -H "Content-Type: application/json" \
  -d "{
    \"partner_id\": \"$PARTNER_ID\",
    \"transport_mode\": \"ROAD\",
    \"origin_city\": \"Paris\",
    \"origin_country\": \"FR\",
    \"dest_city\": \"Lyon\",
    \"dest_country\": \"FR\",
    \"cost\": 100.00
  }")
QUOTE_ID=$(echo $QUOTE | jq -r '.id')
echo "Tarif créé: $QUOTE_ID"

echo ""
echo "=== 3. Liste des tarifs ==="
curl -s "$BASE_URL/quotes?partner_id=$PARTNER_ID" | jq '.[] | {id, origin_city, dest_city, cost}'

echo ""
echo "=== 4. Import d'un fichier CSV ==="
# Créer le fichier de test
cat > /tmp/test_import.csv << 'EOF'
mode,origine,pays_origine,destination,pays_dest,prix,delai
ROAD,Marseille,FR,Nice,FR,80.00,12h
ROAD,Lyon,FR,Grenoble,FR,60.00,6h
EOF

JOB=$(curl -s -X POST $BASE_URL/imports \
  -F "partner_id=$PARTNER_ID" \
  -F "file=@/tmp/test_import.csv")
JOB_ID=$(echo $JOB | jq -r '.id')
echo "Job créé: $JOB_ID"

echo ""
echo "=== 5. Statut de l'import ==="
sleep 2  # Attendre le traitement
curl -s "$BASE_URL/imports/$JOB_ID" | jq '{status, total_rows, success_count, error_count}'

echo ""
echo "=== 6. Vérification des tarifs importés ==="
curl -s "$BASE_URL/quotes?partner_id=$PARTNER_ID" | jq 'length'
echo "tarifs au total"

echo ""
echo "=== Tests terminés ==="
```

---

## 8. Erreurs courantes

### 8.1 Partenaire non trouvé

```json
{"detail": "Partenaire non trouvé"}
```
→ Vérifier que le `partner_id` existe

### 8.2 Code partenaire dupliqué

```json
{"detail": "Un partenaire avec le code 'XXX' existe déjà."}
```
→ Utiliser un code unique

### 8.3 Format de fichier non supporté

```json
{"detail": "Format non supporté: DOC"}
```
→ Utiliser CSV, XLSX ou PDF

### 8.4 Erreurs de validation lors de l'import

```json
{
  "status": "COMPLETED",
  "success_count": 2,
  "error_count": 1,
  "errors": [
    {
      "row": 3,
      "errors": [{"field": "cost", "message": "Le prix est obligatoire"}],
      "raw": {...}
    }
  ]
}
```
→ Vérifier les données du fichier source

---

## 9. Nettoyage

```bash
# Supprimer les données de test
curl -X DELETE http://localhost:3000/api/v1/partners/{id}

# Arrêter les conteneurs
docker-compose down
```
