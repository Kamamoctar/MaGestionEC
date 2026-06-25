from datetime import datetime
from pydantic import BaseModel

from app.models.courrier import TypeCourrier, PrioriteCourrier, ConfidentialiteCourrier, EtatCourrier


class CourrierCreate(BaseModel):
    objet: str
    expediteur: str
    poste_destinataire_id: str
    type: TypeCourrier
    priorite: PrioriteCourrier = PrioriteCourrier.normal
    confidentialite: ConfidentialiteCourrier = ConfidentialiteCourrier.normal
    date_limite: datetime | None = None
    flux_id: str | None = None


class CourrierUpdate(BaseModel):
    objet: str | None = None
    expediteur: str | None = None
    priorite: PrioriteCourrier | None = None
    confidentialite: ConfidentialiteCourrier | None = None
    date_limite: datetime | None = None
    etat: EtatCourrier | None = None


class CourrierOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    reference: str
    objet: str
    expediteur: str
    poste_destinataire_id: str
    type: TypeCourrier
    priorite: PrioriteCourrier
    confidentialite: ConfidentialiteCourrier
    date_reception: datetime
    date_limite: datetime | None
    etat: EtatCourrier
    flux_id: str | None
    etape_courante_id: str | None
    created_by_id: str
    created_at: datetime
    updated_at: datetime


class TransmettreCourrierIn(BaseModel):
    poste_destination_id: str
    commentaire: str | None = None
