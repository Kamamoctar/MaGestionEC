from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_tenant, get_current_user, require_secretariat, tenant_scope_condition
from app.database import get_db
from app.models.courrier import Courrier
from app.models.dossier import Dossier
from app.models.tenant import Tenant
from app.models.utilisateur import Utilisateur
from app.schemas.dossier import DossierCreate, DossierOut, DossierUpdate

router = APIRouter(prefix="/dossiers", tags=["dossiers"])


@router.get("", response_model=list[DossierOut])
async def lister(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Utilisateur, Depends(get_current_user)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Dossier, func.count(Courrier.id).label("nb_courriers"))
        .outerjoin(Courrier, (Courrier.dossier_id == Dossier.id) & tenant_scope_condition(Courrier.tenant_id, current_tenant.id))
        .where(tenant_scope_condition(Dossier.tenant_id, current_tenant.id))
        .group_by(Dossier.id)
        .order_by(Dossier.created_at.desc())
    )
    rows = result.all()
    out = []
    for dossier, nb in rows:
        d = DossierOut.model_validate(dossier)
        d.nb_courriers = nb
        out.append(d)
    return out


@router.post("", response_model=DossierOut, status_code=status.HTTP_201_CREATED)
async def creer(
    data: DossierCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(require_secretariat)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    dossier = Dossier(titre=data.titre, description=data.description, created_by_id=current_user.id, tenant_id=current_tenant.id)
    db.add(dossier)
    await db.commit()
    await db.refresh(dossier)
    out = DossierOut.model_validate(dossier)
    out.nb_courriers = 0
    return out


@router.get("/{dossier_id}", response_model=DossierOut)
async def obtenir(
    dossier_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Utilisateur, Depends(get_current_user)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Dossier, func.count(Courrier.id).label("nb_courriers"))
        .outerjoin(Courrier, (Courrier.dossier_id == Dossier.id) & tenant_scope_condition(Courrier.tenant_id, current_tenant.id))
        .where(Dossier.id == dossier_id, tenant_scope_condition(Dossier.tenant_id, current_tenant.id))
        .group_by(Dossier.id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    dossier, nb = row
    out = DossierOut.model_validate(dossier)
    out.nb_courriers = nb
    return out


@router.patch("/{dossier_id}", response_model=DossierOut)
async def modifier(
    dossier_id: str,
    data: DossierUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Utilisateur, Depends(require_secretariat)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Dossier).where(Dossier.id == dossier_id, tenant_scope_condition(Dossier.tenant_id, current_tenant.id))
    )
    dossier = result.scalar_one_or_none()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(dossier, field, value)
    await db.commit()

    result2 = await db.execute(
        select(Dossier, func.count(Courrier.id).label("nb_courriers"))
        .outerjoin(Courrier, (Courrier.dossier_id == Dossier.id) & tenant_scope_condition(Courrier.tenant_id, current_tenant.id))
        .where(Dossier.id == dossier_id, tenant_scope_condition(Dossier.tenant_id, current_tenant.id))
        .group_by(Dossier.id)
    )
    row = result2.one()
    out = DossierOut.model_validate(row[0])
    out.nb_courriers = row[1]
    return out


@router.delete("/{dossier_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer(
    dossier_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[Utilisateur, Depends(require_secretariat)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    result = await db.execute(
        select(Dossier).where(Dossier.id == dossier_id, tenant_scope_condition(Dossier.tenant_id, current_tenant.id))
    )
    dossier = result.scalar_one_or_none()
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    # Délier les courriers avant suppression (ON DELETE SET NULL fait ça en DB, mais on s'en assure)
    await db.delete(dossier)
    await db.commit()
