from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from keitaro_wrapper.core.db_base import Base


class CampaignOfferStatus(enum.StrEnum):
    ACTIVE = "active"
    PENDING = "pending"
    REMOVED = "removed"
    ARCHIVED = "archived"


def _status_enum(name: str) -> Enum:
    return Enum(
        CampaignOfferStatus,
        name=name,
        native_enum=False,
        length=20,
        values_callable=lambda items: [item.value for item in items],
    )


class CampaignStream(Base):
    __tablename__ = "campaign_streams"
    __table_args__ = (UniqueConstraint("stream_id", name="uq_campaign_streams_stream"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    stream_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    has_offers: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dirty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    offers: Mapped[list[CampaignOffer]] = relationship(
        back_populates="stream",
        cascade="all, delete-orphan",
        order_by="CampaignOffer.order_index",
        lazy="selectin",
    )


class CampaignOffer(Base):
    __tablename__ = "campaign_offers"
    __table_args__ = (UniqueConstraint("stream_id", "offer_id", name="uq_campaign_offers_stream_offer"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stream_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaign_streams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    offer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    offer_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[CampaignOfferStatus] = mapped_column(
        _status_enum("campaign_offer_status"),
        nullable=False,
        default=CampaignOfferStatus.ACTIVE,
    )
    share: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pinned_share: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_status: Mapped[CampaignOfferStatus | None] = mapped_column(
        _status_enum("campaign_offer_baseline_status"),
        nullable=True,
    )
    baseline_share: Mapped[int | None] = mapped_column(Integer, nullable=True)
    baseline_pinned_share: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    stream: Mapped[CampaignStream] = relationship(back_populates="offers")
