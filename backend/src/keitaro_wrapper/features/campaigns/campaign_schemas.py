from __future__ import annotations

import re
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

CampaignName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]

_COUNTRY_CODE = re.compile(r"^[A-Z]{2}$")


def normalize_geo(value: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw in value:
        for chunk in raw.replace(";", ",").split(","):
            code = chunk.strip().upper()
            if not code:
                continue
            if not _COUNTRY_CODE.match(code):
                raise ValueError(f"Некорректный ISO-2 код страны: {code}")
            if code not in normalized:
                normalized.append(code)
    if not normalized:
        raise ValueError("Укажите хотя бы одну страну")
    if len(normalized) > 20:
        raise ValueError("Можно указать не больше 20 стран")
    return normalized


class CreateCampaignRequest(BaseModel):
    name: CampaignName
    geo: list[str] = Field(min_length=1)
    offer_id: int = Field(gt=0)

    @field_validator("geo")
    @classmethod
    def _validate_geo(cls, value: list[str]) -> list[str]:
        return normalize_geo(value)


class CampaignSummary(BaseModel):
    id: int
    name: str
    alias: str
    state: str


class CampaignListResponse(BaseModel):
    items: list[CampaignSummary] = Field(default_factory=list)
    offset: int
    has_more: bool


class OfferSearchItem(BaseModel):
    id: int
    name: str
    payout_value: float | None = None
    payout_currency: str | None = None
    country: list[str] = Field(default_factory=list)


class OfferSearchResponse(BaseModel):
    items: list[OfferSearchItem] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    has_more: bool = False
