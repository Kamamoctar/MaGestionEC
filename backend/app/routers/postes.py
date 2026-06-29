from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_role, get_current_tenant, require_admin, get_current_user, tenant_scope_condition
from app.database import get_db
from app.models.direction import Direction
from app.models.poste import Poste
from app.models.tenant import Tenant, TenantMembre
from app.models.utilisateur import Utilisateur, RoleFonctionnel
from app.schemas.poste import PosteCreate, PosteOut, PosteDetailOut, PosteUpdate, AffectationOccupantIn, InterimaireIn, DelegationIn
from app.services.poste_service import (
    changer_occupant,
    affecter_interimaire,
    affecter_delegation,
    desactiver_poste,
    reactiver_poste,
    get_blocages_suppression_poste,
    get_historique_affectations,
)

router = APIRouter(prefix="/postes", tags=["postes"])


@router.get("", response_model=list[PosteOut])
async def lister(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    current_role: Annotated[RoleFonctionnel, Depends(get_current_role)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
    include_inactive: bool = False,
):
    if include_inactive and current_role != RoleFonctionnel.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    stmt = (
        select(Poste)
        .where(tenant_scope_condition(Poste.tenant_id, current_tenant.id))
        .order_by(Poste.is_active.desc(), Poste.intitule)
    )
    if not include_inactive:
        stmt = stmt.where(Poste.is_active == True)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=PosteOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def creer(
    data: PosteCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    if data.direction_id:
        direction_result = await db.execute(
            select(Direction).where(
                Direction.id == data.direction_id,
                tenant_scope_condition(Direction.tenant_id, current_tenant.id),
            )
        )
        if not direction_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Direction introuvable")

    poste = Poste(**data.model_dump(), tenant_id=current_tenant.id)
    db.add(poste)
    await db.commit()
    await db.refresh(poste)
    return poste


@router.get("/{poste_id}", response_model=PosteDetailOut, dependencies=[Depends(get_current_user)])
async def obtenir(
    poste_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Poste)
        .options(selectinload(Poste.occupant))
        .where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    return poste


@router.patch("/{poste_id}", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def modifier(
    poste_id: str,
    data: PosteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    updates = data.model_dump(exclude_none=True)
    if updates.get("direction_id"):
        direction_result = await db.execute(
            select(Direction).where(
                Direction.id == updates["direction_id"],
                tenant_scope_condition(Direction.tenant_id, current_tenant.id),
            )
        )
        if not direction_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Direction introuvable")

    is_active = updates.pop("is_active", None)
    for field, value in updates.items():
        setattr(poste, field, value)

    if is_active is False and poste.is_active:
        try:
            return await desactiver_poste(db, poste)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if is_active is True and not poste.is_active:
        return await reactiver_poste(db, poste)

    await db.commit()
    await db.refresh(poste)
    return poste


@router.put("/{poste_id}/occupant", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def affecter_occupant(
    poste_id: str,
    data: AffectationOccupantIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    """Change l'occupant du poste. Tout l'historique et les courriers restent liés au poste."""
    result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")

    # Vérifier que l'utilisateur existe
    user_result = await db.execute(
        select(Utilisateur)
        .join(TenantMembre, TenantMembre.utilisateur_id == Utilisateur.id)
        .where(
            Utilisateur.id == data.utilisateur_id,
            TenantMembre.tenant_id == current_tenant.id,
            TenantMembre.is_active == True,
        )
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    return await changer_occupant(db, poste, data.utilisateur_id, data.type)


@router.delete("/{poste_id}/occupant", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def liberer_occupant(
    poste_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    return await changer_occupant(db, poste, None)


@router.post("/{poste_id}/desactiver", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def desactiver(
    poste_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    try:
        return await desactiver_poste(db, poste)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/{poste_id}/reactiver", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def reactiver(
    poste_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    return await reactiver_poste(db, poste)


@router.post("/{poste_id}/interimaire", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def affecter_interim(
    poste_id: str,
    data: InterimaireIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    user_result = await db.execute(
        select(Utilisateur)
        .join(TenantMembre, TenantMembre.utilisateur_id == Utilisateur.id)
        .where(
            Utilisateur.id == data.utilisateur_id,
            TenantMembre.tenant_id == current_tenant.id,
            TenantMembre.is_active == True,
        )
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return await affecter_interimaire(db, poste, data.utilisateur_id)


@router.post("/{poste_id}/delegation", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def affecter_delegation_route(
    poste_id: str,
    data: DelegationIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    """Enregistre une délégation sans changer l'occupant titulaire."""
    result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    user_result = await db.execute(
        select(Utilisateur)
        .join(TenantMembre, TenantMembre.utilisateur_id == Utilisateur.id)
        .where(
            Utilisateur.id == data.utilisateur_id,
            TenantMembre.tenant_id == current_tenant.id,
            TenantMembre.is_active == True,
        )
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return await affecter_delegation(db, poste, data.utilisateur_id)


@router.get("/{poste_id}/historique", dependencies=[Depends(require_admin)])
async def historique(
    poste_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    poste_result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    if not poste_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Poste introuvable")
    affectations = await get_historique_affectations(db, poste_id)
    return [
        {
            "id": a.id,
            "utilisateur_id": a.utilisateur_id,
            "date_debut": a.date_debut,
            "date_fin": a.date_fin,
            "type": a.type,
        }
        for a in affectations
    ]


@router.delete("/{poste_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def supprimer(
    poste_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    """
    Suppression physique réservée aux postes créés par erreur.
    Refusée dès qu'une trace métier référence le poste.
    """
    result = await db.execute(
        select(Poste).where(Poste.id == poste_id, tenant_scope_condition(Poste.tenant_id, current_tenant.id))
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")

    blocages = await get_blocages_suppression_poste(db, poste)
    if blocages:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Suppression impossible : désactivez le poste pour conserver l'historique.",
                "blocages": blocages,
            },
        )

    await db.delete(poste)
    await db.commit()
