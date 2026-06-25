from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, get_poste_utilisateur
from app.database import get_db
from app.models.courrier import Courrier, TypeCourrier, EtatCourrier, PrioriteCourrier, ConfidentialiteCourrier
from app.models.poste import Poste, NiveauAcces
from app.models.utilisateur import Utilisateur, RoleFonctionnel
from app.schemas.courrier import CourrierOut

router = APIRouter(prefix="/recherche", tags=["recherche"])


@router.get("/courriers", response_model=list[CourrierOut])
async def rechercher(
    q: str | None = Query(None, min_length=2, description="Texte libre (objet, expéditeur, référence)"),
    type: TypeCourrier | None = None,
    etat: EtatCourrier | None = None,
    priorite: PrioriteCourrier | None = None,
    date_debut: datetime | None = None,
    date_fin: datetime | None = None,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
    poste: Poste | None = Depends(get_poste_utilisateur),
):
    """
    Recherche full-text + filtres sur les courriers.
    Admin : tous les courriers.
    Autres : uniquement les courriers du poste courant.
    """
    stmt = select(Courrier)

    # Périmètre selon le rôle
    is_admin = current_user.role_fonctionnel == RoleFonctionnel.admin
    if not is_admin:
        if poste is None:
            return []
        stmt = stmt.where(Courrier.poste_destinataire_id == poste.id)
        # Couche 2 confidentialité : masquer les courriers confidentiels si niveau insuffisant
        if poste.niveau_acces != NiveauAcces.confidentiel:
            stmt = stmt.where(Courrier.confidentialite != ConfidentialiteCourrier.confidentiel)

    # Full-text ILIKE sur objet, expediteur, reference
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(
                Courrier.objet.ilike(pattern),
                Courrier.expediteur.ilike(pattern),
                Courrier.reference.ilike(pattern),
            )
        )

    if type:
        stmt = stmt.where(Courrier.type == type)
    if etat:
        stmt = stmt.where(Courrier.etat == etat)
    if priorite:
        stmt = stmt.where(Courrier.priorite == priorite)
    if date_debut:
        stmt = stmt.where(Courrier.date_reception >= date_debut)
    if date_fin:
        stmt = stmt.where(Courrier.date_reception <= date_fin)

    stmt = stmt.order_by(Courrier.date_reception.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
