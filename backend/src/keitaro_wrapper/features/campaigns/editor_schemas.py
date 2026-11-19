from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CampaignOfferStatusValue = Literal["active", "pending", "removed", "archived"]


class CampaignOfferView(BaseModel):
    offer_id: int
    name: str
    share: int
    pinned_share: int | None = None
    status: CampaignOfferStatusValue
    can_remove: bool
    can_restore: bool


class CampaignStreamView(BaseModel):
    stream_id: int
    name: str
    position: int
    has_offers: bool
    dirty: bool
    offers: list[CampaignOfferView] = Field(default_factory=list)


class CampaignEditorView(BaseModel):
    loaded: bool
    dirty: bool
    streams: list[CampaignStreamView] = Field(default_factory=list)


class AddCampaignOfferRequest(BaseModel):
    offer_id: int = Field(gt=0)


class PinCampaignOfferRequest(BaseModel):
    pinned: bool
