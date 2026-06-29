from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_tenant, require_admin, tenant_scope_condition
from app.database import get_db
from app.models.courrier import Courrier, EtatCourrier
from app.models.direction import Direction
from app.models.flux import Flux, FluxEtape
from app.models.poste import Poste
from app.models.tenant import Tenant

router = APIRouter(prefix="/admin/supervision", tags=["supervision"])


@router.get("", dependencies=[Depends(require_admin)])
async def supervision(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    """
    Tableau de bord de pilotage admin :
    - Répartition des courriers par direction
    - Courriers bloqués à chaque étape des circuits actifs
    """
    now = datetime.now(timezone.utc)

    # ── Répartition par direction ────────────────────────────────────────────
    rows_dir = (await db.execute(
        select(
            Direction.id.label("direction_id"),
            Direction.nom.label("nom"),
            func.count(Courrier.id).label("total"),
            func.sum(case((Courrier.etat == EtatCourrier.en_attente, 1), else_=0)).label("en_attente"),
            func.sum(case((Courrier.etat == EtatCourrier.en_cours, 1), else_=0)).label("en_cours"),
            func.sum(case((Courrier.etat == EtatCourrier.traite, 1), else_=0)).label("traites"),
            func.sum(case((
                Courrier.date_limite.isnot(None),
                Courrier.date_limite < now,
                Courrier.etat.not_in([EtatCourrier.traite, EtatCourrier.archive]),
            ), else_=0)).label("en_retard"),
        )
        .join(Poste, Poste.id == Courrier.poste_destinataire_id)
        .join(Direction, Direction.id == Poste.direction_id)
        .where(
            Poste.direction_id.isnot(None),
            tenant_scope_condition(Courrier.tenant_id, current_tenant.id),
            tenant_scope_condition(Poste.tenant_id, current_tenant.id),
        )
        .group_by(Direction.id, Direction.nom)
        .order_by(func.count(Courrier.id).desc())
    )).all()

    par_direction = [
        {
            "direction_id": r.direction_id,
            "nom": r.nom,
            "total": r.total,
            "en_attente": r.en_attente,
            "en_cours": r.en_cours,
            "traites": r.traites,
            "en_retard": r.en_retard,
        }
        for r in rows_dir
    ]

    # ── Courriers bloqués par étape de circuit ───────────────────────────────
    rows_circ = (await db.execute(
        select(
            Flux.id.label("flux_id"),
            Flux.nom.label("flux_nom"),
            FluxEtape.id.label("etape_id"),
            FluxEtape.ordre,
            FluxEtape.type_action,
            Poste.intitule.label("intitule_poste"),
            func.count(Courrier.id).label("nb_courriers"),
        )
        .join(FluxEtape, FluxEtape.flux_id == Flux.id)
        .join(Poste, Poste.id == FluxEtape.poste_id)
        .join(Courrier, Courrier.etape_courante_id == FluxEtape.id)
        .where(
            Courrier.etat == EtatCourrier.en_cours,
            tenant_scope_condition(Courrier.tenant_id, current_tenant.id),
            tenant_scope_condition(Flux.tenant_id, current_tenant.id),
        )
        .group_by(
            Flux.id, Flux.nom,
            FluxEtape.id, FluxEtape.ordre, FluxEtape.type_action,
            Poste.intitule,
        )
        .order_by(Flux.nom, FluxEtape.ordre)
    )).all()

    # Agréger par flux
    circuits: dict[str, dict] = {}
    for r in rows_circ:
        if r.flux_id not in circuits:
            circuits[r.flux_id] = {
                "flux_id": r.flux_id,
                "flux_nom": r.flux_nom,
                "total_en_cours": 0,
                "etapes": [],
            }
        circuits[r.flux_id]["total_en_cours"] += r.nb_courriers
        circuits[r.flux_id]["etapes"].append({
            "ordre": r.ordre,
            "type_action": r.type_action,
            "intitule_poste": r.intitule_poste,
            "nb_courriers": r.nb_courriers,
        })

    return {
        "par_direction": par_direction,
        "circuits_actifs": sorted(circuits.values(), key=lambda c: -c["total_en_cours"]),
    }
