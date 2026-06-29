from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_tenant, get_current_user, get_postes_utilisateur, poste_peut_acceder_courrier, require_secretariat, tenant_scope_condition
from app.database import get_db
from app.models.courrier import Courrier, EtatCourrier
from app.models.flux import FluxEtape
from app.models.mouvement import Mouvement, ActionMouvement
from app.models.poste import Poste
from app.models.tenant import Tenant
from app.models.utilisateur import Utilisateur
from app.schemas.courrier import CourrierCreate, CourrierOut, CourrierUpdate, CourrierLiaisonOut, TransmettreCourrierIn, ActionCourrierIn
from app.services.courrier_service import creer_courrier, creer_courrier_intertenant, transmettre_courrier, get_courriers_postes

router = APIRouter(prefix="/courriers", tags=["courriers"])


def _poste_autorise_courrier(courrier: Courrier, postes: list[Poste]) -> Poste:
    for poste in postes:
        if poste_peut_acceder_courrier(poste, courrier):
            return poste
    raise HTTPException(status_code=403, detail="Accès refusé à ce courrier")


@router.post("", response_model=CourrierOut, status_code=status.HTTP_201_CREATED)
async def enregistrer(
    data: CourrierCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(require_secretariat)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    try:
        payload = data.model_dump()
        if payload.get("tenant_destinataire_id"):
            return await creer_courrier_intertenant(db, payload, current_user, current_tenant, postes)
        return await creer_courrier(db, payload, current_user, current_tenant)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get("/mes-corbeilles", response_model=list[CourrierOut])
async def mes_corbeilles(
    *,
    etat: str | None = None,
    type_action: str | None = None,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    """Retourne les courriers du POSTE de l'utilisateur connecté (couche 2 de sécurité)."""
    if not postes:
        return []
    return await get_courriers_postes(db, postes, etat, type_action)


@router.get("/{courrier_id}", response_model=CourrierOut)
async def obtenir(
    courrier_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    result = await db.execute(
        select(Courrier)
        .options(selectinload(Courrier.etape_courante))
        .where(Courrier.id == courrier_id)
    )
    courrier = result.scalar_one_or_none()
    if not courrier:
        raise HTTPException(status_code=404, detail="Courrier introuvable")

    _poste_autorise_courrier(courrier, postes)

    return courrier


@router.get("/{courrier_id}/liaisons", response_model=dict)
async def liaisons(
    courrier_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    """
    Retourne le fil de correspondance : courrier parent (si existant) + réponses (enfants).
    Accès restreint aux utilisateurs ayant un poste (couche 2 légère — résumés seulement).
    """
    result = await db.execute(select(Courrier).where(Courrier.id == courrier_id))
    courrier = result.scalar_one_or_none()
    if not courrier:
        raise HTTPException(status_code=404, detail="Courrier introuvable")
    _poste_autorise_courrier(courrier, postes)

    parent = None
    if courrier.courrier_parent_id:
        r = await db.execute(select(Courrier).where(Courrier.id == courrier.courrier_parent_id))
        parent_obj = r.scalar_one_or_none()
        if parent_obj and any(poste_peut_acceder_courrier(p, parent_obj) for p in postes):
            parent = CourrierLiaisonOut.model_validate(parent_obj)

    r2 = await db.execute(
        select(Courrier)
        .where(Courrier.courrier_parent_id == courrier_id)
        .order_by(Courrier.created_at)
    )
    reponses = [
        CourrierLiaisonOut.model_validate(c)
        for c in r2.scalars().all()
        if any(poste_peut_acceder_courrier(p, c) for p in postes)
    ]

    return {
        "parent": parent.model_dump() if parent else None,
        "reponses": [r.model_dump() for r in reponses],
    }


@router.get("/{courrier_id}/historique")
async def historique_mouvements(
    courrier_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    """Trace complète des passages du courrier entre postes."""
    result = await db.execute(select(Courrier).where(Courrier.id == courrier_id))
    courrier = result.scalar_one_or_none()
    if not courrier:
        raise HTTPException(status_code=404, detail="Courrier introuvable")
    _poste_autorise_courrier(courrier, postes)

    mvt_result = await db.execute(
        select(Mouvement)
        .where(Mouvement.courrier_id == courrier_id)
        .order_by(Mouvement.created_at)
    )
    mouvements = mvt_result.scalars().all()
    return [
        {
            "id": m.id,
            "action": m.action,
            "poste_source_id": m.poste_source_id,
            "poste_destination_id": m.poste_destination_id,
            "utilisateur_id": m.utilisateur_id,
            "commentaire": m.commentaire,
            "created_at": m.created_at,
        }
        for m in mouvements
    ]


@router.patch("/{courrier_id}", response_model=CourrierOut)
async def modifier(
    courrier_id: str,
    data: CourrierUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    result = await db.execute(select(Courrier).where(Courrier.id == courrier_id))
    courrier = result.scalar_one_or_none()
    if not courrier:
        raise HTTPException(status_code=404, detail="Courrier introuvable")
    _poste_autorise_courrier(courrier, postes)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(courrier, field, value)
    await db.commit()
    await db.refresh(courrier)
    return courrier


@router.post("/{courrier_id}/action", response_model=CourrierOut)
async def action_parapheur(
    courrier_id: str,
    data: ActionCourrierIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    """
    Parapheur — enregistre une action (visa/signature/annotation/retour).
    Si le courrier suit un flux, avance à l'étape suivante ou le marque comme traité.
    """
    result = await db.execute(
        select(Courrier)
        .options(selectinload(Courrier.etape_courante))
        .where(Courrier.id == courrier_id)
    )
    courrier = result.scalar_one_or_none()
    if not courrier:
        raise HTTPException(status_code=404, detail="Courrier introuvable")
    poste = _poste_autorise_courrier(courrier, postes)

    mvt = Mouvement(
        courrier_id=courrier.id,
        poste_source_id=poste.id,
        flux_etape_id=courrier.etape_courante_id,
        utilisateur_id=current_user.id,
        action=ActionMouvement(data.action),
        commentaire=data.commentaire,
    )

    if data.action in ("visa", "signature", "information") and courrier.etape_courante_id:
        etape = courrier.etape_courante
        if etape:
            if etape.is_terminal:
                courrier.etat = EtatCourrier.traite
                courrier.etape_courante_id = None
            else:
                next_res = await db.execute(
                    select(FluxEtape)
                    .where(FluxEtape.flux_id == etape.flux_id, FluxEtape.ordre > etape.ordre)
                    .order_by(FluxEtape.ordre)
                    .limit(1)
                )
                next_etape = next_res.scalar_one_or_none()
                if next_etape:
                    courrier.poste_destinataire_id = next_etape.poste_id
                    courrier.etape_courante_id = next_etape.id
                    mvt.poste_destination_id = next_etape.poste_id
                    courrier.etat = EtatCourrier.en_cours

    elif data.action == "retour":
        prev_res = await db.execute(
            select(Mouvement)
            .where(Mouvement.courrier_id == courrier.id, Mouvement.poste_source_id.isnot(None))
            .order_by(Mouvement.created_at.desc())
            .limit(1)
        )
        prev_mvt = prev_res.scalar_one_or_none()
        if prev_mvt and prev_mvt.poste_source_id:
            courrier.poste_destinataire_id = prev_mvt.poste_source_id
            mvt.poste_destination_id = prev_mvt.poste_source_id

    db.add(mvt)
    await db.commit()

    result2 = await db.execute(
        select(Courrier).options(selectinload(Courrier.etape_courante)).where(Courrier.id == courrier.id)
    )
    return result2.scalar_one()


@router.post("/{courrier_id}/archiver", response_model=CourrierOut)
async def archiver(
    courrier_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    """Archive un courrier traité — action irréversible."""
    result = await db.execute(select(Courrier).where(Courrier.id == courrier_id))
    courrier = result.scalar_one_or_none()
    if not courrier:
        raise HTTPException(status_code=404, detail="Courrier introuvable")
    poste = _poste_autorise_courrier(courrier, postes)
    if courrier.etat != EtatCourrier.traite:
        raise HTTPException(status_code=400, detail="Seuls les courriers traités peuvent être archivés")

    courrier.etat = EtatCourrier.archive
    mvt = Mouvement(
        courrier_id=courrier.id,
        poste_source_id=poste.id,
        utilisateur_id=current_user.id,
        action=ActionMouvement.archive,
    )
    db.add(mvt)
    await db.commit()
    await db.refresh(courrier)
    return courrier


@router.post("/{courrier_id}/transmettre", response_model=CourrierOut)
async def transmettre(
    courrier_id: str,
    data: TransmettreCourrierIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    result = await db.execute(select(Courrier).where(Courrier.id == courrier_id))
    courrier = result.scalar_one_or_none()
    if not courrier:
        raise HTTPException(status_code=404, detail="Courrier introuvable")
    _poste_autorise_courrier(courrier, postes)

    poste_destination = await db.execute(
        select(Poste).where(
            Poste.id == data.poste_destination_id,
            tenant_scope_condition(Poste.tenant_id, current_tenant.id),
        )
    )
    if not poste_destination.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Poste destination introuvable")

    return await transmettre_courrier(db, courrier, data.poste_destination_id, current_user, data.commentaire)
