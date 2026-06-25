import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PieceJointe(Base):
    """Référence vers un fichier stocké HORS base (disque/S3). Jamais le binaire en base."""
    __tablename__ = "piece_jointe"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    courrier_id: Mapped[str] = mapped_column(String(36), ForeignKey("courrier.id"), index=True)
    nom_fichier: Mapped[str] = mapped_column(String(255))
    chemin_stockage: Mapped[str] = mapped_column(String(1000))
    taille_octets: Mapped[int] = mapped_column(Integer)
    mime_type: Mapped[str] = mapped_column(String(100))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    courrier: Mapped["Courrier"] = relationship("Courrier", back_populates="pieces_jointes")
