import enum

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TypeCourrier(str, enum.Enum):
    arrivee = "arrivee"
    depart = "depart"
    interne = "interne"


class CompteurReference(Base):
    """Compteur séquentiel de références de courriers par type et par année."""
    __tablename__ = "compteur_reference"
    __table_args__ = (UniqueConstraint("tenant_id", "type", "annee"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("tenant.id"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(20))
    annee: Mapped[int] = mapped_column(Integer)
    valeur: Mapped[int] = mapped_column(Integer, default=0)
