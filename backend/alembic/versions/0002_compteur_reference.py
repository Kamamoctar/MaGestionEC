"""Ajout table compteur_reference pour les références séquentielles de courriers.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "compteur_reference",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("annee", sa.Integer(), nullable=False),
        sa.Column("valeur", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type", "annee", name="uq_compteur_type_annee"),
    )


def downgrade() -> None:
    op.drop_table("compteur_reference")
