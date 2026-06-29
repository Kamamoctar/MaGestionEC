from pydantic import BaseModel

from app.models.poste import NiveauAcces
from app.models.poste_affectation import TypeAffectation
from app.schemas.utilisateur import UtilisateurOut


class PosteCreate(BaseModel):
    intitule: str
    direction_id: str | None = None
    niveau_acces: NiveauAcces = NiveauAcces.normal


class PosteUpdate(BaseModel):
    intitule: str | None = None
    direction_id: str | None = None
    niveau_acces: NiveauAcces | None = None
    is_active: bool | None = None


class PosteOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    tenant_id: str | None = None
    intitule: str
    direction_id: str | None
    occupant_user_id: str | None
    niveau_acces: NiveauAcces
    is_active: bool


class PosteDetailOut(PosteOut):
    occupant: UtilisateurOut | None = None


class AffectationOccupantIn(BaseModel):
    utilisateur_id: str
    type: TypeAffectation = TypeAffectation.titulaire


class InterimaireIn(BaseModel):
    utilisateur_id: str


class DelegationIn(BaseModel):
    utilisateur_id: str
