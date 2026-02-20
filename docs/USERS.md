# Gestion des utilisateurs - Transport Quote

## Vue d'ensemble

Le projet utilise trois utilisateurs avec des responsabilités séparées :

| Utilisateur | Rôle | Groupe principal | Groupes secondaires | Docker | Git push | sudo |
|-------------|------|------------------|---------------------|--------|----------|------|
| `ubuntu` | Administration système | `ubuntu` | `sudo`, `docker`, `transport` | oui (sudo) | oui | NOPASSWD: ALL |
| `deploy` | Déploiement & rollback | `deploy` | `docker`, `transport` | oui (groupe docker) | non (fetch/checkout) | limité |
| `gitadmin` | Gestion du dépôt git | `gitadmin` | `transport` | non | oui | non |

## Groupes

| Groupe | Rôle | Membres |
|--------|------|---------|
| `transport` | Accès partagé au répertoire projet | `ubuntu`, `deploy`, `gitadmin` |
| `docker` | Accès au daemon Docker sans sudo | `ubuntu`, `deploy` |
| `deploy` | Groupe principal de l'utilisateur deploy | `deploy` |
| `gitadmin` | Groupe principal de l'utilisateur gitadmin | `gitadmin` |

Le groupe `transport` possède le répertoire projet `/home/ubuntu/opt/transport_quote` et garantit un accès en lecture partagé au code pour les trois utilisateurs.

## Utilisateur `deploy`

**Objectif** : Exécuter les déploiements et rollbacks en production.

**Groupes** : `deploy` (principal), `docker`, `transport`

**Droits** :
- Lecture/exécution sur le répertoire projet
- `git fetch` / `git checkout` (lecture seule)
- `docker` et `docker compose` (via groupe docker)
- Exécution de `scripts/deploy.sh` et `scripts/rollback.sh`
- Sudoers limité à `docker compose` et `docker-compose`

**Clé SSH** : `/home/deploy/.ssh/id_ed25519`
- A ajouter comme **Deploy Key read-only** sur GitHub

### Utilisation

```bash
# Déployer une version
sudo -u deploy bash -c 'cd /home/ubuntu/opt/transport_quote && ./scripts/deploy.sh v1.2.0'

# Rollback
sudo -u deploy bash -c 'cd /home/ubuntu/opt/transport_quote && ./scripts/rollback.sh v1.1.0'

# Vérifier les conteneurs
sudo -u deploy bash -c 'docker ps'

# Voir les logs
sudo -u deploy bash -c 'docker compose -f /home/ubuntu/opt/transport_quote/docker-compose.yml logs -f'
```

## Utilisateur `gitadmin`

**Objectif** : Gérer le dépôt git (branches, tags, merges, push).

**Groupes** : `gitadmin` (principal), `transport`

**Droits** :
- Lecture/écriture sur le répertoire `.git`
- Git complet : push, tag, branch, merge
- **Pas d'accès Docker**
- **Pas de sudo**

**Clé SSH** : `/home/gitadmin/.ssh/id_ed25519`
- A ajouter comme **Deploy Key read-write** sur GitHub

### Utilisation

```bash
# Créer un tag de release
sudo -u gitadmin bash -c 'cd /home/ubuntu/opt/transport_quote && git tag -a v1.2.0 -m "Release v1.2.0" && git push origin v1.2.0'

# Créer une branche
sudo -u gitadmin bash -c 'cd /home/ubuntu/opt/transport_quote && git checkout -b feature/xxx && git push -u origin feature/xxx'

# Pousser des changements
sudo -u gitadmin bash -c 'cd /home/ubuntu/opt/transport_quote && git push origin main'
```

## Setup initial

```bash
sudo bash scripts/setup-users.sh
```

Le script :
1. Crée le groupe `transport`
2. Crée les utilisateurs `deploy` et `gitadmin`
3. Génère les clés SSH ed25519
4. Ajuste les permissions du projet
5. Configure le sudoers pour `deploy`
6. Affiche les clés publiques pour ajout sur GitHub

## Configuration GitHub

Après exécution du script, ajouter les deploy keys sur :
https://github.com/tieng7ng/transport_quote/settings/keys

1. **deploy** : coller la clé publique, cocher **"Allow read access only"**
2. **gitadmin** : coller la clé publique, cocher **"Allow write access"**

## Vérification

```bash
# deploy peut fetch et docker
sudo -u deploy bash -c 'cd /home/ubuntu/opt/transport_quote && git fetch --tags'
sudo -u deploy bash -c 'docker ps'

# gitadmin peut git status
sudo -u gitadmin bash -c 'cd /home/ubuntu/opt/transport_quote && git status'

# gitadmin ne peut PAS docker (doit échouer)
sudo -u gitadmin bash -c 'docker ps'
```

## Permissions du répertoire projet

```
/home/ubuntu/opt/transport_quote
  Owner  : ubuntu
  Groupe : transport
  Perms  : u+rwX, g+rX, o-rwx (setgid sur les dossiers)
  .git/  : g+w (écriture pour gitadmin)
```

## Fichier sudoers

`/etc/sudoers.d/deploy` :
```
deploy ALL=(root) NOPASSWD: /usr/bin/docker compose *
deploy ALL=(root) NOPASSWD: /usr/bin/docker-compose *
```
