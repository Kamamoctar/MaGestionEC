# Kit de prompts — GEC en PWA (web app from scratch, Claude Code)

Application autonome de Gestion Électronique des Courriers, construite de zéro (pas un module Odoo).
PWA installable + espace Admin (configuration & import BPMN) + espace Utilisateur (traitement du courrier).

Trois éléments, dans l'ordre :
1. **`CLAUDE.md`** — contexte permanent (à la racine du dépôt, relu à chaque session).
2. **Prompt de démarrage** — pose les fondations.
3. **Template d'évolution** — réutilisable pour chaque nouvelle fonctionnalité.

> Remplace les zones `<...>` avant de lancer. Le choix du stack est marqué comme décision à confirmer.

---

## 1. Fichier `CLAUDE.md` (contexte permanent)

```markdown
# Projet : GEC — Application web PWA (Gestion Électronique des Courriers)

## Nature du projet
- Application web AUTONOME développée DE ZÉRO (pas un module d'un ERP existant).
- Livrée en PWA : installable, responsive (mobile + desktop), shell utilisable hors-ligne.
- Architecture : API REST (backend) + SPA (frontend).

## Stack technique (À CONFIRMER / ADAPTER aux compétences de l'équipe)
- Backend : Python FastAPI + PostgreSQL + SQLAlchemy + Alembic (migrations).
  (Alternative : Django REST Framework si on veut un admin technique fourni.)
- Auth : JWT, avec DEUX couches distinctes (voir "Sécurité" plus bas).
- Frontend : React + Vite + TypeScript, PWA via vite-plugin-pwa (service worker + manifest).
- BPMN : rendu/visualisation via bpmn-js (bibliothèque bpmn.io) côté frontend ;
  parsing et mapping côté backend en Python (lxml).
- Tests : pytest (backend), Vitest + Testing Library (frontend).

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
  - IMPORT BPMN : charge un .bpmn/.xml, mappe les lanes -> Postes, génère les circuits automatiquement.
  - Paramétrage : métadonnées, priorités, niveaux de confidentialité, règles de SLA, directions.
  - Supervision / dashboard de pilotage.
- ESPACE UTILISATEUR : consomme la configuration.
  - Enregistrement express (rôle secrétariat).
  - Corbeilles par Poste : À traiter / En attente de visa / Pour information / Traités.
  - Parapheur : visa, annotations, signature en un clic.
  - Recherche, suivi des courriers.

## Modèles clés
- poste            : fonction. occupant_user_id (nullable), niveau d'accès, direction.
- poste_affectation: historique occupant/poste (date_debut, date_fin) + intérim/délégation.
- utilisateur      : personne. role_fonctionnel (admin/secretariat/agent/direction). PAS de droit courrier ici.
- courrier         : objet, expéditeur, poste destinataire, priorité, date limite, type (arrivé/départ/interne), confidentialité (normal/confidentiel), état.
- flux             : circuit issu d'un import BPMN.
- flux_etape       : étape ordonnée (poste, type d'action distribution/visa/signature, condition de transition).
- mouvement / log  : traçabilité des passages de poste à poste.

## Sécurité — DEUX couches à ne pas confondre
1. Rôle fonctionnel (admin / secretariat / agent / direction) : décide quels ÉCRANS sont accessibles
   (ex. seul l'admin voit l'import BPMN ; seul le secrétariat voit l'enregistrement express).
2. Accès aux DONNÉES (courriers) : calculé sur le POSTE de l'utilisateur connecté, jamais sur la personne,
   modulé par le niveau de confidentialité (normal/confidentiel). C'est la couche qui porte le pilier "Poste".

## Règles de travail pour Claude Code
- Avancer par INCRÉMENTS testables. Une fonctionnalité = modèle + endpoint(s) REST + écran(s) + tests.
- API REST cohérente et documentée (OpenAPI/Swagger auto via FastAPI).
- Toujours écrire des tests pour la logique métier (transfert de poste, intérim, mapping BPMN, accès confidentiel).
- Migrations versionnées (Alembic) pour tout changement de schéma.
- PWA : maintenir manifest + service worker ; le shell et les listes consultées doivent rester accessibles hors-ligne.
- UX : épurée, zéro jargon, zéro formation pour le top management.
- Documenter en français les modèles et la logique non triviale.
```

---

## 2. Prompt de démarrage

```
Tu es Architecte Logiciel et développeur full-stack senior. Lis CLAUDE.md : il contient
le contexte complet, le stack et les règles non négociables. Respecte-les strictement.

OBJECTIF DE CETTE SESSION : poser les fondations de l'application (backend + frontend + PWA).

Procède dans cet ordre, en t'arrêtant pour validation après chaque étape :

ÉTAPE 1 — Structure du projet
- Crée le monorepo : /backend (API REST) et /frontend (SPA PWA), avec README et instructions de lancement.
- Configure : base PostgreSQL, migrations, auth JWT, et le squelette PWA (manifest + service worker).

ÉTAPE 2 — Modèle de données & entités clés
- Implémente poste, poste_affectation, utilisateur, courrier, flux, flux_etape, mouvement
  conformément à CLAUDE.md.
- Implémente la méthode de CHANGEMENT D'OCCUPANT d'un poste : met à jour l'occupant et clôture/ouvre
  l'affectation, sans toucher aux courriers/droits/historique (démontre l'héritage automatique).
- Implémente l'intérim/délégation temporaire.

ÉTAPE 3 — Sécurité à deux couches
- Couche 1 : rôles fonctionnels (admin/secretariat/agent/direction) protégeant les routes/écrans.
- Couche 2 : accès aux courriers calculé sur le POSTE du connecté + niveau de confidentialité.

ÉTAPE 4 — Espaces & navigation
- Pose la séparation Espace Admin / Espace Utilisateur côté frontend (routing + garde par rôle).
- Admin : écran vide "Postes" et "Import BPMN" (placeholders branchés sur l'API).
- Utilisateur : écran vide "Mes corbeilles" (placeholder).

ÉTAPE 5 — Tests
- Backend : transfert de poste donne au nouvel occupant tout l'historique sans autre modification ;
  intérim ; un agent sans le bon poste ne voit pas un courrier confidentiel ;
  un non-admin ne peut pas accéder aux routes d'admin.

NE code PAS encore le parsing BPMN détaillé, les corbeilles complètes ni le dashboard.
Commence par me proposer (a) le choix de stack final et (b) le modèle de données (entités + champs + relations)
AVANT d'écrire le code, pour que je valide.
```

---

## 3. Template d'évolution (réutilisable à l'infini)

```
Lis CLAUDE.md et respecte ses règles (architecture Poste, deux espaces, deux couches de sécurité, PWA).

NOUVELLE FONCTIONNALITÉ / AMÉLIORATION :
<une phrase>

ESPACE CONCERNÉ : <Admin / Utilisateur / les deux>

COMPORTEMENT ATTENDU (du point de vue de l'acteur) :
- <ce que l'admin OU l'utilisateur doit pouvoir faire, concrètement>

CONTRAINTES / PRÉCISIONS :
- <impacts modèles, règles métier, cas limites, hors-ligne le cas échéant>

LIVRABLES ATTENDUS :
- Modèles + migration
- Endpoints REST (+ doc OpenAPI)
- Écran(s) frontend (respect de l'espace concerné et de la garde par rôle)
- Tests (backend + frontend)
- Mise à jour README / CLAUDE.md si l'architecture évolue

MÉTHODE :
- D'abord, propose ton plan et les changements de modèle de données. Attends ma validation.
- Puis implémente par petits incréments testables.
```

### Exemples de remplissage

**Import BPMN (espace Admin) :**
```
NOUVELLE FONCTIONNALITÉ : import BPMN et génération automatique des circuits.
ESPACE CONCERNÉ : Admin.
COMPORTEMENT ATTENDU :
- L'admin charge un fichier .bpmn/.xml ; il est affiché via bpmn-js.
- Le backend parse le fichier, liste les lanes/acteurs détectés et propose un mapping lane -> Poste (modifiable).
- À la validation, génère un flux + ses flux_etape ordonnées (distribution/visa/signature),
  les gateways simples devenant des conditions de transition.
- Le circuit généré devient disponible pour être appliqué aux courriers par les utilisateurs.
CONTRAINTES : parseur backend en lxml, testable isolément ; gérer un BPMN invalide proprement.
LIVRABLES : endpoint d'upload + parsing, écran admin avec bpmn-js et table de mapping, tests avec un BPMN d'exemple.
```

**Corbeilles (espace Utilisateur) :**
```
NOUVELLE FONCTIONNALITÉ : corbeilles par Poste.
ESPACE CONCERNÉ : Utilisateur.
COMPORTEMENT ATTENDU :
- L'agent voit, pour SON poste : À traiter / En attente de visa / Pour information / Traités.
- Il peut ouvrir un courrier, le traiter, le transmettre au poste suivant selon le circuit.
CONTRAINTES : les listes consultées doivent rester visibles hors-ligne (PWA). Accès strictement borné au poste.
LIVRABLES : endpoints de listing par état + poste, écrans de corbeilles, tests d'accès.
```

**Dashboard direction (espace Admin/Direction) :**
```
NOUVELLE FONCTIONNALITÉ : dashboard executive de pilotage.
ESPACE CONCERNÉ : Admin (rôle direction en lecture).
COMPORTEMENT ATTENDU :
- KPIs : volumes (arrivés/départs/internes) par période, taux de respect des SLA,
  cartographie des goulets d'étranglement (postes en retard).
- Filtre par direction, export d'un rapport simplifié.
CONTRAINTES : agrégations efficaces côté backend ; rendu visuel épuré, zéro jargon.
LIVRABLES : endpoints d'agrégation, écran dashboard, tests sur les calculs de KPIs.
```

---

## Note sur la roadmap

Le périmètre complet (multicanal mail, dépôt du courrier physique + grosses pièces jointes 600+ pages,
courrier sortant, archivage, etc.) reste valable : réutilise la checklist en 7 phases du projet,
en l'adaptant aux deux espaces. Rappel critique : les pièces jointes volumineuses sont stockées
HORS base (stockage objet type S3/MinIO ou disque), seule la référence va en base.
```
