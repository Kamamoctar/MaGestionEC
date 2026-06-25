"""Migration initiale — toutes les tables GEC

Revision ID: 0001
Revises:
Create Date: 2026-06-25
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "direction",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nom", sa.String(200), nullable=False, unique=True),
        sa.Column("description", sa.String(500), nullable=True),
    )

    op.create_table(
        "utilisateur",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nom", sa.String(100), nullable=False),
        sa.Column("prenom", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role_fonctionnel", sa.Enum("admin", "secretariat", "agent", "direction", name="rolefonctionnel"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_utilisateur_email", "utilisateur", ["email"])

    op.create_table(
        "poste",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("intitule", sa.String(200), nullable=False),
        sa.Column("direction_id", sa.String(36), sa.ForeignKey("direction.id"), nullable=True),
        sa.Column("occupant_user_id", sa.String(36), sa.ForeignKey("utilisateur.id"), nullable=True),
        sa.Column("niveau_acces", sa.Enum("normal", "confidentiel", name="niveauacces"), nullable=False, server_default="normal"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )

    op.create_table(
        "poste_affectation",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("poste_id", sa.String(36), sa.ForeignKey("poste.id"), nullable=False),
        sa.Column("utilisateur_id", sa.String(36), sa.ForeignKey("utilisateur.id"), nullable=False),
        sa.Column("date_debut", sa.DateTime(timezone=True), nullable=False),
        sa.Column("date_fin", sa.DateTime(timezone=True), nullable=True),
        sa.Column("type", sa.Enum("titulaire", "interim", "delegation", name="typeaffectation"), nullable=False, server_default="titulaire"),
    )
    op.create_index("ix_poste_affectation_poste_id", "poste_affectation", ["poste_id"])
    op.create_index("ix_poste_affectation_utilisateur_id", "poste_affectation", ["utilisateur_id"])

    op.create_table(
        "flux",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("nom", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("bpmn_source", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "flux_etape",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("flux_id", sa.String(36), sa.ForeignKey("flux.id"), nullable=False),
        sa.Column("ordre", sa.Integer(), nullable=False),
        sa.Column("poste_id", sa.String(36), sa.ForeignKey("poste.id"), nullable=False),
        sa.Column("type_action", sa.Enum("distribution", "visa", "signature", "information", name="typeaction"), nullable=False),
        sa.Column("condition_transition", sa.String(500), nullable=True),
        sa.Column("is_terminal", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("ix_flux_etape_flux_id", "flux_etape", ["flux_id"])

    op.create_table(
        "courrier",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("reference", sa.String(50), nullable=False, unique=True),
        sa.Column("objet", sa.String(500), nullable=False),
        sa.Column("expediteur", sa.String(300), nullable=False),
        sa.Column("poste_destinataire_id", sa.String(36), sa.ForeignKey("poste.id"), nullable=False),
        sa.Column("type", sa.Enum("arrivee", "depart", "interne", name="typecourrier"), nullable=False),
        sa.Column("priorite", sa.Enum("normal", "urgent", "tres_urgent", name="prioritecourrier"), nullable=False, server_default="normal"),
        sa.Column("confidentialite", sa.Enum("normal", "confidentiel", name="confidentialitecourrier"), nullable=False, server_default="normal"),
        sa.Column("date_reception", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("date_limite", sa.DateTime(timezone=True), nullable=True),
        sa.Column("etat", sa.Enum("en_attente", "en_cours", "traite", "archive", name="etatcourrier"), nullable=False, server_default="en_attente"),
        sa.Column("flux_id", sa.String(36), sa.ForeignKey("flux.id"), nullable=True),
        sa.Column("etape_courante_id", sa.String(36), sa.ForeignKey("flux_etape.id"), nullable=True),
        sa.Column("created_by_id", sa.String(36), sa.ForeignKey("utilisateur.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_courrier_reference", "courrier", ["reference"])
    op.create_index("ix_courrier_poste_destinataire_id", "courrier", ["poste_destinataire_id"])

    op.create_table(
        "piece_jointe",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("courrier_id", sa.String(36), sa.ForeignKey("courrier.id"), nullable=False),
        sa.Column("nom_fichier", sa.String(255), nullable=False),
        sa.Column("chemin_stockage", sa.String(1000), nullable=False),
        sa.Column("taille_octets", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_piece_jointe_courrier_id", "piece_jointe", ["courrier_id"])

    op.create_table(
        "mouvement",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("courrier_id", sa.String(36), sa.ForeignKey("courrier.id"), nullable=False),
        sa.Column("flux_etape_id", sa.String(36), sa.ForeignKey("flux_etape.id"), nullable=True),
        sa.Column("poste_source_id", sa.String(36), sa.ForeignKey("poste.id"), nullable=True),
        sa.Column("poste_destination_id", sa.String(36), sa.ForeignKey("poste.id"), nullable=True),
        sa.Column("utilisateur_id", sa.String(36), sa.ForeignKey("utilisateur.id"), nullable=False),
        sa.Column("action", sa.Enum("creation", "transmission", "visa", "signature", "annotation", "retour", "archive", name="actionmouvement"), nullable=False),
        sa.Column("commentaire", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mouvement_courrier_id", "mouvement", ["courrier_id"])


def downgrade() -> None:
    op.drop_table("mouvement")
    op.drop_table("piece_jointe")
    op.drop_table("courrier")
    op.drop_table("flux_etape")
    op.drop_table("flux")
    op.drop_table("poste_affectation")
    op.drop_table("poste")
    op.drop_table("utilisateur")
    op.drop_table("direction")

    for enum in ["rolefonctionnel", "niveauacces", "typeaffectation", "typeaction",
                 "typecourrier", "prioritecourrier", "confidentialitecourrier", "etatcourrier", "actionmouvement"]:
        sa.Enum(name=enum).drop(op.get_bind())
