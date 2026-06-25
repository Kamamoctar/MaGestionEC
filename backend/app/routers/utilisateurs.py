from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_admin, get_current_user
from app.core.security import hash_password
from app.database import get_db
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurOut, UtilisateurUpdate

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


@router.get("", response_model=list[UtilisateurOut], dependencies=[Depends(require_admin)])
async def lister(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Utilisateur).order_by(Utilisateur.nom))
    return list(result.scalars().all())


@router.post("", response_model=UtilisateurOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def creer(data: UtilisateurCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    existing = await db.execute(select(Utilisateur).where(Utilisateur.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    user = Utilisateur(
        nom=data.nom,
        prenom=data.prenom,
        email=data.email,
        password_hash=hash_password(data.password),
        role_fonctionnel=data.role_fonctionnel,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UtilisateurOut, dependencies=[Depends(require_admin)])
async def obtenir(user_id: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Utilisateur).where(Utilisateur.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@router.patch("/{user_id}", response_model=UtilisateurOut, dependencies=[Depends(require_admin)])
async def modifier(user_id: str, data: UtilisateurUpdate, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Utilisateur).where(Utilisateur.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
