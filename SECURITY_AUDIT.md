# Audit de Securite - Serveur Transport Quote
**Date** : 2026-02-10
**Serveur** : vps-ddfa60f6 (135.125.103.119)

---

## Resultat malware : AUCUN DETECTE

- Processus en cours : tous legitimes
- Fichiers SUID : tous standards
- Aucun fichier suspect dans /tmp, /var/tmp, /dev/shm
- Crontabs propres (packages systeme uniquement)
- Connexions SSH reussies uniquement depuis 2 IPs connues via cle publique

---

## Attaques en cours

- **32 775 tentatives de brute-force SSH** depuis ~240 IPs en 3 jours
- Utilisateurs testes : root, admin, git, orangepi, solana
- **Aucune intrusion reussie** (authentification par cle uniquement)

---

## Failles de securite

### CRITIQUE

- [ ] **1. Aucune authentification sur l'API transport_quote**
  - Fichiers : `backend/app/api/*.py`
  - Tous les endpoints (devis, partenaires, imports, uploads) sont accessibles sans login
  - Action : implementer JWT ou OAuth2 sur tous les endpoints

- [ ] **2. Secrets en clair dans le repo Git**
  - Fichier : `.env` (racine du projet)
  - Contient les mots de passe PostgreSQL, Redis, SECRET_KEY en clair
  - Le `.gitignore` ignore `backend/.env` mais PAS le `.env` racine
  - Action : supprimer `.env` de l'historique Git (BFG Repo-Cleaner), ajouter au `.gitignore`, changer tous les mots de passe

- [ ] **3. Cle JWT hardcodee dans kpi-backend**
  - Fichier : `/home/ubuntu/opt/kpi-analyzer/kpi-analyzer-monorepo/python-engine/auth/auth_service.py:12`
  - Valeur : `"votre-cle-secrete-a-changer-en-production"`
  - Action : passer la cle en variable d'environnement, generer une vraie cle

- [ ] **4. Containers Docker en root**
  - Les containers backend et kpi-backend tournent en tant que root
  - Action : ajouter `USER` non-root dans les Dockerfiles

- [ ] **5. CORS trop permissif**
  - Fichier : `backend/app/main.py:17-25`
  - `allow_methods=["*"]`, `allow_headers=["*"]` avec `allow_credentials=True`
  - Action : specifier explicitement les methodes (GET, POST, PUT, DELETE) et headers autorises

- [ ] **6. Firewall desactive**
  - `ufw status: inactive` — tous les ports sont ouverts sur Internet
  - Action : `sudo ufw allow 22,80,443/tcp && sudo ufw enable`

### HAUTE

- [ ] **7. Pas de fail2ban installe**
  - 32 775 tentatives de brute-force SSH non bloquees
  - Action : `sudo apt install fail2ban && sudo systemctl enable fail2ban`

- [ ] **8. Pas de rate limiting sur les API**
  - Aucune limitation de requetes sur aucun endpoint
  - Action : ajouter un middleware de rate limiting (slowapi ou similaire)

- [ ] **9. Headers de securite manquants (Nginx staging)**
  - Fichier : `frontend/nginx.staging.conf`
  - Manquent : X-Frame-Options, X-Content-Type-Options, HSTS, CSP strict
  - Action : ajouter les headers de securite (copier depuis nginx-reverse-proxy.conf)

- [ ] **10. Upload fichiers peu valide**
  - Fichier : `backend/app/api/imports.py:22-60`
  - Verification MIME loose, pas de scan antivirus
  - Action : utiliser python-magic pour validation stricte du type MIME

- [ ] **11. Port 3000 expose directement sur Internet**
  - Le backend est accessible en contournant le reverse proxy
  - Action : limiter le port 3000 au reseau Docker interne (supprimer le mapping ports dans docker-compose.yml ou bloquer via ufw)

- [ ] **12. Documentation API publique**
  - Fichier : `backend/app/main.py:12-13`
  - `/docs` et `/redoc` exposent la structure complete de l'API
  - Action : desactiver en production (`docs_url=None, redoc_url=None`)

### MOYENNE

- [ ] **13. Pas de HTTPS natif**
  - Le reverse proxy (nginx-reverse-proxy.conf) ecoute sur port 80 uniquement
  - Action : configurer Let's Encrypt / certbot pour HTTPS, rediriger HTTP vers HTTPS

- [ ] **14. Pas d'audit logging**
  - Aucune trace des actions utilisateur (qui a modifie quoi, quand)
  - Action : implementer un systeme de logging structure (table audit_log en BDD)

- [ ] **15. Dependances non a jour**
  - Fichier : `backend/requirements.txt`
  - FastAPI 0.109.2, SQLAlchemy 2.0.25, PyYAML 6.0.1 (versions anciennes)
  - Action : mettre a jour les dependances, scanner avec `pip-audit` ou Snyk

- [ ] **16. CSP trop permissive sur le reverse proxy**
  - Fichier : `nginx-reverse-proxy.conf:10`
  - Autorise `http:`, `'unsafe-inline'`, `data:`, `blob:`
  - Action : restreindre la politique CSP

- [ ] **17. Gestion d'erreurs trop large**
  - Plusieurs `except Exception` silencieux dans le code
  - Action : utiliser des exceptions specifiques, logger les erreurs

### BASSE

- [ ] **18. Pas de masquage des secrets dans les logs**
  - Des print/debug peuvent afficher des donnees sensibles
  - Action : implementer du logging structure avec redaction des secrets

- [ ] **19. Permissions des repertoires d'upload**
  - Fichier : `backend/Dockerfile:20`
  - Repertoires crees sans permissions explicites
  - Action : definir explicitement `chmod 755` pour les repertoires

---

## Ordre de traitement recommande

### Immediat (aujourd'hui)
1. Activer le firewall (faille #6)
2. Installer fail2ban (faille #7)
3. Fermer le port 3000 au public (faille #11)

### Cette semaine
4. Supprimer .env de Git et changer les mots de passe (faille #2)
5. Changer la SECRET_KEY du kpi-backend (faille #3)
6. Desactiver /docs et /redoc en production (faille #12)

### Prochaines semaines
7. Ajouter l'authentification API (faille #1)
8. Corriger CORS (faille #5)
9. Ajouter rate limiting (faille #8)
10. Passer les containers en non-root (faille #4)
11. Ajouter les headers de securite Nginx (faille #9)
12. Configurer HTTPS (faille #13)

### Backlog
13. Valider les uploads (faille #10)
14. Mettre a jour les dependances (faille #15)
15. Ajouter l'audit logging (faille #14)
16. Corriger CSP et gestion d'erreurs (failles #16, #17, #18, #19)
