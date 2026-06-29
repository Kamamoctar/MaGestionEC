from datetime import datetime

from pydantic import BaseModel


class TenantOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    nom: str
    slug: str
    is_active: bool
    created_at: datetime
