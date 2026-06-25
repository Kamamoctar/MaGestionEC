import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TypeAffectation(str, enum.Enum):
    titulaire = "titulaire"
    interim = "interim"
    delegation = "delegation"


class PosteAffectation(Base):
    """Historique complet des occupants d'un poste (titulaires, intérims, délégations)."""
    __tablename__ = "poste_affectation"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    poste_id: Mapped[str] = mapped_column(String(36), ForeignKey("poste.id"), index=True)
    utilisateur_id: Mapped[str] = mapped_column(String(36), ForeignKey("utilisateur.id"), index=True)
    date_debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    # date_fin null = affectation encore active
    date_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    type: Mapped[TypeAffectation] = mapped_column(SAEnum(TypeAffectation), default=TypeAffectation.titulaire)

    poste: Mapped["Poste"] = relationship("Poste", back_populates="affectations")
    utilisateur: Mapped["Utilisateur"] = relationship("Utilisateur", back_populates="affectations")
