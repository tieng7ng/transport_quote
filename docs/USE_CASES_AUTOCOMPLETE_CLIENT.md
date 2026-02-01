# Use Cases : Gestion & Autocomplete Client

Ce document définit les cas d'usage (Use Cases) pour l'implémentation de la fonctionnalité de gestion et recherche de clients dans l'éditeur de devis. Il sert de référence pour le développement et la validation.

---

## 👥 Acteurs
*   **Utilisateur** : Gestionnaire de transport qui crée ou édite des devis.
*   **Système** : L'application Transport Quote.

---

## 📋 Liste des Cas d'Usage
1.  [UC-01] Rechercher et sélectionner un client existant
2.  [UC-02] Créer un nouveau client à la volée
3.  [UC-03] Modifier les informations client d'un devis (Snapshot vs Master)
4.  [UC-04] Remplacer le client d'un devis
5.  [UC-05] Validation des données client avant finalisation

---

## 🔍 Détail des Scénarios

### [UC-01] Rechercher et sélectionner un client existant

**Objectif** : Associer rapidement un client connu à un devis sans ressaisir ses informations.

*   **Pré-conditions** : L'utilisateur est sur l'écran "Éditeur de Devis". Des clients existent en base.
*   **Scénario Nominal** :
    1.  L'utilisateur clique sur la zone de recherche "Rechercher un client".
    2.  Il saisit les premières lettres (ex: "ABC") ou un SIRET.
    3.  Le système affiche une liste déroulante des clients correspondants (Nom, Ville, Code).
    4.  L'utilisateur sélectionne "ABC Logistique (CLI-123)".
    5.  Le système :
        *   Associe l'ID du client au devis.
        *   Copie les informations (Nom, Société, Email, Délai de paiement) dans les champs du devis (Snapshot).
        *   Clôt la recherche et affiche la "Carte Client" résumée.

*   **Variante** :
    *   *Aucun résultat* : Le système affiche "Aucun résultat trouvé" et propose l'action [UC-02].

---

### [UC-02] Créer un nouveau client à la volée

**Objectif** : Créer une fiche client pérenne sans quitter le flux de création de devis.

*   **Pré-conditions** : L'utilisateur est dans l'outil de recherche de l'éditeur. Le client n'existe pas encore.
*   **Scénario Nominal** :
    1.  L'utilisateur ne trouve pas le client dans la recherche.
    2.  Il clique sur le bouton **"+ Nouveau Client"**.
    3.  Une modale s'ouvre avec un formulaire vierge.
    4.  L'utilisateur remplit les champs obligatoires (Société ou Nom, Email).
    5.  L'utilisateur clique sur "Créer et Sélectionner".
    6.  Le système :
        *   Crée l'enregistrement dans la table `Customers`.
        *   Sélectionne automatiquement ce nouveau client pour le devis en cours (cf. étape 5 du [UC-01]).
    7.  La modale se ferme, le client est visible sur le devis.

---

### [UC-03] Modifier les informations client d'un devis (Snapshot vs Master)

**Objectif** : Personnaliser les infos pour *ce* devis spécifique OU corriger la fiche client générale.

*   **Pré-conditions** : Un client est déjà sélectionné sur le devis.
*   **Scénario A : Modification locale (Snapshot)**
    1.  L'utilisateur voit les infos pré-remplies.
    2.  Il change le "Nom du contact" car pour ce dossier c'est une autre personne.
    3.  L'utilisateur sauvegarde le devis.
    4.  **Résultat** : Seul le `customer_name` du devis est changé. La fiche master `Customers` reste inchangée.

*   **Scénario B : Modification de la fiche client (Master)**
    1.  L'utilisateur clique sur un bouton ou lien "Éditer la fiche client" (distinct de l'édition locale).
    2.  Une modale s'ouvre avec les infos du client (Master).
    3.  Il corrige une erreur dans l'adresse ou le SIRET.
    4.  Il valide.
    5.  **Résultat** :
        *   La table `Customers` est mise à jour.
        *   (Optionnel) Le système demande s'il faut répercuter ces changements sur le devis en cours (si oui, met à jour le Snapshot).

---

### [UC-04] Remplacer le client d'un devis

**Objectif** : Corriger une erreur d'affectation de client.

*   **Pré-conditions** : Un client A est sélectionné.
*   **Scénario Nominal** :
    1.  L'utilisateur clique sur un bouton "Changer de client" ou sur l'icône de suppression (X) dans la carte client.
    2.  Le système vide les champs clients du devis et réaffiche la barre de recherche.
    3.  L'utilisateur recherche et sélectionne le client B.
    4.  Le système écrase les anciennes données (A) par les nouvelles (B).

---

### [UC-05] Validation des données client

**Objectif** : S'assurer qu'un devis ne part pas sans client valide (si validation stricte activée).

*   **Scénario Nominal** :
    1.  L'utilisateur tente de passer le devis du statut "BROUILLON" à "PRÊT" ou "ENVOYÉ".
    2.  Le système vérifie si un `customer_id` est lié.
    3.  Si non : Une erreur bloquante s'affiche "Veuillez sélectionner un client avant de finaliser".
    4.  Si oui : Le changement de statut est autorisé.

---

## 🛠 Données Techniques (Rappel)

**Champs minimums pour un client (Mode simple) :**
*   Nom ou Société (Requis)
*   Email (Recommandé pour l'envoi)

**Champs étendus (Mode complet) :**
*   Code Client (Généré auto ex: CLI-0001)
*   SIRET (Pour validation pro)
*   Adresse complète
*   Conditions paiement (ex: 30 jours fin de mois)
