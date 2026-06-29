import uuid
from datetime import datetime, timezone
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import courrier_access_condition
from app.models.compteur import CompteurReference
from app.models.courrier import Courrier, EtatCourrier
from app.models.flux import FluxEtape
from app.models.mouvement import Mouvement, ActionMouvement
from app.models.poste import Poste
from app.models.utilisateur import Utilisateur


async def _generer_reference(db: AsyncSession, type_courrier: str) -> str:
    """
    Référence séquentielle au format PREFIX-ANNEE-XXXX (ex : ARR-2026-0042).
    Utilise SELECT FOR UPDATE pour garantir l'unicité sous concurrence.
    """
    annee = datetime.now(timezone.utc).year
    prefixes = {"arrivee": "ARR", "depart": "DEP", "interne": "INT"}
    prefix = prefixes.get(type_courrier, "GEC")

    result = await db.execute(
        select(CompteurReference)
        .where(CompteurReference.type == type_courrier, CompteurReference.annee == annee)
    )
    compteur = result.scalar_one_or_none()
    if compteur is None:
        compteur = CompteurReference(type=type_courrier, annee=annee, valeur=1)
        db.add(compteur)
    else:
        compteur.valeur += 1

    await db.flush()
    return f"{prefix}-{annee}-{compteur.valeur:04d}"


async def creer_courrier(db: AsyncSession, data: dict, created_by: Utilisateur) -> Courrier:
    flux_id = data.get("flux_id")
    etape_courante_id = None

    # Si un circuit est associé, initialiser sur la première étape
    if flux_id:
        first_res = await db.execute(
            select(FluxEtape)
            .where(FluxEtape.flux_id == flux_id)
            .order_by(FluxEtape.ordre)
            .limit(1)
        )
        first_etape = first_res.scalar_one_or_none()
        if first_etape:
            etape_courante_id = first_etape.id
            data["poste_destinataire_id"] = first_etape.poste_id

    reference = await _generer_reference(db, data["type"])

    courrier = Courrier(
        **data,
        id=str(uuid.uuid4()),
        reference=reference,
        created_by_id=created_by.id,
        etape_courante_id=etape_courante_id,
        etat=EtatCourrier.en_cours if etape_courante_id else EtatCourrier.en_attente,
    )
    db.add(courrier)

    mouvement = Mouvement(
        courrier_id=courrier.id,
        utilisateur_id=created_by.id,
        action=ActionMouvement.creation,
        poste_destination_id=data["poste_destinataire_id"],
    )
    db.add(mouvement)
    await db.commit()
    await db.refresh(courrier)
    return courrier


async def transmettre_courrier(
    db: AsyncSession,
    courrier: Courrier,
    poste_destination_id: str,
    acteur: Utilisateur,
    commentaire: str | None = None,
) -> Courrier:
    poste_source_id = courrier.poste_destinataire_id
    courrier.poste_destinataire_id = poste_destination_id
    courrier.etat = EtatCourrier.en_cours
    courrier.updated_at = datetime.now(timezone.utc)

    mouvement = Mouvement(
        courrier_id=courrier.id,
        utilisateur_id=acteur.id,
        action=ActionMouvement.transmission,
        poste_source_id=poste_source_id,
        poste_destination_id=poste_destination_id,
        commentaire=commentaire,
    )
    db.add(mouvement)
    await db.commit()
    await db.refresh(courrier)
    return courrier


async def get_courriers_poste(
    db: AsyncSession,
    poste: Poste,
    etat: str | None = None,
    type_action: str | None = None,
) -> list[Courrier]:
    return await get_courriers_postes(db, [poste], etat, type_action)


async def get_courriers_postes(
    db: AsyncSession,
    postes: Iterable[Poste],
    etat: str | None = None,
    type_action: str | None = None,
) -> list[Courrier]:
    """
    Couche 2 : retourne uniquement les courriers des postes accessibles.
    - Les courriers confidentiels ne sont visibles que par un poste de niveau confidentiel.
    - type_action filtre sur FluxEtape.type_action (ex : 'information' pour la corbeille dédiée).
    """
    stmt = (
        select(Courrier)
        .options(selectinload(Courrier.etape_courante))
        .where(courrier_access_condition(postes))
    )

    if etat:
        stmt = stmt.where(Courrier.etat == etat)

    if type_action:
        stmt = (
            stmt.join(FluxEtape, Courrier.etape_courante_id == FluxEtape.id)
            .where(FluxEtape.type_action == type_action)
        )

    result = await db.execute(stmt.order_by(Courrier.created_at.desc()))
    return list(result.scalars().all())
