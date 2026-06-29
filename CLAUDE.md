# Projet : GEC — Application web PWA (Gestion Électronique des Courriers)

## Nature du projet
- Application web AUTONOME développée DE ZÉRO (pas un module d'un ERP existant).
- Livrée en PWA : installable, responsive (mobile + desktop), shell utilisable hors-ligne.
- Architecture : API REST (backend) + SPA (frontend).

## Stack technique
- Backend : Python 3.12 + FastAPI + PostgreSQL 16 + SQLAlchemy 2.0 + Alembic.
- Auth : JWT (python-jose + passlib/bcrypt), deux couches distinctes (voir "Sécurité").
- Frontend : React 18 + Vite 5 + TypeScript 5 + TailwindCSS, PWA via vite-plugin-pwa.
- BPMN : bpmn-js (frontend) + lxml (backend).
- Tests : pytest + httpx (backend), Vitest + Testing Library (frontend).
- Dev local : docker-compose (postgres + backend + frontend).

## Principe architectural NON NÉGOCIABLE : tout est centré sur le POSTE
- Le POSTE (fonction : "Directeur Général", "Secrétariat", etc.) est l'entité centrale.
- L'utilisateur (personne) est un SIMPLE ATTRIBUT dynamique du poste (champ occupant courant).
- Courriers, droits, corbeilles et historique sont TOUJOURS rattachés au POSTE, jamais à la personne.
- Conséquence voulue : changer l'occupant d'un poste transfère instantanément encours, droits et historique.
- Ne jamais lier un courrier ou un droit d'accès directement à un utilisateur.

## Deux espaces applicatifs distincts
- ESPACE ADMIN : configure tout ce que les utilisateurs consommeront.
  - CRUD des Postes ; affectation de l'occupant ; gestion intérim/délégation.
  - Gestion des utilisateurs et de leurs rôles fonctionnels.
  - IMPORT BPMN : charge un .bpmn/.xml, mappe les lanes -> Postes, génère les circuits.
  - Paramétrage : métadonnées, priorités, niveaux de confidentialité, règles de SLA, directions.
  - Supervision / dashboard de pilotage.
- ESPACE UTILISATEUR : consomme la configuration.
  - Enregistrement express (rôle secrétariat).
  - Corbeilles par Poste : À traiter / En attente de visa / Pour information / Traités.
  - Parapheur : visa, annotations, signature en un clic.
  - Recherche, suivi des courriers.

## Modèles clés
- direction       : entité organisationnelle (DG, DRH, etc.)
- poste           : fonction. occupant_user_id (nullable), niveau_acces, direction_id.
- poste_affectation: historique occupant/poste (date_debut, date_fin, type titulaire/interim/delegation).
- utilisateur     : personne. role_fonctionnel (admin/secretariat/agent/direction). PAS de droit courrier ici.
- courrier        : objet, expediteur (str libre), poste_destinataire_id, priorité, date_limite, type, confidentialité, état.
- piece_jointe    : référence fichier HORS base (chemin S3/disque), jamais le binaire en base.
- flux            : circuit issu d'un import BPMN.
- flux_etape      : étape ordonnée (poste_id, type_action, condition_transition, is_terminal).
- mouvement       : log immuable de traçabilité des passages poste à poste.

## Sécurité — DEUX couches à ne pas confondre
1. Rôle fonctionnel (admin / secretariat / agent / direction) : décide quels ÉCRANS/ROUTES sont accessibles.
2. Accès aux DONNÉES (courriers) : calculé sur le POSTE de l'utilisateur connecté + confidentialité. Jamais sur la personne.

## Règles de travail pour Claude Code
- Avancer par INCRÉMENTS testables. Une fonctionnalité = modèle + endpoint(s) REST + écran(s) + tests.
- API REST cohérente et documentée (OpenAPI/Swagger auto via FastAPI).
- Toujours écrire des tests pour la logique métier (transfert de poste, intérim, mapping BPMN, accès confidentiel).
- Migrations versionnées (Alembic) pour tout changement de schéma.
- PWA : maintenir manifest + service worker ; le shell et les listes consultées doivent rester accessibles hors-ligne.
- Pièces jointes volumineuses stockées HORS base (S3/MinIO ou disque) — seule la référence va en base.
- UX : épurée, zéro jargon, zéro formation pour le top management.
- Toujours mettre à jour la page frontend `Aide & documentation` (`frontend/src/pages/AidePage.tsx`) lorsqu'une fonctionnalité visible, une règle métier ou un workflow utilisateur/admin évolue.
- Documenter en français les modèles et la logique non triviale.
