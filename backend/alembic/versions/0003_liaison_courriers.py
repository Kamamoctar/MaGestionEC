"""Liaison entre courriers : reference_expediteur, courrier_parent_id, dossier_id + table dossier.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Table dossier (doit être créée avant la FK sur courrier)
    op.create_table(
        "dossier",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("titre", sa.String(300), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("utilisateur.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Nouveaux champs sur courrier
    op.add_column("courrier", sa.Column("reference_expediteur", sa.String(100), nullable=True))
    op.add_column("courrier", sa.Column(
        "courrier_parent_id", sa.String(36),
        sa.ForeignKey("courrier.id", ondelete="SET NULL"),
        nullable=True,
    ))
    op.add_column("courrier", sa.Column(
        "dossier_id", sa.String(36),
        sa.ForeignKey("dossier.id", ondelete="SET NULL"),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column("courrier", "dossier_id")
    op.drop_column("courrier", "courrier_parent_id")
    op.drop_column("courrier", "reference_expediteur")
    op.drop_table("dossier")
