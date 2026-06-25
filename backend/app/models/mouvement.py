import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ActionMouvement(str, enum.Enum):
    creation = "creation"
    transmission = "transmission"
    visa = "visa"
    signature = "signature"
    annotation = "annotation"
    retour = "retour"
    archive = "archive"


class Mouvement(Base):
    """Log immuable — chaque passage d'un courrier d'un poste à un autre est enregistré ici."""
    __tablename__ = "mouvement"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    courrier_id: Mapped[str] = mapped_column(String(36), ForeignKey("courrier.id"), index=True)
    flux_etape_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("flux_etape.id"), nullable=True)
    poste_source_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("poste.id"), nullable=True)
    poste_destination_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("poste.id"), nullable=True)
    utilisateur_id: Mapped[str] = mapped_column(String(36), ForeignKey("utilisateur.id"))
    action: Mapped[ActionMouvement] = mapped_column(SAEnum(ActionMouvement))
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    courrier: Mapped["Courrier"] = relationship("Courrier", back_populates="mouvements")
    flux_etape: Mapped["FluxEtape | None"] = relationship("FluxEtape", back_populates="mouvements")
    poste_source: Mapped["Poste | None"] = relationship("Poste", back_populates="mouvements_source", foreign_keys=[poste_source_id])
    poste_destination: Mapped["Poste | None"] = relationship("Poste", back_populates="mouvements_destination", foreign_keys=[poste_destination_id])
    utilisateur: Mapped["Utilisateur"] = relationship("Utilisateur", back_populates="mouvements")
