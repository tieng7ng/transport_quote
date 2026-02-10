# Procédures de Déploiement et Rollback

Ce document détaille les stratégies recommandées pour déployer l'application **Transport Quote** en production tout en garantissant la possibilité de revenir en arrière (Rollback) en cas de problème.

---

## Stratégie 1 : Git Tags + Docker Rebuild (Recommandée)

Cette méthode est la plus simple et la plus fiable pour une architecture mono-serveur (Docker Compose). Elle s'appuie sur Git comme source de vérité.

### ✅ Avantages
*   Simple à mettre en place.
*   Pas de coût d'infrastructure supplémentaire (pas de duplication des environnements).
*   Rollback précis basé sur l'historique Git.

### ⚠️ Inconvénients
*   Courte interruption de service (quelques secondes) lors du redémarrage des conteneurs (`docker-compose up -d`).

### 🚀 Procédure de Déploiement
1.  **Commit & Push** : Valider le code et pousser sur la branche `main`.
2.  **Tag** : Créer un tag de version (ex: `v1.0.1`).
3.  **Sur le Serveur** :
    ```bash
    # 1. Récupérer les changements
    git fetch --tags
    git checkout v1.0.1

    # 2. Reconstruire et relancer
    docker-compose up -d --build
    
    # 3. Vérifier la santé
    docker-compose ps
    ```

### 🔙 Procédure de Rollback (Retour arrière)
Si la version `v1.0.1` est instable, on revient à la `v1.0.0` :

1.  **Identifier la version stable** précédente.
2.  **Sur le Serveur** :
    ```bash
    # 1. Revenir à la version précédente
    git checkout v1.0.0

    # 2. Forcer la reconstruction/redémarrage
    docker-compose up -d --build
    ```

---

## Stratégie 2 : Blue-Green Deployment (Avancée)

Cette méthode consiste à avoir deux environnements parallèles (Blue = Actuel, Green = Nouveau). On bascule le trafic de l'un à l'autre via Nginx.

### ✅ Avantages
*   **Zéro Downtime** : L'utilisateur ne subit aucune coupure.
*   Test en conditions réelles possible sur "Green" avant de basculer le trafic.

### ⚠️ Inconvénients
*   **Ressources Doubles** : Nécessite 2x plus de RAM/CPU temporairement (ou en permanence).
*   **Complexité** : Gestion de la base de données (les migrations de schéma doivent être rétro-compatibles).

### 🚀 Procédure
1.  Déployer la nouvelle version sur une stack parallèle (ex: nouveaux ports).
2.  Tester l'accès direct sur le port "Green".
3.  Modifier la config Nginx pour pointer vers "Green".
4.  Reload Nginx.
5.  Éteindre "Blue".

---

## Scripts d'Automatisation (Implémentés)

Les scripts suivants sont disponibles dans le dossier `/scripts` pour automatiser la **Stratégie 1**.

### 1. Déployer une version (`scripts/deploy.sh`)

Ce script effectue automatiquement :
1.  Une **sauvegarde SQL** de la base de données dans `/backups`.
2.  Un `git fetch` et `git checkout` de la version demandée.
3.  Un `docker-compose up -d --build` pour appliquer changements.
4.  Un nettoyage des images Docker inutilisées.

**Utilisation :**
```bash
./scripts/deploy.sh v1.0.1
```

### 2. Revenir en arrière (`scripts/rollback.sh`)

Ce script permet de revenir à une version précédente du code. Il propose également une option (activable manuellement) pour restaurer la base de données depuis un backup.

**Utilisation (Code uniquement) :**
```bash
./scripts/rollback.sh v1.0.0
```

**Utilisation (Avec restauration BDD) :**
```bash
./scripts/rollback.sh v1.0.0 true
# Le script vous demandera ensuite de spécifier le fichier .sql à restaurer
```
