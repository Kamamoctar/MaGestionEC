import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TypeAction(str, enum.Enum):
    distribution = "distribution"
    visa = "visa"
    signature = "signature"
    information = "information"


class Flux(Base):
    """Circuit de traitement issu d'un import BPMN."""
    __tablename__ = "flux"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bpmn_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    etapes: Mapped[list["FluxEtape"]] = relationship("FluxEtape", back_populates="flux", order_by="FluxEtape.ordre", cascade="all, delete-orphan")
    courriers: Mapped[list["Courrier"]] = relationship("Courrier", back_populates="flux")


class FluxEtape(Base):
    __tablename__ = "flux_etape"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flux_id: Mapped[str] = mapped_column(String(36), ForeignKey("flux.id"), index=True)
    ordre: Mapped[int] = mapped_column(Integer)
    poste_id: Mapped[str] = mapped_column(String(36), ForeignKey("poste.id"))
    type_action: Mapped[TypeAction] = mapped_column(SAEnum(TypeAction))
    condition_transition: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_terminal: Mapped[bool] = mapped_column(Boolean, default=False)

    flux: Mapped["Flux"] = relationship("Flux", back_populates="etapes")
    poste: Mapped["Poste"] = relationship("Poste", back_populates="etapes_flux")
    courriers_en_cours: Mapped[list["Courrier"]] = relationship("Courrier", back_populates="etape_courante", foreign_keys="Courrier.etape_courante_id")
    mouvements: Mapped[list["Mouvement"]] = relationship("Mouvement", back_populates="flux_etape")
