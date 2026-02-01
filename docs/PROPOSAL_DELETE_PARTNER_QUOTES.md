# Proposition : Suppression des tarifs d'un partenaire

## Contexte

Permettre à l'administrateur de supprimer tous les tarifs associés à un partenaire donné.

---

## 1. Propositions Techniques (Backend)

### Option A : Endpoint dédié (Recommandé)

```
DELETE /api/v1/partners/{partner_id}/quotes
```

**Avantages :**
- URL RESTful claire
- Intention explicite
- Facile à documenter

**Implémentation :**
```python
# app/api/v1/partners.py
@router.delete("/{partner_id}/quotes", status_code=204)
def delete_partner_quotes(partner_id: str, db: Session = Depends(get_db)):
    count = QuoteService.delete_all_by_partner(db, partner_id)
    return {"deleted_count": count}
```

---

### Option B : Paramètre sur l'endpoint quotes

```
DELETE /api/v1/quotes?partner_id={partner_id}
```

**Avantages :**
- Réutilise l'endpoint existant
- Cohérent avec les filtres de lecture

**Inconvénients :**
- Risque de suppression accidentelle sans paramètre
- Moins explicite

---

### Option C : Action bulk dans le body

```
POST /api/v1/quotes/bulk-delete
Body: { "partner_id": "xxx" }
```

**Avantages :**
- Extensible (peut ajouter d'autres critères)
- Body permet plus de flexibilité

**Inconvénients :**
- POST pour une suppression (non RESTful)

---

## 2. Propositions Interface (Frontend)

### Option A : Bouton dans la page Partenaires (Recommandé)

Ajouter un bouton "Supprimer tarifs" dans les actions de chaque ligne du tableau.

```
┌─────────────────────────────────────────────────────────────┐
│ Partenaires                                                 │
├──────┬──────────────┬─────────────────┬────────────────────┤
│ Code │ Nom          │ Email           │ Actions            │
├──────┼──────────────┼─────────────────┼────────────────────┤
│ DHL  │ DHL Express  │ dhl@example.com │ ✏️  🗑️  📦❌        │
└──────┴──────────────┴─────────────────┴────────────────────┘
                                              │
                                              └── Nouveau bouton
                                                  "Supprimer tarifs"
```

**Flow :**
1. Clic sur l'icône
2. Modal de confirmation avec nombre de tarifs
3. Confirmation → Suppression → Toast de succès

---

### Option B : Bouton dans la page Tarifs (filtré)

Quand un partenaire est sélectionné dans le filtre, afficher un bouton "Supprimer tous".

```
┌─────────────────────────────────────────────────────────────┐
│ Tarifs                                                      │
├─────────────────────────────────────────────────────────────┤
│ Filtre: [DHL Express ▼]  [Tous les modes ▼]                 │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ⚠️ 1,620 tarifs pour DHL Express                        │ │
│ │                              [Supprimer tous les tarifs]│ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Avantages :**
- Contexte clair (on voit les tarifs avant de supprimer)
- Cohérent avec la page

---

### Option C : Page dédiée "Gestion des données"

Créer une page d'administration avec des actions bulk.

```
┌─────────────────────────────────────────────────────────────┐
│ Gestion des données                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Supprimer les tarifs d'un partenaire                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Partenaire: [Sélectionner ▼]                            │ │
│ │                                                         │ │
│ │ Tarifs actuels: 1,620                                   │ │
│ │                                                         │ │
│ │                              [Supprimer]                │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Purger tous les tarifs expirés                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Tarifs expirés: 45                                      │ │
│ │                              [Purger]                   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Avantages :**
- Centralise les actions d'administration
- Extensible

**Inconvénients :**
- Plus de travail
- Navigation supplémentaire

---

## 3. Recommandation

| Composant | Recommandation |
|-----------|----------------|
| **Backend** | Option A : `DELETE /api/v1/partners/{id}/quotes` |
| **Frontend** | Option A : Bouton dans la page Partenaires |

### Raisons :
1. **Simple** : Moins de code, rapide à implémenter
2. **Intuitif** : L'action est proche du partenaire concerné
3. **Sécurisé** : Modal de confirmation obligatoire

---

## 4. Sécurité

- [ ] Modal de confirmation avec saisie du nom du partenaire
- [ ] Afficher le nombre de tarifs avant suppression
- [ ] Log de l'action (audit trail)
- [ ] Possibilité de limiter aux admins (futur)

---

## 5. Estimation

| Tâche | Effort |
|-------|--------|
| Endpoint backend | ~15 min |
| Service frontend | ~10 min |
| UI + Modal | ~30 min |
| Tests | ~20 min |
| **Total** | **~1h15** |

---

## Décision

Quelle option choisissez-vous ?

- [ ] Backend : Option A / B / C
- [ ] Frontend : Option A / B / C
