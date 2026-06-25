from pydantic import BaseModel


class DirectionCreate(BaseModel):
    nom: str
    description: str | None = None


class DirectionUpdate(BaseModel):
    nom: str | None = None
    description: str | None = None


class DirectionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    nom: str
    description: str | None
