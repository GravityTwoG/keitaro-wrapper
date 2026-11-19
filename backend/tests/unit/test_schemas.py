from __future__ import annotations

import pytest
from pydantic import ValidationError

from keitaro_wrapper.features.campaigns.campaign_schemas import CreateCampaignRequest, normalize_geo


def test_normalize_geo_uppercases_and_deduplicates() -> None:
    assert normalize_geo(["au", "DE, au", " ro "]) == ["AU", "DE", "RO"]


def test_normalize_geo_rejects_invalid_codes() -> None:
    with pytest.raises(ValueError, match="ISO-2"):
        normalize_geo(["AUS"])


def test_create_request_requires_geo() -> None:
    with pytest.raises(ValidationError):
        CreateCampaignRequest(name="x", geo=[], offer_id=1)
