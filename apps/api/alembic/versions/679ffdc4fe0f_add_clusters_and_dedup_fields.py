"""add clusters and dedup fields

Revision ID: 679ffdc4fe0f
Revises: 79d898738194
Create Date: 2026-03-28 02:46:10.905560

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "679ffdc4fe0f"
down_revision: Union[str, Sequence[str], None] = "79d898738194"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create incident_clusters table
    op.create_table(
        "incident_clusters",
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("incident_count", sa.Integer(), nullable=False),
        sa.Column("max_severity_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("primary_service", sa.String(length=200), nullable=True),
        sa.Column("primary_source", sa.String(length=100), nullable=True),
        sa.Column("primary_environment", sa.String(length=50), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_incident_clusters_fingerprint"),
        "incident_clusters",
        ["fingerprint"],
        unique=True,
    )

    # Add new columns to incidents
    op.add_column(
        "incidents",
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("incidents", sa.Column("duplicate_of", sa.UUID(), nullable=True))
    op.add_column("incidents", sa.Column("similarity_score", sa.Float(), nullable=True))

    # Drop old cluster_id (was VARCHAR) and create new one (UUID with FK)
    op.drop_index("ix_incidents_cluster_id", table_name="incidents")
    op.drop_column("incidents", "cluster_id")
    op.add_column("incidents", sa.Column("cluster_id", sa.UUID(), nullable=True))
    op.create_index(
        op.f("ix_incidents_cluster_id"), "incidents", ["cluster_id"], unique=False
    )
    op.create_foreign_key(
        "fk_incidents_cluster_id",
        "incidents",
        "incident_clusters",
        ["cluster_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop FK and new cluster_id, restore old VARCHAR version
    op.drop_constraint("fk_incidents_cluster_id", "incidents", type_="foreignkey")
    op.drop_index(op.f("ix_incidents_cluster_id"), table_name="incidents")
    op.drop_column("incidents", "cluster_id")
    op.add_column(
        "incidents",
        sa.Column("cluster_id", sa.VARCHAR(length=64), nullable=True),
    )
    op.create_index("ix_incidents_cluster_id", "incidents", ["cluster_id"], unique=False)

    # Drop dedup columns
    op.drop_column("incidents", "similarity_score")
    op.drop_column("incidents", "duplicate_of")
    op.drop_column("incidents", "is_duplicate")

    # Drop clusters table
    op.drop_index(op.f("ix_incident_clusters_fingerprint"), table_name="incident_clusters")
    op.drop_table("incident_clusters")
