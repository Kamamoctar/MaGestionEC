from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import courrier_access_condition, get_current_user, get_postes_utilisateur
from app.database import get_db
from app.models.courrier import Courrier, EtatCourrier
from app.models.poste import Poste
from app.models.utilisateur import Utilisateur, RoleFonctionnel

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[Utilisateur, Depends(get_current_user)],
    postes: Annotated[list[Poste], Depends(get_postes_utilisateur)],
):
    """KPIs globaux (admin) ou filtrés sur le poste de l'utilisateur connecté."""
    now = datetime.now(timezone.utc)
    is_admin = current_user.role_fonctionnel == RoleFonctionnel.admin

    def scoped(q):
        """Filtre optionnel selon le rôle."""
        if not is_admin:
            return q.where(courrier_access_condition(postes))
        return q

    en_attente = (await db.execute(scoped(select(func.count()).select_from(Courrier).where(Courrier.etat == EtatCourrier.en_attente)))).scalar() or 0
    en_cours   = (await db.execute(scoped(select(func.count()).select_from(Courrier).where(Courrier.etat == EtatCourrier.en_cours)))).scalar() or 0
    traites    = (await db.execute(scoped(select(func.count()).select_from(Courrier).where(Courrier.etat == EtatCourrier.traite)))).scalar() or 0
    archives   = (await db.execute(scoped(select(func.count()).select_from(Courrier).where(Courrier.etat == EtatCourrier.archive)))).scalar() or 0

    en_retard = (await db.execute(
        scoped(select(func.count()).select_from(Courrier)).where(
            Courrier.date_limite.isnot(None),
            Courrier.date_limite < now,
            Courrier.etat.not_in([EtatCourrier.traite, EtatCourrier.archive]),
        )
    )).scalar() or 0

    # Top 8 postes par volume total (admin uniquement)
    top_postes: list[dict] = []
    if is_admin:
        rows = (await db.execute(
            select(
                Poste.intitule,
                func.count(Courrier.id).label("total"),
                func.sum(case((Courrier.etat == EtatCourrier.traite, 1), else_=0)).label("traites"),
                func.sum(case((
                    Courrier.date_limite.isnot(None),
                    Courrier.date_limite < now,
                    Courrier.etat.not_in([EtatCourrier.traite, EtatCourrier.archive]),
                ), else_=0)).label("en_retard"),
            )
            .join(Poste, Poste.id == Courrier.poste_destinataire_id)
            .group_by(Poste.id, Poste.intitule)
            .order_by(func.count(Courrier.id).desc())
            .limit(8)
        )).all()
        top_postes = [
            {"intitule": r.intitule, "total": r.total, "traites": r.traites, "en_retard": r.en_retard}
            for r in rows
        ]

    return {
        "total": en_attente + en_cours + traites + archives,
        "en_attente": en_attente,
        "en_cours": en_cours,
        "traites": traites,
        "archives": archives,
        "en_retard": en_retard,
        "top_postes": top_postes,
    }
