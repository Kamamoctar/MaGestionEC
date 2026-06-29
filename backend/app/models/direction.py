import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Direction(Base):
    __tablename__ = "direction"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=True, index=True)
    nom: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="directions")
    postes: Mapped[list["Poste"]] = relationship("Poste", back_populates="direction")
