# Proposition : Amélioration du Modal de Recherche Transport

## Contexte

Le modal de recherche actuel (`SearchModal.tsx`) offre une expérience unique pour tous les utilisateurs. Cette proposition vise à différencier deux cas d'usage distincts pour améliorer l'ergonomie.

---

## 1. Analyse de l'Existant

### Composants actuels
- **SearchModal.tsx** : Modal de recherche avec formulaire complet (origine, destination, poids, volume, date)
- **Results.tsx** : Page de résultats avec bouton "Ajouter au devis" sur chaque offre
- **CustomerQuoteContext** : Gère l'état `isSearchModalOpen` et `selectedTransportMode`

### Points d'entrée actuels
1. **Sidebar** : Bouton "Recherche" → `openSearchModal()`
2. **CustomerQuoteEditor** : Bouton "+ Ajouter un transport" → `openSearchModalWithMode(mode)`

### Problèmes identifiés
- Pas de distinction entre recherche simple (consultation) et recherche pour devis
- L'utilisateur voit toujours "Ajouter au devis" même s'il veut juste consulter les tarifs
- Depuis la sidebar, l'utilisateur doit remplir tout le formulaire sans sélection préalable du mode

---

## 2. Cas d'Usage Cibles

### 2.1 Recherche Simple (Consultation)

**Objectif** : Consulter rapidement les tarifs disponibles sans intention d'ajouter à un devis.

**Workflow proposé** :
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  [Sidebar: Recherche]                                                       │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────┐                                │
│  │   ÉTAPE 1 : Sélection du Mode           │                                │
│  │                                         │                                │
│  │   Quel type de transport ?              │                                │
│  │                                         │                                │
│  │   ┌─────────┐  ┌─────────┐              │                                │
│  │   │ 🚚      │  │ 🚂      │              │                                │
│  │   │ Route   │  │ Rail    │              │                                │
│  │   └─────────┘  └─────────┘              │                                │
│  │                                         │                                │
│  │   ┌─────────┐  ┌─────────┐              │                                │
│  │   │ ✈️      │  │ 🚢      │              │                                │
│  │   │ Aérien  │  │ Maritime│              │                                │
│  │   └─────────┘  └─────────┘              │                                │
│  │                                         │                                │
│  │            [Annuler]                    │                                │
│  └─────────────────────────────────────────┘                                │
│         │                                                                   │
│         ▼ (clic sur un mode)                                                │
│  ┌─────────────────────────────────────────┐                                │
│  │   ÉTAPE 2 : Formulaire de Recherche     │                                │
│  │                                         │                                │
│  │   Mode: 🚚 Route                        │                                │
│  │   ─────────────────────                 │                                │
│  │   Origine: [...] Destination: [...]     │                                │
│  │   Poids: [...] Volume: [...]            │                                │
│  │   Date: [...]                           │                                │
│  │                                         │                                │
│  │   [← Retour]        [🔍 Rechercher]     │                                │
│  └─────────────────────────────────────────┘                                │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────┐                                │
│  │   PAGE RÉSULTATS (Mode Consultation)    │                                │
│  │                                         │                                │
│  │   ┌─────────────────────────────────┐   │                                │
│  │   │ Transporteur A    150 €         │   │  ← Pas de bouton "Ajouter"     │
│  │   │ Transit: 48h                    │   │                                │
│  │   └─────────────────────────────────┘   │                                │
│  │                                         │                                │
│  │   ┌─────────────────────────────────┐   │                                │
│  │   │ Transporteur B    180 €         │   │                                │
│  │   │ Transit: 24h                    │   │                                │
│  │   └─────────────────────────────────┘   │                                │
│  │                                         │                                │
│  │   [← Nouvelle recherche]                │                                │
│  └─────────────────────────────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Caractéristiques** :
- Modal intermédiaire pour sélectionner le mode de transport
- Formulaire de recherche pré-filtré par mode
- Page résultats **SANS** bouton "Ajouter au devis"
- Objectif : consultation pure

---

### 2.2 Recherche pour Devis

**Objectif** : Ajouter un transport à un devis existant.

**Workflow proposé** :
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  [CustomerQuoteEditor: + Ajouter un transport (mode déjà sélectionné)]      │
│         │                                                                   │
│         ▼ (pas d'étape intermédiaire)                                       │
│  ┌─────────────────────────────────────────┐                                │
│  │   FORMULAIRE DE RECHERCHE               │                                │
│  │                                         │                                │
│  │   Mode: 🚚 Route (pré-sélectionné)      │                                │
│  │   ─────────────────────                 │                                │
│  │   Origine: [...] Destination: [...]     │                                │
│  │   Poids: [...] Volume: [...]            │                                │
│  │   Date: [...]                           │                                │
│  │                                         │                                │
│  │   [Annuler]         [🔍 Rechercher]     │                                │
│  └─────────────────────────────────────────┘                                │
│         │                                                                   │
│         ▼                                                                   │
│  ┌─────────────────────────────────────────┐                                │
│  │   PAGE RÉSULTATS (Mode Devis)           │                                │
│  │                                         │                                │
│  │   Devis: DEV-2024-0042 (Jean Dupont)    │  ← Bandeau rappel devis        │
│  │                                         │                                │
│  │   ┌─────────────────────────────────┐   │                                │
│  │   │ Transporteur A    150 €         │   │                                │
│  │   │ Transit: 48h                    │   │                                │
│  │   │           [➕ Ajouter au devis] │   │  ← Bouton visible              │
│  │   └─────────────────────────────────┘   │                                │
│  │                                         │                                │
│  │   ┌─────────────────────────────────┐   │                                │
│  │   │ Transporteur B    180 €  ✓ Ajouté│  │                                │
│  │   │ Transit: 24h                    │   │                                │
│  │   │           [🗑️ Retirer]          │   │  ← Si déjà ajouté              │
│  │   └─────────────────────────────────┘   │                                │
│  │                                         │                                │
│  │   [← Retour au devis]                   │                                │
│  └─────────────────────────────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Caractéristiques** :
- Pas d'étape intermédiaire (mode déjà sélectionné dans l'éditeur)
- Page résultats **AVEC** bouton "Ajouter au devis"
- Bandeau rappelant le devis en cours
- Possibilité de retirer un item déjà ajouté

---

## 3. Architecture Technique Proposée

### 3.1 Nouveau State dans le Context

```typescript
// CustomerQuoteContext.tsx

interface CustomerQuoteContextType {
    // ... existant ...

    // Nouveau : Mode de recherche
    searchMode: 'consultation' | 'quote' | null;
    setSearchMode: (mode: 'consultation' | 'quote' | null) => void;

    // Nouveau : Ouvrir la recherche en mode consultation
    openSearchForConsultation: () => void;

    // Existant mais renommé pour clarté
    openSearchForQuote: (mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA') => void;
}
```

### 3.2 Nouveaux Composants

```
src/components/
├── search/
│   ├── TransportModeSelector.tsx    # Nouveau : Modal sélection du mode
│   ├── SearchFormModal.tsx          # Renommé depuis SearchModal.tsx
│   └── index.ts
```

#### TransportModeSelector.tsx (Nouveau)
```typescript
interface TransportModeSelectorProps {
    isOpen: boolean;
    onClose: () => void;
    onSelectMode: (mode: 'ROAD' | 'RAIL' | 'AIR' | 'SEA') => void;
}

export const TransportModeSelector: React.FC<TransportModeSelectorProps> = ({
    isOpen,
    onClose,
    onSelectMode
}) => {
    const modes = [
        { value: 'ROAD', label: 'Route', icon: <Truck />, description: 'Transport routier' },
        { value: 'RAIL', label: 'Rail', icon: <Train />, description: 'Transport ferroviaire' },
        { value: 'AIR', label: 'Aérien', icon: <Plane />, description: 'Fret aérien' },
        { value: 'SEA', label: 'Maritime', icon: <Ship />, description: 'Fret maritime' }
    ];

    return (
        <Modal isOpen={isOpen} onClose={onClose} title="Quel type de transport ?">
            <div className="grid grid-cols-2 gap-4 p-6">
                {modes.map(mode => (
                    <button
                        key={mode.value}
                        onClick={() => onSelectMode(mode.value)}
                        className="flex flex-col items-center p-6 border rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all"
                    >
                        <div className="text-3xl mb-2">{mode.icon}</div>
                        <div className="font-semibold">{mode.label}</div>
                        <div className="text-sm text-gray-500">{mode.description}</div>
                    </button>
                ))}
            </div>
        </Modal>
    );
};
```

### 3.3 Modification de Results.tsx

```typescript
// Results.tsx

export const Results: React.FC = () => {
    const location = useLocation();
    const state = location.state as LocationState;
    const { searchMode, currentQuote } = useCustomerQuote();

    // Déterminer si on affiche les actions devis
    const isQuoteMode = searchMode === 'quote' && currentQuote !== null;

    return (
        <div>
            {/* Bandeau devis si mode quote */}
            {isQuoteMode && (
                <div className="bg-blue-50 border-b border-blue-200 px-6 py-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-600" />
                        <span className="font-medium">Devis en cours : {currentQuote.reference}</span>
                        <span className="text-gray-500">({currentQuote.customer_name || 'Sans client'})</span>
                    </div>
                    <Link to={`/customer-quotes/${currentQuote.id}/edit`} className="text-blue-600 hover:underline">
                        Retour au devis
                    </Link>
                </div>
            )}

            {/* Liste des résultats */}
            {results.map(quote => (
                <ResultCard
                    key={quote.id}
                    quote={quote}
                    showQuoteActions={isQuoteMode}  // Nouveau prop
                />
            ))}
        </div>
    );
};
```

### 3.4 Flow Complet

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  POINT D'ENTRÉE 1: Sidebar "Recherche"                                       │
│  ─────────────────────────────────────                                       │
│                                                                              │
│  1. Clic sur "Recherche"                                                     │
│  2. setSearchMode('consultation')                                            │
│  3. Afficher TransportModeSelector                                           │
│  4. Utilisateur sélectionne un mode                                          │
│  5. setSelectedTransportMode(mode)                                           │
│  6. Afficher SearchFormModal                                                 │
│  7. Soumettre → Navigate /results                                            │
│  8. Results.tsx détecte searchMode='consultation' → pas de boutons devis     │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  POINT D'ENTRÉE 2: CustomerQuoteEditor "+ Ajouter un transport"              │
│  ──────────────────────────────────────────────────────────────              │
│                                                                              │
│  1. Clic sur "+ Ajouter un transport" (mode déjà sélectionné)                │
│  2. setSearchMode('quote')                                                   │
│  3. setSelectedTransportMode(selectedMode)                                   │
│  4. Afficher SearchFormModal directement (skip TransportModeSelector)        │
│  5. Soumettre → Navigate /results                                            │
│  6. Results.tsx détecte searchMode='quote' → affiche boutons devis           │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Options d'Implémentation

### Option A : Deux Modals Séparés (Recommandée)

**Principe** : Créer un nouveau composant `TransportModeSelector` qui s'affiche avant `SearchFormModal` en mode consultation.

**Avantages** :
- Séparation claire des responsabilités
- Code plus maintenable
- Réutilisable (le sélecteur de mode peut servir ailleurs)

**Inconvénients** :
- Deux modals à gérer
- Légère complexité additionnelle dans le context

**Estimation** : ~6-8h

---

### Option B : Modal Unique avec Étapes

**Principe** : Un seul modal `SearchModal` avec un state interne `step: 'mode' | 'form'`.

```typescript
const SearchModal: React.FC = () => {
    const { searchMode } = useCustomerQuote();
    const [step, setStep] = useState<'mode' | 'form'>(
        searchMode === 'consultation' ? 'mode' : 'form'
    );

    if (!isOpen) return null;

    return (
        <Modal>
            {step === 'mode' ? (
                <ModeSelectionStep onSelect={(mode) => {
                    setSelectedMode(mode);
                    setStep('form');
                }} />
            ) : (
                <SearchFormStep onBack={() => setStep('mode')} />
            )}
        </Modal>
    );
};
```

**Avantages** :
- Un seul composant à maintenir
- Transition fluide entre étapes

**Inconvénients** :
- Logique plus complexe dans un seul fichier
- Moins de flexibilité pour réutilisation

**Estimation** : ~5-6h

---

### Option C : Page Intermédiaire (Alternative)

**Principe** : Au lieu d'un modal, rediriger vers une page `/search/select-mode` puis `/search`.

**Avantages** :
- Navigation classique avec URL
- Historique navigateur fonctionne naturellement

**Inconvénients** :
- Rompt avec l'approche modal actuelle
- Plus de changements nécessaires
- Moins fluide pour l'utilisateur

**Estimation** : ~8-10h

---

## 5. Recommandation

**Option A : Deux Modals Séparés** est recommandée car :

1. **Clarté du code** : Chaque composant a une responsabilité unique
2. **Flexibilité** : Le sélecteur de mode peut être réutilisé ailleurs
3. **Cohérence** : Garde l'approche modal existante
4. **Maintenabilité** : Facile à faire évoluer indépendamment

---

## 6. Fichiers à Modifier/Créer

### Nouveaux fichiers
| Fichier | Description |
|---------|-------------|
| `src/components/search/TransportModeSelector.tsx` | Modal de sélection du mode |
| `src/components/search/index.ts` | Export des composants |

### Fichiers à modifier
| Fichier | Modifications |
|---------|---------------|
| `src/context/CustomerQuoteContext.tsx` | Ajouter `searchMode`, `openSearchForConsultation()` |
| `src/components/SearchModal.tsx` | Renommer en `SearchFormModal.tsx`, adapter logique |
| `src/pages/Results.tsx` | Conditionner affichage boutons selon `searchMode` |
| `src/components/layout/Sidebar.tsx` | Appeler `openSearchForConsultation()` |
| `src/components/layout/Layout.tsx` | Ajouter `TransportModeSelector` dans le render |

---

## 7. Maquettes Détaillées

### 7.1 Modal Sélection du Mode (Consultation)

```
┌──────────────────────────────────────────────────────────────┐
│                                                        [X]   │
│                                                              │
│              Quel type de transport recherchez-vous ?        │
│                                                              │
│    ┌─────────────────────┐    ┌─────────────────────┐        │
│    │                     │    │                     │        │
│    │        🚚           │    │        🚂           │        │
│    │                     │    │                     │        │
│    │       Route         │    │        Rail         │        │
│    │   Transport routier │    │ Transport ferroviaire│       │
│    │                     │    │                     │        │
│    └─────────────────────┘    └─────────────────────┘        │
│                                                              │
│    ┌─────────────────────┐    ┌─────────────────────┐        │
│    │                     │    │                     │        │
│    │        ✈️           │    │        🚢           │        │
│    │                     │    │                     │        │
│    │       Aérien        │    │      Maritime       │        │
│    │     Fret aérien     │    │    Fret maritime    │        │
│    │                     │    │                     │        │
│    └─────────────────────┘    └─────────────────────┘        │
│                                                              │
│                        [Annuler]                             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 7.2 Formulaire de Recherche (après sélection mode)

```
┌──────────────────────────────────────────────────────────────┐
│  Rechercher un transport                               [X]   │
│  ─────────────────────────                                   │
│  Mode : 🚚 Route                    [← Changer de mode]      │
│                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐    │
│  │  📍 Origine             │  │  📍 Destination         │    │
│  │  ─────────────────────  │  │  ─────────────────────  │    │
│  │  Pays: [France     ▼]   │  │  Pays: [France     ▼]   │    │
│  │  Code Postal: [     ]   │  │  Code Postal: [     ]   │    │
│  │  Ville: [           ]   │  │  Ville: [           ]   │    │
│  └─────────────────────────┘  └─────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────┐  ┌─────────────────────────┐    │
│  │  📦 Marchandise         │  │  📅 Date                │    │
│  │  ─────────────────────  │  │  ─────────────────────  │    │
│  │  Poids (kg): [    ]     │  │  Date: [          ]     │    │
│  │  Volume (m³): [   ]     │  │                         │    │
│  └─────────────────────────┘  └─────────────────────────┘    │
│                                                              │
│         [Annuler]                    [🔍 Rechercher]         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 7.3 Page Résultats - Mode Consultation

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  [← Nouvelle recherche]                                                      │
│                                                                              │
│  3 offres correspondantes                                                    │
│  Paris, 75001, France → Lyon, 69000, France | 500 kg                         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  🚚  Transporteur Express                                              │  │
│  │      ROAD | 100-1000 kg                                                │  │
│  │                                                                        │  │
│  │      ⏱️ Transit: 24h    📅 Validité: illimitée                         │  │
│  │                                                                        │  │
│  │                                              Prix estimé               │  │
│  │                                                 150 €                  │  │
│  │                                                                        │  │
│  │      ← Pas de bouton "Ajouter" en mode consultation                    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  🚚  Trans Rapide                                                      │  │
│  │      ROAD | 50-500 kg                                                  │  │
│  │                                                                        │  │
│  │      ⏱️ Transit: 48h    📅 Validité: 31/12/2024                        │  │
│  │                                                                        │  │
│  │                                              Prix estimé               │  │
│  │                                                 120 €                  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 7.4 Page Résultats - Mode Devis

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  📄 Devis en cours : DEV-2024-0042 (Jean Dupont)    [Retour au devis →]│  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  [← Retour au devis]                                                         │
│                                                                              │
│  3 offres correspondantes                                                    │
│  Paris, 75001, France → Lyon, 69000, France | 500 kg                         │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  🚚  Transporteur Express                                              │  │
│  │      ROAD | 100-1000 kg                                                │  │
│  │                                                                        │  │
│  │      ⏱️ Transit: 24h    📅 Validité: illimitée                         │  │
│  │                                                                        │  │
│  │                                              Prix estimé               │  │
│  │                                                 150 €                  │  │
│  │                                                                        │  │
│  │                                       [➕ Ajouter au devis]            │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────── ✓ Ajouté ──┐  │
│  │  🟢  Trans Rapide                                                      │  │
│  │      ROAD | 50-500 kg                                                  │  │
│  │                                                                        │  │
│  │      ⏱️ Transit: 48h    📅 Validité: 31/12/2024                        │  │
│  │                                                                        │  │
│  │                                              Prix estimé               │  │
│  │                                                 120 €                  │  │
│  │                                                                        │  │
│  │                                            [🗑️ Retirer]                │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Estimation

| Tâche | Durée |
|-------|-------|
| Modifier CustomerQuoteContext (searchMode, nouvelles fonctions) | 1h |
| Créer TransportModeSelector.tsx | 2h |
| Modifier SearchModal → SearchFormModal | 1h |
| Modifier Results.tsx (conditionner boutons, bandeau) | 2h |
| Modifier Sidebar.tsx et Layout.tsx | 0.5h |
| Tests et ajustements | 1.5h |
| **Total** | **~8h** |

---

## 9. Questions Ouvertes

1. **Bouton "Changer de mode"** : En mode consultation, faut-il pouvoir revenir à la sélection du mode depuis le formulaire de recherche ?
   - Option A : Oui, bouton "← Changer de mode"
   - Option B : Non, il faut fermer et rouvrir

2. **Persistance du mode** : En mode consultation, si l'utilisateur fait plusieurs recherches, doit-on mémoriser son dernier mode sélectionné ?
   - Option A : Oui, garder en mémoire (localStorage ou state)
   - Option B : Non, toujours redemander

3. **Accès rapide depuis résultats** : En mode consultation, faut-il proposer un bouton pour "passer en mode devis" directement depuis les résultats ?
   - Option A : Oui, bouton "Créer un devis avec ces résultats"
   - Option B : Non, l'utilisateur doit aller dans "Mes Devis" puis rechercher

---

## 10. Prochaines Étapes

1. Valider l'option d'implémentation (A, B ou C)
2. Répondre aux questions ouvertes
3. Procéder à l'implémentation
