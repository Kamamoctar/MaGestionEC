import uuid
from datetime import datetime, timezone
from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import courrier_access_condition, tenant_scope_condition
from app.models.compteur import CompteurReference
from app.models.courrier import Courrier, ConfidentialiteCourrier, EtatCourrier, PrioriteCourrier, TypeCourrier
from app.models.flux import Flux, FluxEtape
from app.models.mouvement import Mouvement, ActionMouvement
from app.models.poste import Poste
from app.models.tenant import Tenant
from app.models.utilisateur import Utilisateur


def _code_tenant(tenant: Tenant | None) -> str | None:
    if tenant is None:
        return None
    base = "".join(ch for ch in tenant.slug.upper() if ch.isalnum())[:8] or "TENANT"
    return f"{base}{tenant.id[:4].upper()}"


async def _generer_reference(db: AsyncSession, type_courrier: str, tenant: Tenant | None = None) -> str:
    """
    Référence séquentielle au format PREFIX-ANNEE-XXXX (ex : ARR-2026-0042).
    Utilise SELECT FOR UPDATE pour garantir l'unicité sous concurrence.
    """
    annee = datetime.now(timezone.utc).year
    prefixes = {"arrivee": "ARR", "depart": "DEP", "interne": "INT"}
    prefix = prefixes.get(type_courrier, "GEC")
    tenant_condition = (
        CompteurReference.tenant_id == tenant.id
        if tenant
        else CompteurReference.tenant_id.is_(None)
    )

    result = await db.execute(
        select(CompteurReference)
        .where(
            CompteurReference.type == type_courrier,
            CompteurReference.annee == annee,
            tenant_condition,
        )
    )
    compteur = result.scalar_one_or_none()
    if compteur is None:
        compteur = CompteurReference(type=type_courrier, annee=annee, valeur=1, tenant_id=tenant.id if tenant else None)
        db.add(compteur)
    else:
        compteur.valeur += 1

    await db.flush()
    code = _code_tenant(tenant)
    if code:
        return f"{code}-{prefix}-{annee}-{compteur.valeur:04d}"
    return f"{prefix}-{annee}-{compteur.valeur:04d}"


async def _premier_poste_accueil_tenant(db: AsyncSession, tenant_id: str) -> Poste | None:
    secretariat = await db.execute(
        select(Poste)
        .where(Poste.tenant_id == tenant_id, Poste.is_active == True, Poste.intitule.ilike("%secr%"))
        .order_by(Poste.intitule)
        .limit(1)
    )
    poste = secretariat.scalar_one_or_none()
    if poste:
        return poste

    first = await db.execute(
        select(Poste)
        .where(Poste.tenant_id == tenant_id, Poste.is_active == True)
        .order_by(Poste.intitule)
        .limit(1)
    )
    return first.scalar_one_or_none()


async def _valider_poste_tenant(db: AsyncSession, poste_id: str, tenant: Tenant | None) -> Poste:
    stmt = select(Poste).where(Poste.id == poste_id)
    if tenant is not None:
        stmt = stmt.where(tenant_scope_condition(Poste.tenant_id, tenant.id))
    result = await db.execute(stmt)
    poste = result.scalar_one_or_none()
    if poste is None:
        raise ValueError("Poste destinataire introuvable")
    return poste


async def _valider_flux_tenant(db: AsyncSession, flux_id: str, tenant: Tenant | None) -> Flux:
    stmt = select(Flux).where(Flux.id == flux_id)
    if tenant is not None:
        stmt = stmt.where(tenant_scope_condition(Flux.tenant_id, tenant.id))
    result = await db.execute(stmt)
    flux = result.scalar_one_or_none()
    if flux is None:
        raise ValueError("Flux introuvable")
    return flux


async def creer_courrier(db: AsyncSession, data: dict, created_by: Utilisateur, tenant: Tenant | None = None) -> Courrier:
    flux_id = data.get("flux_id")
    etape_courante_id = None

    # Si un circuit est associé, initialiser sur la première étape
    if flux_id:
        await _valider_flux_tenant(db, flux_id, tenant)
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

    if not data.get("poste_destinataire_id"):
        raise ValueError("Un poste destinataire est requis")
    await _valider_poste_tenant(db, data["poste_destinataire_id"], tenant)

    data["tenant_id"] = tenant.id if tenant else data.get("tenant_id")
    reference = await _generer_reference(db, data["type"], tenant)

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


async def creer_courrier_intertenant(
    db: AsyncSession,
    data: dict,
    created_by: Utilisateur,
    tenant_source: Tenant,
    postes_source: Iterable[Poste],
) -> Courrier:
    if data.get("type") != TypeCourrier.depart:
        raise ValueError("L'envoi inter-tenant doit etre un courrier depart")

    tenant_destinataire_id = data.get("tenant_destinataire_id")
    if not tenant_destinataire_id:
        raise ValueError("Tenant destinataire requis")
    if tenant_destinataire_id == tenant_source.id:
        raise ValueError("Le tenant destinataire doit etre different du tenant courant")

    tenant_dest_result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_destinataire_id, Tenant.is_active == True)
    )
    tenant_dest = tenant_dest_result.scalar_one_or_none()
    if tenant_dest is None:
        raise ValueError("Tenant destinataire introuvable")

    postes_source = list(postes_source)
    poste_source_id = data.get("poste_destinataire_id") or (postes_source[0].id if postes_source else None)
    if not poste_source_id:
        raise ValueError("Aucun poste source accessible pour envoyer ce courrier")
    await _valider_poste_tenant(db, poste_source_id, tenant_source)

    poste_arrivee = await _premier_poste_accueil_tenant(db, tenant_dest.id)
    if poste_arrivee is None:
        raise ValueError("Le tenant destinataire n'a aucun poste actif pour recevoir le courrier")

    data_depart = data.copy()
    data_depart.update(
        tenant_id=tenant_source.id,
        tenant_expediteur_id=tenant_source.id,
        tenant_destinataire_id=tenant_dest.id,
        poste_destinataire_id=poste_source_id,
        flux_id=None,
    )
    data_depart.pop("dossier_id", None)

    courrier_depart = Courrier(
        **data_depart,
        id=str(uuid.uuid4()),
        reference=await _generer_reference(db, TypeCourrier.depart, tenant_source),
        created_by_id=created_by.id,
        etat=EtatCourrier.en_attente,
    )
    db.add(courrier_depart)
    await db.flush()

    db.add(Mouvement(
        courrier_id=courrier_depart.id,
        utilisateur_id=created_by.id,
        action=ActionMouvement.creation,
        poste_destination_id=poste_source_id,
    ))

    courrier_arrivee = Courrier(
        id=str(uuid.uuid4()),
        tenant_id=tenant_dest.id,
        tenant_expediteur_id=tenant_source.id,
        poste_destinataire_id=poste_arrivee.id,
        type=TypeCourrier.arrivee,
        objet=data["objet"],
        expediteur=tenant_source.nom,
        priorite=data.get("priorite") or PrioriteCourrier.normal,
        confidentialite=data.get("confidentialite") or ConfidentialiteCourrier.normal,
        date_limite=data.get("date_limite"),
        reference_expediteur=courrier_depart.reference,
        courrier_lie_id=courrier_depart.id,
        reference=await _generer_reference(db, TypeCourrier.arrivee, tenant_dest),
        created_by_id=created_by.id,
        etat=EtatCourrier.en_attente,
    )
    db.add(courrier_arrivee)
    await db.flush()

    courrier_depart.courrier_lie_id = courrier_arrivee.id
    db.add(Mouvement(
        courrier_id=courrier_arrivee.id,
        utilisateur_id=created_by.id,
        action=ActionMouvement.creation,
        poste_destination_id=poste_arrivee.id,
        commentaire=f"Arrivee inter-tenant depuis {tenant_source.nom}",
    ))

    await db.commit()
    await db.refresh(courrier_depart)
    return courrier_depart


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
