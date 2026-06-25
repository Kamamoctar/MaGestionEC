# GEC — Gestion Électronique des Courriers

Application web autonome (PWA) de gestion des courriers entrants, sortants et internes.
Architecture : API REST FastAPI + SPA React/TypeScript installable hors-ligne.

---

## Démarrage rapide (Docker)

### Prérequis
- Docker Desktop installé et démarré

### Lancement

```bash
docker-compose up --build
```

| Service   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:5173        |
| Backend   | http://localhost:8000        |
| Swagger   | http://localhost:8000/docs   |
| ReDoc     | http://localhost:8000/redoc  |

### Premier lancement : créer l'admin

Après `docker-compose up`, dans un second terminal :

```bash
docker-compose exec backend python scripts/seed.py
```

Cela crée :
- Un admin `admin@gec.local` / `Admin1234!`
- Une direction "Direction Générale"
- Un poste "Directeur Général" rattaché à cette direction

---

## Développement local (sans Docker)

### Backend

```bash
cd backend
python -m venv .venv
# Windows :
.venv\Scripts\activate
# Linux/macOS :
source .venv/bin/activate

pip install -e ".[dev]"

# Copier et ajuster les variables d'environnement
cp .env.example .env

# Lancer les migrations
alembic upgrade head

# Démarrer l'API
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Tests backend

```bash
cd backend
pytest -v
```

---

## Structure du projet

```
STANDALONE_GEC/
├── CLAUDE.md                  ← Contexte permanent pour Claude Code
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py            ← Point d'entrée FastAPI
│   │   ├── config.py          ← Variables d'environnement (pydantic-settings)
│   │   ├── database.py        ← Moteur SQLAlchemy async + session
│   │   ├── models/            ← Entités SQLAlchemy ORM
│   │   ├── schemas/           ← Schémas Pydantic I/O
│   │   ├── routers/           ← Endpoints REST
│   │   ├── services/          ← Logique métier (transfert poste, courriers…)
│   │   └── core/
│   │       ├── auth.py        ← Dépendances FastAPI (get_current_user, require_role…)
│   │       └── security.py    ← JWT + bcrypt
│   ├── alembic/               ← Migrations versionnées
│   ├── tests/                 ← Tests pytest (logique métier + sécurité)
│   └── scripts/
│       └── seed.py            ← Données initiales
└── frontend/
    └── src/
        ├── App.tsx             ← Routing principal + gardes par rôle
        ├── pages/
        │   ├── admin/          ← Espace Admin (postes, utilisateurs, BPMN)
        │   └── user/           ← Espace Utilisateur (corbeilles, parapheur)
        ├── api/                ← Clients Axios par domaine
        ├── store/              ← Zustand (auth)
        └── types/              ← Types TypeScript partagés
```

---

## Principe central : tout est rattaché au POSTE

Le **poste** (ex : "Directeur Général") est l'entité centrale, pas la personne.  
L'occupant est un simple attribut dynamique : changer d'occupant transfère automatiquement
tous les courriers, droits et historique au nouvel occupant — sans aucune action manuelle.

---

## Deux espaces

| Espace | Rôles | Accès |
|--------|-------|-------|
| Admin (`/admin`) | `admin` | Postes, utilisateurs, import BPMN, paramétrage |
| Utilisateur (`/app`) | tous | Corbeilles, parapheur, recherche |

## Deux couches de sécurité

1. **Rôle fonctionnel** (`admin / secretariat / agent / direction`) → contrôle les écrans/routes
2. **Accès aux courriers** → calculé sur le poste occupé + niveau de confidentialité

---

## Variables d'environnement backend

| Variable | Défaut | Description |
|----------|--------|-------------|
| `DATABASE_URL` | postgresql+asyncpg://gec:gec_secret@localhost:5432/gec_db | URL PostgreSQL async |
| `SECRET_KEY` | *(à changer en prod)* | Clé de signature JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 60 | Durée de validité du token |
| `UPLOADS_DIR` | uploads | Répertoire des pièces jointes |

---

## Roadmap (prochaines itérations)

- [ ] Import BPMN complet (parsing lxml + mapping lanes → postes)
- [ ] Corbeilles complètes (visa, signature, annotation en un clic)
- [ ] Parapheur
- [ ] Dashboard direction (KPIs, SLA, goulets)
- [ ] Pièces jointes volumineuses (S3/MinIO)
- [ ] Enregistrement express multicanal
- [ ] Recherche avancée
- [ ] Archivage
