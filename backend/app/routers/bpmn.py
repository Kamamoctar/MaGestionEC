from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth import get_current_tenant, require_admin, tenant_scope_condition
from app.database import get_db
from app.models.flux import Flux, FluxEtape
from app.models.poste import Poste
from app.models.tenant import Tenant
from app.schemas.bpmn import BpmnAnalyseOut, GenererFluxIn, LaneDetecteOut
from app.schemas.flux import FluxOut
from app.services.bpmn_service import analyser_bpmn

router = APIRouter(prefix="/bpmn", tags=["bpmn"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 Mo


@router.post("/analyser", response_model=BpmnAnalyseOut, dependencies=[Depends(require_admin)])
async def analyser(file: UploadFile = File(...)):
    """
    Étape 1 — Upload du fichier .bpmn/.xml.
    Retourne l'analyse (lanes détectées, ordre proposé) sans toucher à la base.
    L'admin valide le mapping avant d'appeler /bpmn/generer.
    """
    if file.content_type not in ("application/xml", "text/xml", "application/octet-stream", ""):
        # On accepte aussi application/octet-stream car certains OS envoient ça pour .bpmn
        pass  # pas de rejet strict sur le content-type, on valide via lxml

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 5 Mo)")

    try:
        analyse = analyser_bpmn(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return BpmnAnalyseOut(
        nom_processus=analyse.nom_processus,
        lanes=[
            LaneDetecteOut(
                lane_id=l.lane_id,
                lane_name=l.lane_name,
                taches=l.taches,
                type_action_propose=l.type_action_propose,
            )
            for l in analyse.lanes
        ],
        ordre_lanes=analyse.ordre_lanes,
        bpmn_source=analyse.bpmn_source,
        avertissements=analyse.avertissements,
    )


@router.post("/generer", response_model=FluxOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
async def generer(
    data: GenererFluxIn,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_tenant: Annotated[Tenant, Depends(get_current_tenant)],
):
    """
    Étape 2 — Génère le Flux + FluxEtape en base à partir du mapping validé par l'admin.
    Le mapping associe chaque lane_id à un poste_id réel de la base.
    L'ordre des étapes suit ordre_lanes (topologique ou modifié par l'admin).
    """
    # Vérifier que tous les postes existent
    mapping_index = {m.lane_id: m for m in data.mapping}
    poste_ids = [m.poste_id for m in data.mapping]
    result = await db.execute(
        select(Poste).where(
            Poste.id.in_(poste_ids),
            tenant_scope_condition(Poste.tenant_id, current_tenant.id),
        )
    )
    postes_trouves = {p.id for p in result.scalars().all()}
    manquants = set(poste_ids) - postes_trouves
    if manquants:
        raise HTTPException(status_code=422, detail=f"Postes introuvables : {list(manquants)}")

    # Créer le Flux
    flux = Flux(nom=data.nom, description=data.description, bpmn_source=data.bpmn_source, tenant_id=current_tenant.id)
    db.add(flux)
    await db.flush()

    # Créer les FluxEtape dans l'ordre fourni
    ordre_effectif = data.ordre_lanes or [m.lane_id for m in data.mapping]
    for i, lane_id in enumerate(ordre_effectif, start=1):
        mapping = mapping_index.get(lane_id)
        if mapping is None:
            continue
        is_terminal = (i == len(ordre_effectif))
        etape = FluxEtape(
            flux_id=flux.id,
            ordre=i,
            poste_id=mapping.poste_id,
            type_action=mapping.type_action,
            is_terminal=is_terminal,
        )
        db.add(etape)

    await db.commit()

    result = await db.execute(
        select(Flux)
        .options(selectinload(Flux.etapes).selectinload(FluxEtape.poste))
        .where(Flux.id == flux.id, tenant_scope_condition(Flux.tenant_id, current_tenant.id))
    )
    return result.scalar_one()
