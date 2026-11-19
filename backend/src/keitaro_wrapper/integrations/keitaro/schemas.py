from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class KeitaroModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Campaign(KeitaroModel):
    id: int
    name: str = ""
    alias: str = ""
    state: str = "active"
    group_id: int | None = None
    traffic_source_id: int | None = None
    domain_id: int | None = None


class CampaignWrite(KeitaroModel):
    name: str
    alias: str
    type: str = "position"
    state: str = "active"
    cost_type: str = "CPC"
    cost_value: float = 0
    group_id: int | None = None
    traffic_source_id: int | None = None
    domain_id: int | None = None


class StreamFilter(KeitaroModel):
    id: int | None = None
    name: str
    mode: str = "accept"
    payload: Any = None


class StreamOffer(KeitaroModel):
    offer_id: int
    share: int = 100
    state: str = "active"


class StreamLanding(KeitaroModel):
    landing_id: int
    share: int = 100
    state: str = "active"


class StreamTrigger(KeitaroModel):
    id: int | None = None
    stream_id: int | None = None
    condition: str
    target: str
    action: str
    selected_page: str | None = None
    pattern: str | None = None
    interval: int | None = None
    alternative_urls: str | None = None
    grab_from_page: str | None = None
    av_settings: str | None = None
    reverse: bool | None = None
    scan_page: bool | None = None


class Stream(KeitaroModel):
    id: int
    campaign_id: int
    name: str = ""
    type: str = "regular"
    position: int | None = None
    weight: float | None = None
    state: str = "active"
    action_type: str | None = None
    action_payload: Any = None
    action_options: dict[str, Any] | None = None
    comments: str | None = None
    schema_: str = Field(default="landings", alias="schema")
    collect_clicks: bool = False
    filter_or: bool = False
    filters: list[StreamFilter] = Field(default_factory=list)
    offers: list[StreamOffer] = Field(default_factory=list)
    landings: list[StreamLanding] = Field(default_factory=list)
    triggers: list[StreamTrigger] = Field(default_factory=list)


class StreamWrite(KeitaroModel):
    campaign_id: int
    name: str
    type: Literal["regular", "forced", "default"] = "regular"
    position: int | None = None
    weight: float | None = None
    state: str = "active"
    action_type: str = "http"
    action_payload: Any = None
    action_options: dict[str, Any] | None = None
    comments: str | None = None
    schema_: Literal["redirect", "landings", "action"] = Field(default="landings", alias="schema")
    collect_clicks: bool = True
    filter_or: bool = False
    filters: list[StreamFilter] = Field(default_factory=list)
    offers: list[StreamOffer] = Field(default_factory=list)
    landings: list[StreamLanding] = Field(default_factory=list)
    triggers: list[StreamTrigger] = Field(default_factory=list)


class Offer(KeitaroModel):
    id: int
    name: str = ""
    state: str = "active"
    payout_value: float | None = None
    payout_currency: str | None = None
    country: list[str] | None = None


class Domain(KeitaroModel):
    id: int
    name: str = ""
    state: str = "active"


class Group(KeitaroModel):
    id: int
    name: str = ""


class TrafficSource(KeitaroModel):
    id: int
    name: str = ""
    state: str = "active"
