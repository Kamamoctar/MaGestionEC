"""Ajout du multi-tenant et de l'envoi inter-tenant.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

DEFAULT_TENANT_ID = "00000000-0000-4000-8000-000000000001"


def upgrade() -> None:
    op.create_table(
        "tenant",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nom", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("slug", name="uq_tenant_slug"),
    )
    op.create_index("ix_tenant_slug", "tenant", ["slug"])

    op.create_table(
        "tenant_membre",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("utilisateur_id", sa.String(36), nullable=False),
        sa.Column("role_fonctionnel", sa.Enum("admin", "secretariat", "agent", "direction", name="rolefonctionnel", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], name="fk_tenant_membre_tenant", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["utilisateur_id"], ["utilisateur.id"], name="fk_tenant_membre_utilisateur", ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "utilisateur_id", name="uq_tenant_membre_tenant_user"),
    )
    op.create_index("ix_tenant_membre_tenant_id", "tenant_membre", ["tenant_id"])
    op.create_index("ix_tenant_membre_utilisateur_id", "tenant_membre", ["utilisateur_id"])

    op.execute(
        sa.text(
            "INSERT INTO tenant (id, nom, slug, is_active, created_at) "
            "VALUES (:id, 'Tenant legacy', 'legacy', true, now())"
        ).bindparams(id=DEFAULT_TENANT_ID)
    )
    op.execute(
        sa.text(
            "INSERT INTO tenant_membre (id, tenant_id, utilisateur_id, role_fonctionnel, is_active, created_at) "
            "SELECT id, :tenant_id, id, role_fonctionnel, true, now() FROM utilisateur"
        ).bindparams(tenant_id=DEFAULT_TENANT_ID)
    )

    for table_name in ["direction", "poste", "flux", "dossier", "courrier", "compteur_reference"]:
        op.add_column(table_name, sa.Column("tenant_id", sa.String(36), nullable=True))
        op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"])
        op.create_foreign_key(f"fk_{table_name}_tenant", table_name, "tenant", ["tenant_id"], ["id"])
        op.execute(sa.text(f"UPDATE {table_name} SET tenant_id = :tenant_id").bindparams(tenant_id=DEFAULT_TENANT_ID))

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_constraint("direction_nom_key", "direction", type_="unique")

    op.drop_constraint("uq_compteur_type_annee", "compteur_reference", type_="unique")
    op.create_unique_constraint(
        "uq_compteur_tenant_type_annee",
        "compteur_reference",
        ["tenant_id", "type", "annee"],
    )

    op.add_column("courrier", sa.Column("courrier_lie_id", sa.String(36), nullable=True))
    op.add_column("courrier", sa.Column("tenant_expediteur_id", sa.String(36), nullable=True))
    op.add_column("courrier", sa.Column("tenant_destinataire_id", sa.String(36), nullable=True))
    op.create_foreign_key("fk_courrier_lie", "courrier", "courrier", ["courrier_lie_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_courrier_tenant_expediteur", "courrier", "tenant", ["tenant_expediteur_id"], ["id"])
    op.create_foreign_key("fk_courrier_tenant_destinataire", "courrier", "tenant", ["tenant_destinataire_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_courrier_tenant_destinataire", "courrier", type_="foreignkey")
    op.drop_constraint("fk_courrier_tenant_expediteur", "courrier", type_="foreignkey")
    op.drop_constraint("fk_courrier_lie", "courrier", type_="foreignkey")
    op.drop_column("courrier", "tenant_destinataire_id")
    op.drop_column("courrier", "tenant_expediteur_id")
    op.drop_column("courrier", "courrier_lie_id")

    op.drop_constraint("uq_compteur_tenant_type_annee", "compteur_reference", type_="unique")
    op.create_unique_constraint("uq_compteur_type_annee", "compteur_reference", ["type", "annee"])

    for table_name in ["compteur_reference", "courrier", "dossier", "flux", "poste", "direction"]:
        op.drop_constraint(f"fk_{table_name}_tenant", table_name, type_="foreignkey")
        op.drop_index(f"ix_{table_name}_tenant_id", table_name=table_name)
        op.drop_column(table_name, "tenant_id")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_unique_constraint("direction_nom_key", "direction", ["nom"])

    op.drop_index("ix_tenant_membre_utilisateur_id", table_name="tenant_membre")
    op.drop_index("ix_tenant_membre_tenant_id", table_name="tenant_membre")
    op.drop_table("tenant_membre")
    op.drop_index("ix_tenant_slug", table_name="tenant")
    op.drop_table("tenant")
