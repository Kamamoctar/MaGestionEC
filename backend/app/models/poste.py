import uuid
import enum

from sqlalchemy import String, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NiveauAcces(str, enum.Enum):
    normal = "normal"
    confidentiel = "confidentiel"


class Poste(Base):
    __tablename__ = "poste"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=True, index=True)
    intitule: Mapped[str] = mapped_column(String(200))
    direction_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("direction.id"), nullable=True)
    # L'occupant courant — simple attribut dynamique, PAS la personne propriétaire des courriers
    occupant_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("utilisateur.id"), nullable=True)
    niveau_acces: Mapped[NiveauAcces] = mapped_column(SAEnum(NiveauAcces), default=NiveauAcces.normal)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relations
    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="postes")
    direction: Mapped["Direction | None"] = relationship("Direction", back_populates="postes")
    occupant: Mapped["Utilisateur | None"] = relationship("Utilisateur", back_populates="postes_occupes", foreign_keys=[occupant_user_id])
    affectations: Mapped[list["PosteAffectation"]] = relationship("PosteAffectation", back_populates="poste", cascade="all, delete-orphan")
    courriers_recus: Mapped[list["Courrier"]] = relationship("Courrier", back_populates="poste_destinataire", foreign_keys="Courrier.poste_destinataire_id")
    etapes_flux: Mapped[list["FluxEtape"]] = relationship("FluxEtape", back_populates="poste")
    mouvements_source: Mapped[list["Mouvement"]] = relationship("Mouvement", back_populates="poste_source", foreign_keys="Mouvement.poste_source_id")
    mouvements_destination: Mapped[list["Mouvement"]] = relationship("Mouvement", back_populates="poste_destination", foreign_keys="Mouvement.poste_destination_id")
