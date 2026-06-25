from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin, get_current_user
from app.database import get_db
from app.models.direction import Direction
from app.models.utilisateur import Utilisateur
from app.schemas.direction import DirectionCreate, DirectionOut, DirectionUpdate

router = APIRouter(prefix="/directions", tags=["directions"])


@router.get("", response_model=list[DirectionOut], dependencies=[Depends(get_current_user)])
async def lister(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Direction).order_by(Direction.nom))
    return list(result.scalars().all())


@router.post("", response_model=DirectionOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def creer(data: DirectionCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    direction = Direction(**data.model_dump())
    db.add(direction)
    await db.commit()
    await db.refresh(direction)
    return direction


@router.patch("/{direction_id}", response_model=DirectionOut, dependencies=[Depends(require_admin)])
async def modifier(direction_id: str, data: DirectionUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Direction).where(Direction.id == direction_id))
    direction = result.scalar_one_or_none()
    if not direction:
        raise HTTPException(status_code=404, detail="Direction introuvable")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(direction, field, value)
    await db.commit()
    await db.refresh(direction)
    return direction


@router.delete("/{direction_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def supprimer(direction_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Direction).where(Direction.id == direction_id))
    direction = result.scalar_one_or_none()
    if not direction:
        raise HTTPException(status_code=404, detail="Direction introuvable")
    await db.delete(direction)
    await db.commit()
