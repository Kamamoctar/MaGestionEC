import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RoleFonctionnel(str, enum.Enum):
    admin = "admin"
    secretariat = "secretariat"
    agent = "agent"
    direction = "direction"


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(100))
    prenom: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role_fonctionnel: Mapped[RoleFonctionnel] = mapped_column(SAEnum(RoleFonctionnel), default=RoleFonctionnel.agent)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relations
    tenants: Mapped[list["TenantMembre"]] = relationship("TenantMembre", back_populates="utilisateur", cascade="all, delete-orphan")
    postes_occupes: Mapped[list["Poste"]] = relationship("Poste", back_populates="occupant", foreign_keys="Poste.occupant_user_id")
    affectations: Mapped[list["PosteAffectation"]] = relationship("PosteAffectation", back_populates="utilisateur")
    mouvements: Mapped[list["Mouvement"]] = relationship("Mouvement", back_populates="utilisateur")
