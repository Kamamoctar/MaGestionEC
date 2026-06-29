from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.models.utilisateur import RoleFonctionnel


class UtilisateurCreate(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    password: str
    role_fonctionnel: RoleFonctionnel = RoleFonctionnel.agent


class UtilisateurUpdate(BaseModel):
    nom: str | None = None
    prenom: str | None = None
    email: EmailStr | None = None
    role_fonctionnel: RoleFonctionnel | None = None
    is_active: bool | None = None


class UtilisateurOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    nom: str
    prenom: str
    email: str
    role_fonctionnel: RoleFonctionnel
    is_active: bool
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    utilisateur: UtilisateurOut
    tenant_id: str | None = None
    tenant_nom: str | None = None
