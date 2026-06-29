import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.utilisateur import RoleFonctionnel


class Tenant(Base):
    """Organisation isolee dans l'application GEC."""

    __tablename__ = "tenant"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    membres: Mapped[list["TenantMembre"]] = relationship("TenantMembre", back_populates="tenant", cascade="all, delete-orphan")
    directions: Mapped[list["Direction"]] = relationship("Direction", back_populates="tenant")
    postes: Mapped[list["Poste"]] = relationship("Poste", back_populates="tenant")
    flux: Mapped[list["Flux"]] = relationship("Flux", back_populates="tenant")
    dossiers: Mapped[list["Dossier"]] = relationship("Dossier", back_populates="tenant")


class TenantMembre(Base):
    """Role fonctionnel d'une personne dans un tenant donne."""

    __tablename__ = "tenant_membre"
    __table_args__ = (UniqueConstraint("tenant_id", "utilisateur_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenant.id", ondelete="CASCADE"), index=True)
    utilisateur_id: Mapped[str] = mapped_column(String(36), ForeignKey("utilisateur.id", ondelete="CASCADE"), index=True)
    role_fonctionnel: Mapped[RoleFonctionnel] = mapped_column(SAEnum(RoleFonctionnel), default=RoleFonctionnel.agent)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="membres")
    utilisateur: Mapped["Utilisateur"] = relationship("Utilisateur", back_populates="tenants")
