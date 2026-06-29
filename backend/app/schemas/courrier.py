from datetime import datetime
from typing import Literal
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
    reference_expediteur: str | None = None
    courrier_parent_id: str | None = None
    dossier_id: str | None = None


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
    reference_expediteur: str | None
    poste_destinataire_id: str
    type: TypeCourrier
    priorite: PrioriteCourrier
    confidentialite: ConfidentialiteCourrier
    date_reception: datetime
    date_limite: datetime | None
    etat: EtatCourrier
    flux_id: str | None
    etape_courante_id: str | None
    type_action_courante: str | None = None
    courrier_parent_id: str | None
    dossier_id: str | None
    created_by_id: str
    created_at: datetime
    updated_at: datetime


class CourrierLiaisonOut(BaseModel):
    """Résumé léger pour l'affichage du fil de correspondance (sans contrôle d'accès complet)."""
    model_config = {"from_attributes": True}

    id: str
    reference: str
    objet: str
    type: TypeCourrier
    etat: EtatCourrier
    priorite: PrioriteCourrier
    date_reception: datetime
    expediteur: str


class TransmettreCourrierIn(BaseModel):
    poste_destination_id: str
    commentaire: str | None = None


class ActionCourrierIn(BaseModel):
    action: Literal["visa", "signature", "annotation", "retour"]
    commentaire: str | None = None
