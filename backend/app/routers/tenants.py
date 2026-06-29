from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_tenant, get_current_user
from app.database import get_db
from app.models.tenant import Tenant
from app.models.utilisateur import Utilisateur
from app.schemas.tenant import TenantOut

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=list[TenantOut])
async def lister(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Tenant)
        .where(Tenant.is_active == True, Tenant.id != current_tenant.id)
        .order_by(Tenant.nom)
    )
    return list(result.scalars().all())


@router.get("/me", response_model=TenantOut)
async def courant(current_tenant: Annotated[Tenant, Depends(get_current_tenant)]):
    return current_tenant
