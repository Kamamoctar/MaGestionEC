import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Dossier(Base):
    __tablename__ = "dossier"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=True, index=True)
    titre: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_by_id: Mapped[str] = mapped_column(String(36), ForeignKey("utilisateur.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="dossiers")
    created_by: Mapped["Utilisateur"] = relationship("Utilisateur")
    courriers: Mapped[list["Courrier"]] = relationship("Courrier", back_populates="dossier")
