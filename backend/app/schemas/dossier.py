from datetime import datetime
from pydantic import BaseModel


class DossierCreate(BaseModel):
    titre: str
    description: str | None = None


class DossierUpdate(BaseModel):
    titre: str | None = None
    description: str | None = None


class DossierOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    tenant_id: str | None = None
    titre: str
    description: str | None
    created_by_id: str
    created_at: datetime
    nb_courriers: int = 0
