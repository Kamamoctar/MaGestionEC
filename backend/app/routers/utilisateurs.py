from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_tenant, require_admin
from app.core.security import hash_password
from app.database import get_db
from app.models.tenant import Tenant, TenantMembre
from app.models.utilisateur import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurOut, UtilisateurUpdate

router = APIRouter(prefix="/utilisateurs", tags=["utilisateurs"])


def _utilisateur_tenant_out(user: Utilisateur, membre: TenantMembre) -> dict:
    data = UtilisateurOut.model_validate(user).model_dump()
    data["role_fonctionnel"] = membre.role_fonctionnel
    data["is_active"] = membre.is_active and user.is_active
    return data


@router.get("", response_model=list[UtilisateurOut], dependencies=[Depends(require_admin)])
async def lister(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Utilisateur, TenantMembre)
        .join(TenantMembre, TenantMembre.utilisateur_id == Utilisateur.id)
        .where(TenantMembre.tenant_id == current_tenant.id)
        .order_by(Utilisateur.nom)
    )
    return [_utilisateur_tenant_out(user, membre) for user, membre in result.all()]


@router.post("", response_model=UtilisateurOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def creer(
    data: UtilisateurCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    existing = await db.execute(select(Utilisateur).where(Utilisateur.email == data.email))
    user = existing.scalar_one_or_none()
    if user:
        membre_result = await db.execute(
            select(TenantMembre).where(
                TenantMembre.tenant_id == current_tenant.id,
                TenantMembre.utilisateur_id == user.id,
            )
        )
        membre = membre_result.scalar_one_or_none()
        if membre and membre.is_active:
            raise HTTPException(status_code=400, detail="Email deja utilise")
        if membre:
            membre.is_active = True
            membre.role_fonctionnel = data.role_fonctionnel
        else:
            membre = TenantMembre(
                tenant_id=current_tenant.id,
                utilisateur_id=user.id,
                role_fonctionnel=data.role_fonctionnel,
            )
            db.add(membre)
        await db.commit()
        await db.refresh(user)
        await db.refresh(membre)
        return _utilisateur_tenant_out(user, membre)

    user = Utilisateur(
        nom=data.nom,
        prenom=data.prenom,
        email=data.email,
        password_hash=hash_password(data.password),
        role_fonctionnel=data.role_fonctionnel,
    )
    db.add(user)
    await db.flush()
    membre = TenantMembre(
        tenant_id=current_tenant.id,
        utilisateur_id=user.id,
        role_fonctionnel=data.role_fonctionnel,
    )
    db.add(membre)
    await db.commit()
    await db.refresh(user)
    await db.refresh(membre)
    return _utilisateur_tenant_out(user, membre)


@router.get("/{user_id}", response_model=UtilisateurOut, dependencies=[Depends(require_admin)])
async def obtenir(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Utilisateur, TenantMembre)
        .join(TenantMembre, TenantMembre.utilisateur_id == Utilisateur.id)
        .where(
            Utilisateur.id == user_id,
            TenantMembre.tenant_id == current_tenant.id,
        )
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user, membre = row
    return _utilisateur_tenant_out(user, membre)


@router.patch("/{user_id}", response_model=UtilisateurOut, dependencies=[Depends(require_admin)])
async def modifier(
    user_id: str,
    data: UtilisateurUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Utilisateur, TenantMembre)
        .join(TenantMembre, TenantMembre.utilisateur_id == Utilisateur.id)
        .where(
            Utilisateur.id == user_id,
            TenantMembre.tenant_id == current_tenant.id,
        )
    )
    row = result.one_or_none()
    user = row[0] if row else None
    membre = row[1] if row else None
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    for field, value in data.model_dump(exclude_none=True).items():
        if field == "role_fonctionnel":
            membre.role_fonctionnel = value
        elif field == "is_active":
            membre.is_active = value
        else:
            setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    await db.refresh(membre)
    return _utilisateur_tenant_out(user, membre)
