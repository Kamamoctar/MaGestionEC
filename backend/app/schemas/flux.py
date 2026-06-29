from pydantic import BaseModel

from app.models.flux import TypeAction


class FluxEtapeCreate(BaseModel):
    ordre: int
    poste_id: str
    type_action: TypeAction
    condition_transition: str | None = None
    is_terminal: bool = False


class FluxCreate(BaseModel):
    nom: str
    description: str | None = None
    etapes: list[FluxEtapeCreate] = []


class FluxEtapeOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    flux_id: str
    ordre: int
    poste_id: str
    intitule_poste: str | None = None
    type_action: TypeAction
    condition_transition: str | None
    is_terminal: bool


class FluxOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    tenant_id: str | None = None
    nom: str
    description: str | None
    etapes: list[FluxEtapeOut] = []
