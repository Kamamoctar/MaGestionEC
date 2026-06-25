# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

---

## [0.2.0] - 2026-06-25

### Added — Infrastructure

- `CLAUDE.md` : contexte permanent (stack, principes, règles de travail) pour Claude Code
- `docker-compose.yml` : orchestration dev (PostgreSQL 16 + backend + frontend)
- `README.md` : documentation complète avec instructions de lancement, structure, variables d'env, roadmap
- `backend/.env.example` : template des variables d'environnement
- `backend/.env` : configuration locale (PostgreSQL 17, clé JWT)

### Added — Backend

- **Modèles SQLAlchemy** (`app/models/`) :
  - `Direction` — entité organisationnelle
  - `Utilisateur` — personne avec rôle fonctionnel (admin/secretariat/agent/direction)
  - `Poste` — fonction, entité centrale ; `occupant_user_id` nullable, jamais propriétaire des données
  - `PosteAffectation` — historique complet occupant/poste (titulaire/intérim/délégation)
  - `Flux` + `FluxEtape` — circuits de traitement issus de BPMN
  - `Courrier` — rattaché au POSTE (jamais à la personne)
  - `PieceJointe` — référence fichier hors base (chemin stockage, pas le binaire)
  - `Mouvement` — log immuable de traçabilité
- **Schemas Pydantic v2** (`app/schemas/`) : direction, utilisateur, poste, courrier, flux
- **Auth JWT** (`app/core/security.py`, `app/core/auth.py`) :
  - Couche 1 : `require_role()` — protège les routes par rôle fonctionnel
  - Couche 2 : `get_poste_utilisateur()` + `peut_voir_courrier_confidentiel()` — filtre les données par poste
- **Services métier** (`app/services/`) :
  - `poste_service` : `changer_occupant()`, `liberer_poste()`, `affecter_interimaire()`, `get_historique_affectations()`
  - `courrier_service` : `creer_courrier()`, `transmettre_courrier()`, `get_courriers_poste()` (filtrage confidentialité)
- **Routers REST** (`app/routers/`) :
  - `auth` : `POST /auth/token`, `GET /auth/me`
  - `utilisateurs` : CRUD (admin uniquement)
  - `directions` : CRUD
  - `postes` : CRUD + affectation occupant + intérim + historique
  - `courriers` : enregistrement, corbeilles, détail, transmission, historique mouvements
  - `flux` : CRUD circuits
- **`app/main.py`** : FastAPI app + CORS + inclusion de tous les routers
- **`app/config.py`** : `Settings` pydantic-settings (DATABASE_URL, SECRET_KEY, etc.)
- **`app/database.py`** : moteur SQLAlchemy async + `AsyncSessionLocal` + `Base`
- **Migration Alembic** `0001_initial` : toutes les tables (upgrade + downgrade)
- **Script seed** `scripts/seed.py` :
  - Crée admin `admin@gec.local` / `Admin1234!`
  - Crée secrétariat `secretariat@gec.local` / `Secret1234!`
  - Direction "Direction Générale" + poste "Directeur Général" affecté à l'admin

### Added — Frontend

- **Setup** : Vite 5 + React 18 + TypeScript 5 + TailwindCSS + vite-plugin-pwa (PWA Workbox)
- **`src/types/index.ts`** : types TypeScript partagés (Utilisateur, Poste, Courrier, Flux…)
- **`src/store/authStore.ts`** : store Zustand persistant (token JWT + utilisateur connecté)
- **`src/api/`** : clients Axios (`auth`, `courriers`, `postes`, `mouvements`) + intercepteur token + redirection 401
- **`src/router/PrivateRoute.tsx`** : garde de route (authentification + vérification rôle)
- **`src/App.tsx`** : routing React Router v6 (routes publiques + espace admin + espace utilisateur)
- **Pages Admin** (`src/pages/admin/`) :
  - `AdminLayout.tsx` : sidebar avec navigation + lien espace utilisateur
  - `PostesPage.tsx` : liste + création de postes
  - `UtilisateursPage.tsx` : liste des utilisateurs
  - `ImportBpmnPage.tsx` : placeholder upload BPMN (drag & drop UI)
- **Pages Utilisateur** (`src/pages/user/`) :
  - `UserLayout.tsx` : sidebar avec navigation + lien espace admin (si admin)
  - `CorbeillesPage.tsx` : liste des courriers par état, cliquables
  - `CourrierDetailPage.tsx` : détail courrier + formulaire de transmission + timeline historique
  - `EnregistrementPage.tsx` : formulaire d'enregistrement express (secrétariat)
  - `LoginPage.tsx` : formulaire de connexion avec redirection selon rôle
  - `NonAutorisePage.tsx` : page d'erreur 403

### Added — Tests backend (`backend/tests/`)

- `test_poste_transfert.py` : transfert poste hérite les courriers, clôture affectation, intérim, libération
- `test_acces_confidentiel.py` : poste normal ne voit pas les courriers confidentiels ; poste confidentiel voit tout
- `test_roles.py` : agent/secrétariat refusé sur routes admin, admin autorisé, non authentifié refusé, mauvais mdp refusé

### Fixed

- Compatibilité `bcrypt 5.x` vs `passlib` : version verrouillée à `bcrypt<5.0` dans `pyproject.toml`
- Dépendance `email-validator` ajoutée (requise par `EmailStr` de Pydantic)
- Signature `mes_corbeilles` router : paramètres keyword-only avec `*` (suppression `= None` sur les dépendances)

### Infrastructure locale (sans Docker)

- PostgreSQL 17 installé via `winget` et configuré (`gec_db`, user `gec`)
- Node.js 24 LTS installé via `winget`
- Environnement Python `.venv` configuré dans `backend/`

---

## [0.1.0] - 2026-06-25

### Added

- Création du squelette projet avec les dossiers `backend/` et `frontend/`.
- `README.md` initial.
- `MANIFEST.md` pour le suivi des métadonnées et des règles de modification.
