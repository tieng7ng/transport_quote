# Proposition : Moteur de Prix (Marges & Frais)

Pour répondre au besoin d'ajouter des frais et des marges sur les tarifs partenaires (qui sont des *prix d'achat*), voici 3 approches possibles, de la plus simple à la plus complète.

---

## Option 1 : Approche "Coefficient Global" (La plus simple)

Appliquer une marge unique par défaut sur tous les devis.

*   **Principe** : `Prix Vente = Prix Achat Partenaire * 1.20` (Marge 20%)
*   **Gestion** : Un paramètre global "Marge par défaut" dans la configuration.
*   **Avantages** : Très rapide à mettre en place.
*   **Inconvénients** : Pas de flexibilité (ex: un petit colis nécessite plus de marge % qu'un camion complet).

## Option 2 : Approche "Flexible" (Recommandée) ⭐

Donner la main à l'opérateur pour ajuster chaque ligne avant l'envoi du devis.

*   **Principe** : Le système propose un prix public, mais l'opérateur peut le surcharger.
*   **Fonctionnalités** :
    1.  **Marge par défaut** définie par *Partenaire* (ex: Besson +15%, XPO +10%).
    2.  **Ajout de lignes de frais** manuelles (ex: "Frais de dossier", "Urgence", "Assurance").
    3.  **Édition du prix final** : L'opérateur voit le prix d'achat, saisit sa marge, et le système calcule le prix de vente.
*   **Interface (UI)** :
    *   Nouvel écran "Constructeur de Devis" avant la génération du PDF.
    *   Tableau éditable : `[Description] [Prix Achat] [Marge %] [Prix Vente]`.

## Option 3 : Approche "Règles Métier" (Avancée)

Automatisation complète basée sur des critères complexes.

*   **Principe** : Moteur de règles "Si... Alors...".
*   **Exemples** :
    *   *Si* client = "VIP", *Alors* Marge = 10%.
    *   *Si* Zone = "Montagne", *Alors* Ajouter Frais "Accès difficile" (50€).
    *   *Si* Poids < 100kg, *Alors* Forfait minimum 30€.
*   **Avantages** : Puissant et sans intervention humaine.
*   **Inconvénients** : Très lourd à développer et à maintenir (usine à gaz).

---

## Recommandation Technique (Option 2)

Je suggère d'implémenter l'**Option 2** qui offre le meilleur équilibre pour votre stade de projet.

### Impact sur le Modèle de Données (`GeneratedQuote`)

Il faut transformer l'objet `GeneratedQuote` pour qu'il ne soit plus une simple copie du `PartnerQuote`.

```python
class QuoteItem(Base):
    # ...
    description = Column(String)      # ex: "Transport Paris->Lyon"
    cost_price = Column(Float)        # Prix d'achat (Partenaire)
    sell_price = Column(Float)        # Prix de vente (Client)
    margin_amount = Column(Float)     # Bénéfice (Calculé)
    type = "TRANSPORT" | "FEE"        # Type de ligne
```

### Impact sur le Flux Utilisateur

1.  **Recherche** : Le système affiche les offres avec une marge indicative (+15%).
2.  **Sélection** : L'opérateur choisit une offre.
3.  **Édition (Nouveau)** :
    *   Écran récapitulatif.
    *   Bouton "Ajouter des frais" (ex: +50€ Assurance).
    *   Champ "Marge" modifiable (passe de 15% à 20% en un clic).
4.  **Validation** : Génération du PDF avec uniquement les prix de vente.
