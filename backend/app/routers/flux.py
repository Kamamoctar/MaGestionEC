from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin, get_current_user
from app.models.utilisateur import Utilisateur
from app.database import get_db
from app.models.flux import Flux, FluxEtape
from app.schemas.flux import FluxCreate, FluxOut

router = APIRouter(prefix="/flux", tags=["flux"])


@router.get("", response_model=list[FluxOut])
async def lister(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Utilisateur, Depends(get_current_user)],
):
    """Liste les circuits disponibles — accessible à tout utilisateur authentifié (sélection à l'enregistrement)."""
    result = await db.execute(select(Flux).options(selectinload(Flux.etapes).selectinload(FluxEtape.poste)).order_by(Flux.nom))
    return list(result.scalars().all())


@router.post("", response_model=FluxOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def creer(data: FluxCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    flux = Flux(nom=data.nom, description=data.description)
    db.add(flux)
    await db.flush()

    for etape_data in data.etapes:
        etape = FluxEtape(flux_id=flux.id, **etape_data.model_dump())
        db.add(etape)

    await db.commit()
    await db.refresh(flux)

    result = await db.execute(
        select(Flux).options(selectinload(Flux.etapes).selectinload(FluxEtape.poste)).where(Flux.id == flux.id)
    )
    return result.scalar_one()


@router.get("/{flux_id}", response_model=FluxOut, dependencies=[Depends(require_admin)])
async def obtenir(flux_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Flux).options(selectinload(Flux.etapes).selectinload(FluxEtape.poste)).where(Flux.id == flux_id)
    )
    flux = result.scalar_one_or_none()
    if not flux:
        raise HTTPException(status_code=404, detail="Flux introuvable")
    return flux


@router.delete("/{flux_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def supprimer(flux_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Flux).where(Flux.id == flux_id))
    flux = result.scalar_one_or_none()
    if not flux:
        raise HTTPException(status_code=404, detail="Flux introuvable")
    await db.delete(flux)
    await db.commit()
