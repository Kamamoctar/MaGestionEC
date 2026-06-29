import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TypeCourrier(str, enum.Enum):
    arrivee = "arrivee"
    depart = "depart"
    interne = "interne"


class PrioriteCourrier(str, enum.Enum):
    normal = "normal"
    urgent = "urgent"
    tres_urgent = "tres_urgent"


class ConfidentialiteCourrier(str, enum.Enum):
    normal = "normal"
    confidentiel = "confidentiel"


class EtatCourrier(str, enum.Enum):
    en_attente = "en_attente"
    en_cours = "en_cours"
    traite = "traite"
    archive = "archive"


class Courrier(Base):
    __tablename__ = "courrier"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    objet: Mapped[str] = mapped_column(String(500))
    expediteur: Mapped[str] = mapped_column(String(300))

    # Destinataire = POSTE, jamais la personne
    poste_destinataire_id: Mapped[str] = mapped_column(String(36), ForeignKey("poste.id"), index=True)

    type: Mapped[TypeCourrier] = mapped_column(SAEnum(TypeCourrier))
    priorite: Mapped[PrioriteCourrier] = mapped_column(SAEnum(PrioriteCourrier), default=PrioriteCourrier.normal)
    confidentialite: Mapped[ConfidentialiteCourrier] = mapped_column(SAEnum(ConfidentialiteCourrier), default=ConfidentialiteCourrier.normal)
    date_reception: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    date_limite: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    etat: Mapped[EtatCourrier] = mapped_column(SAEnum(EtatCourrier), default=EtatCourrier.en_attente)

    reference_expediteur: Mapped[str | None] = mapped_column(String(100), nullable=True)
    courrier_parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("courrier.id", ondelete="SET NULL"), nullable=True)
    dossier_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("dossier.id", ondelete="SET NULL"), nullable=True)

    flux_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("flux.id"), nullable=True)
    etape_courante_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("flux_etape.id"), nullable=True)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("utilisateur.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    @property
    def type_action_courante(self) -> str | None:
        """Retourne le type_action de l'étape courante si le circuit est chargé."""
        etape = self.__dict__.get("etape_courante")
        return etape.type_action if etape is not None else None

    # Relations
    poste_destinataire: Mapped["Poste"] = relationship("Poste", back_populates="courriers_recus", foreign_keys=[poste_destinataire_id])
    flux: Mapped["Flux | None"] = relationship("Flux", back_populates="courriers")
    etape_courante: Mapped["FluxEtape | None"] = relationship("FluxEtape", back_populates="courriers_en_cours", foreign_keys=[etape_courante_id])
    created_by: Mapped["Utilisateur"] = relationship("Utilisateur")
    pieces_jointes: Mapped[list["PieceJointe"]] = relationship("PieceJointe", back_populates="courrier", cascade="all, delete-orphan")
    mouvements: Mapped[list["Mouvement"]] = relationship("Mouvement", back_populates="courrier", order_by="Mouvement.created_at")

    parent: Mapped["Courrier | None"] = relationship("Courrier", back_populates="reponses", remote_side="Courrier.id", foreign_keys=[courrier_parent_id])
    reponses: Mapped[list["Courrier"]] = relationship("Courrier", back_populates="parent", foreign_keys=[courrier_parent_id])
    dossier: Mapped["Dossier | None"] = relationship("Dossier", back_populates="courriers")
