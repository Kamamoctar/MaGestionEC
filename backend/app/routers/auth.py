from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_role, get_current_user
from app.core.security import verify_password, create_access_token, hash_password
from app.database import get_db
from app.models.tenant import Tenant, TenantMembre
from app.models.utilisateur import RoleFonctionnel, Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurOut, TokenOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenOut)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Utilisateur).where(Utilisateur.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé")

    membre_result = await db.execute(
        select(TenantMembre, Tenant)
        .join(Tenant, Tenant.id == TenantMembre.tenant_id)
        .where(
            TenantMembre.utilisateur_id == user.id,
            TenantMembre.is_active == True,
            Tenant.is_active == True,
        )
        .order_by(Tenant.nom)
        .limit(1)
    )
    row = membre_result.one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Aucun tenant actif pour ce compte")
    membre, tenant = row

    token = create_access_token({"sub": user.id, "role": membre.role_fonctionnel, "tenant_id": tenant.id})
    utilisateur = UtilisateurOut.model_validate(user).model_dump()
    utilisateur["role_fonctionnel"] = membre.role_fonctionnel
    return {
        "access_token": token,
        "token_type": "bearer",
        "utilisateur": utilisateur,
        "tenant_id": tenant.id,
        "tenant_nom": tenant.nom,
    }


@router.get("/me", response_model=UtilisateurOut)
async def me(
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    current_role: Annotated[RoleFonctionnel, Depends(get_current_role)],
):
    utilisateur = UtilisateurOut.model_validate(current_user).model_dump()
    utilisateur["role_fonctionnel"] = current_role
    return utilisateur
