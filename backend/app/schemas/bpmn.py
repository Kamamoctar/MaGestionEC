from pydantic import BaseModel

from app.models.flux import TypeAction


class LaneDetecteOut(BaseModel):
    lane_id: str
    lane_name: str
    taches: list[str]
    type_action_propose: TypeAction


class BpmnAnalyseOut(BaseModel):
    nom_processus: str
    lanes: list[LaneDetecteOut]
    ordre_lanes: list[str]
    bpmn_source: str
    avertissements: list[str]


class MappingLane(BaseModel):
    lane_id: str
    poste_id: str
    type_action: TypeAction


class GenererFluxIn(BaseModel):
    nom: str
    description: str | None = None
    bpmn_source: str
    mapping: list[MappingLane]
    ordre_lanes: list[str]
