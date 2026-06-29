# Project Manifest

**Project**: GEC – Gestion Électronique des Courriers (PWA)
**Version**: 0.2.2
**Created**: 2026-06-25
**Last Updated**: 2026-06-29

## Description
Application web autonome (PWA installable) de Gestion Électronique des Courriers.
Monorepo contenant un backend FastAPI et un frontend React/Vite PWA.
L'architecture est centrée sur l'entité **Poste** (fonction), jamais sur la personne.

## Stack technique
- **Backend** : Python 3.12 · FastAPI · PostgreSQL 17 · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2
- **Auth** : JWT (python-jose + passlib/bcrypt)
- **Frontend** : React 18 · Vite 5 · TypeScript 5 · TailwindCSS · vite-plugin-pwa (Workbox)
- **BPMN** : bpmn-js (frontend) · lxml (backend — à venir)
- **Tests** : pytest + httpx + aiosqlite (backend) · Vitest + Testing Library (frontend)

## Structure
```
STANDALONE_GEC/
├── CLAUDE.md              ← Contexte permanent pour Claude Code
├── MANIFEST.md            ← Ce fichier
├── CHANGELOG.md           ← Historique détaillé des changements
├── README.md              ← Documentation utilisateur + instructions lancement
├── docker-compose.yml     ← Orchestration dev (postgres + backend + frontend)
├── backend/
│   ├── app/
│   │   ├── main.py        ← Point d'entrée FastAPI + CORS
│   │   ├── config.py      ← Variables d'environnement (pydantic-settings)
│   │   ├── database.py    ← Moteur SQLAlchemy async + session
│   │   ├── models/        ← ORM : utilisateur, direction, poste, poste_affectation,
│   │   │                     flux, flux_etape, courrier, piece_jointe, mouvement
│   │   ├── schemas/       ← Pydantic I/O par domaine
│   │   ├── routers/       ← Endpoints REST : auth, utilisateurs, directions,
│   │   │                     postes, courriers, flux
│   │   ├── services/      ← Logique métier : poste_service, courrier_service
│   │   └── core/
│   │       ├── auth.py    ← get_current_user, require_role, couche 2 accès données
│   │       └── security.py← JWT encode/decode, bcrypt hash/verify
│   ├── alembic/           ← Migrations versionnées
│   │   └── versions/0001_initial.py ← Toutes les tables GEC
│   ├── scripts/
│   │   └── seed.py        ← Création premier admin + données démo
│   └── tests/
│       ├── test_poste_transfert.py   ← Transfert poste, intérim, libération
│       ├── test_acces_confidentiel.py← Couche 2 sécurité (poste normal vs confidentiel)
│       └── test_roles.py             ← Couche 1 sécurité (rôles fonctionnels)
└── frontend/
    └── src/
        ├── App.tsx         ← Routing principal + gardes par rôle
        ├── types/          ← Types TypeScript partagés
        ├── store/authStore.ts ← Zustand (token JWT + utilisateur connecté)
        ├── api/            ← Clients Axios : auth, courriers, postes, mouvements
        ├── router/PrivateRoute.tsx ← Garde de route (auth + rôle)
        └── pages/
            ├── LoginPage.tsx
            ├── NonAutorisePage.tsx
            ├── admin/
            │   ├── AdminLayout.tsx    ← Sidebar admin
            │   ├── PostesPage.tsx     ← CRUD postes
            │   ├── UtilisateursPage.tsx
            │   └── ImportBpmnPage.tsx ← Placeholder upload BPMN
            └── user/
                ├── UserLayout.tsx        ← Sidebar utilisateur
                ├── CorbeillesPage.tsx    ← Liste courriers par état
                ├── CourrierDetailPage.tsx← Détail + transmission + historique
                └── EnregistrementPage.tsx← Formulaire enregistrement express

## Principe fondamental
Le **POSTE** (ex : "Directeur Général") est l'entité centrale. L'occupant est un
attribut dynamique : changer d'occupant transfère automatiquement tous les courriers,
droits et historique — sans aucune action manuelle.

## Deux espaces
| Espace | Rôles | Fonctionnalités |
|--------|-------|-----------------|
| `/admin` | `admin` | Postes, utilisateurs, import BPMN, paramétrage |
| `/app` | tous | Corbeilles, enregistrement express, détail courrier |

## Deux couches de sécurité
1. **Rôle fonctionnel** (`admin/secretariat/agent/direction`) → contrôle routes/écrans
2. **Accès aux courriers** → calculé sur le POSTE occupé + niveau de confidentialité

## Tracking Modifications
Toutes les modifications sont enregistrées dans `CHANGELOG.md` au format **Keep a Changelog**.
Chaque entrée inclut : date (YYYY-MM-DD), description, composants affectés.
