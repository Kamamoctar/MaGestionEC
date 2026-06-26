from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin, get_current_user
from app.database import get_db
from app.models.poste import Poste
from app.models.utilisateur import Utilisateur
from app.models.poste_affectation import PosteAffectation
from app.schemas.poste import PosteCreate, PosteOut, PosteDetailOut, PosteUpdate, AffectationOccupantIn, InterimaireIn, DelegationIn
from app.services.poste_service import changer_occupant, affecter_interimaire, affecter_delegation, get_historique_affectations

router = APIRouter(prefix="/postes", tags=["postes"])


@router.get("", response_model=list[PosteOut], dependencies=[Depends(get_current_user)])
async def lister(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Poste).where(Poste.is_active == True).order_by(Poste.intitule))
    return list(result.scalars().all())


@router.post("", response_model=PosteOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def creer(data: PosteCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    poste = Poste(**data.model_dump())
    db.add(poste)
    await db.commit()
    await db.refresh(poste)
    return poste


@router.get("/{poste_id}", response_model=PosteDetailOut, dependencies=[Depends(get_current_user)])
async def obtenir(poste_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Poste).options(selectinload(Poste.occupant)).where(Poste.id == poste_id)
    )
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    return poste


@router.patch("/{poste_id}", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def modifier(poste_id: str, data: PosteUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Poste).where(Poste.id == poste_id))
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(poste, field, value)
    await db.commit()
    await db.refresh(poste)
    return poste


@router.put("/{poste_id}/occupant", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def affecter_occupant(poste_id: str, data: AffectationOccupantIn, db: Annotated[AsyncSession, Depends(get_db)]):
    """Change l'occupant du poste. Tout l'historique et les courriers restent liés au poste."""
    result = await db.execute(select(Poste).where(Poste.id == poste_id))
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")

    # Vérifier que l'utilisateur existe
    user_result = await db.execute(select(Utilisateur).where(Utilisateur.id == data.utilisateur_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    return await changer_occupant(db, poste, data.utilisateur_id, data.type)


@router.delete("/{poste_id}/occupant", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def liberer_occupant(poste_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Poste).where(Poste.id == poste_id))
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    return await changer_occupant(db, poste, None)


@router.post("/{poste_id}/interimaire", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def affecter_interim(poste_id: str, data: InterimaireIn, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Poste).where(Poste.id == poste_id))
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    return await affecter_interimaire(db, poste, data.utilisateur_id)


@router.post("/{poste_id}/delegation", response_model=PosteOut, dependencies=[Depends(require_admin)])
async def affecter_delegation_route(poste_id: str, data: DelegationIn, db: Annotated[AsyncSession, Depends(get_db)]):
    """Enregistre une délégation sans changer l'occupant titulaire."""
    result = await db.execute(select(Poste).where(Poste.id == poste_id))
    poste = result.scalar_one_or_none()
    if not poste:
        raise HTTPException(status_code=404, detail="Poste introuvable")
    return await affecter_delegation(db, poste, data.utilisateur_id)


@router.get("/{poste_id}/historique", dependencies=[Depends(require_admin)])
async def historique(poste_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
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
