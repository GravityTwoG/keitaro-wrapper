"""Add campaign offer editor state

Revision ID: 0001_campaign_editor
Revises:
Create Date: 2026-11-22

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_campaign_editor"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    offer_status = sa.Enum(
        "active",
        "pending",
        "removed",
        "archived",
        name="campaign_offer_status",
        native_enum=False,
        length=20,
        create_constraint=True,
    )
    baseline_status = sa.Enum(
        "active",
        "pending",
        "removed",
        "archived",
        name="campaign_offer_baseline_status",
        native_enum=False,
        length=20,
        create_constraint=True,
    )

    op.create_table(
        "campaign_streams",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("stream_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("has_offers", sa.Boolean(), nullable=False),
        sa.Column("dirty", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_streams")),
        sa.UniqueConstraint("stream_id", name="uq_campaign_streams_stream"),
    )
    op.create_index(
        op.f("ix_campaign_streams_campaign_id"),
        "campaign_streams",
        ["campaign_id"],
        unique=False,
    )

    op.create_table(
        "campaign_offers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stream_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("offer_name", sa.String(length=255), nullable=False),
        sa.Column("status", offer_status, nullable=False),
        sa.Column("share", sa.Integer(), nullable=False),
        sa.Column("pinned_share", sa.Integer(), nullable=True),
        sa.Column("baseline_status", baseline_status, nullable=True),
        sa.Column("baseline_share", sa.Integer(), nullable=True),
        sa.Column("baseline_pinned_share", sa.Integer(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["stream_id"],
            ["campaign_streams.id"],
            name=op.f("fk_campaign_offers_stream_id_campaign_streams"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_campaign_offers")),
        sa.UniqueConstraint("stream_id", "offer_id", name="uq_campaign_offers_stream_offer"),
    )
    op.create_index(
        op.f("ix_campaign_offers_stream_id"),
        "campaign_offers",
        ["stream_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_campaign_offers_stream_id"), table_name="campaign_offers")
    op.drop_table("campaign_offers")
    op.drop_index(op.f("ix_campaign_streams_campaign_id"), table_name="campaign_streams")
    op.drop_table("campaign_streams")
