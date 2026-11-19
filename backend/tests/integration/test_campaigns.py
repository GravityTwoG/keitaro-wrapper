from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.integration


async def test_create_campaign_builds_geo_and_offer_streams(client: httpx.AsyncClient) -> None:
    from mock_keitaro.main import STORE

    response = await client.post(
        "/api/v1/campaigns",
        json={"name": "Австралия — тест", "geo": ["au"], "offer_id": 101},
    )

    assert response.status_code == 201, response.text
    detail = response.json()
    assert detail["name"] == "Австралия — тест"
    stored = STORE.campaigns[detail["id"]]
    assert stored["domain_id"] == 1
    assert stored["group_id"] == 1
    assert stored["traffic_source_id"] == 1

    streams = sorted(
        (
            stream
            for stream in STORE.streams.values()
            if stream["campaign_id"] == detail["id"] and stream["state"] != "deleted"
        ),
        key=lambda stream: stream["position"],
    )
    assert len(streams) == 2
    geo_stream, offer_stream = streams
    assert geo_stream["schema"] == "redirect"
    assert geo_stream["action_payload"] == "https://google.com"
    assert geo_stream["filters"][0]["name"] == "country"
    assert geo_stream["filters"][0]["mode"] == "accept"
    assert geo_stream["filters"][0]["payload"] == ["AU"]
    assert geo_stream["offers"] == []

    assert offer_stream["schema"] == "landings"
    assert offer_stream["type"] == "default"
    assert offer_stream["action_payload"] is None
    assert [offer["offer_id"] for offer in offer_stream["offers"]] == [101]
    assert STORE.offers[101]["name"] == "E2E Offer Alpha"


async def test_create_campaign_with_unknown_offer_returns_404(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/campaigns",
        json={"name": "No offer", "geo": ["AU"], "offer_id": 999999},
    )

    assert response.status_code == 404
    assert "999999" in response.json()["message"]


async def test_create_campaign_validates_geo(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/campaigns",
        json={"name": "Bad geo", "geo": ["australia"], "offer_id": 101},
    )

    assert response.status_code == 422


async def test_offer_search(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/offers", params={"search": "delta"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == 104


async def test_offer_search_supports_pages(client: httpx.AsyncClient) -> None:
    first_page = (await client.get("/api/v1/offers", params={"search": "e2e", "limit": 2})).json()
    assert first_page["total"] == 4
    assert first_page["has_more"] is True
    assert [item["id"] for item in first_page["items"]] == [101, 102]

    second_page = (
        await client.get("/api/v1/offers", params={"search": "e2e", "limit": 2, "offset": 2})
    ).json()
    assert second_page["has_more"] is False
    assert [item["id"] for item in second_page["items"]] == [104, 103]


async def test_campaign_list_is_paginated(client: httpx.AsyncClient) -> None:
    from mock_keitaro.main import STORE

    for index in range(150):
        campaign_id = 1000 + index
        STORE.campaigns[campaign_id] = {
            "id": campaign_id,
            "name": f"Campaign {index}",
            "alias": f"campaign-{index}",
            "state": "active",
            "cost_currency": "USD",
            "group_id": 1,
            "traffic_source_id": 1,
            "domain_id": 1,
            "type": "position",
            "cost_type": "CPC",
        }

    first = (await client.get("/api/v1/campaigns", params={"limit": 100, "offset": 0})).json()
    assert first["offset"] == 0
    assert first["has_more"] is True
    assert len(first["items"]) == 100
    assert {2, 3, 1000} <= {campaign["id"] for campaign in first["items"]}

    second = (await client.get("/api/v1/campaigns", params={"limit": 100, "offset": 100})).json()
    assert second["has_more"] is False
    assert len(second["items"]) == 52
    assert 1149 in {campaign["id"] for campaign in second["items"]}

    default_page = (await client.get("/api/v1/campaigns")).json()
    assert len(default_page["items"]) == 20
    assert default_page["has_more"] is True


async def test_editor_fetch_and_publish_flow(client: httpx.AsyncClient) -> None:
    from mock_keitaro.main import STORE

    editor = (await client.get("/api/v1/campaigns/2/editor")).json()
    assert editor["loaded"] is False

    fetched = (await client.post("/api/v1/campaigns/2/editor/fetch")).json()
    assert fetched["loaded"] is True
    assert fetched["dirty"] is False
    streams = {stream["stream_id"]: stream for stream in fetched["streams"]}
    assert streams[101]["has_offers"] is False
    assert streams[101]["offers"] == []
    offers = {offer["offer_id"]: offer for offer in streams[102]["offers"]}
    assert offers[3749]["share"] == 60
    assert offers[3717]["share"] == 40
    assert {offer["status"] for offer in offers.values()} == {"active"}

    added = (
        await client.post(
            "/api/v1/campaigns/2/editor/streams/102/offers",
            json={"offer_id": 104},
        )
    ).json()
    assert added["dirty"] is True
    assert len(added["offers"]) == 3
    assert sum(offer["share"] for offer in added["offers"]) == 100
    assert next(offer for offer in added["offers"] if offer["offer_id"] == 104)["status"] == "pending"
    assert len(STORE.streams[102]["offers"]) == 2

    blocked = await client.post("/api/v1/campaigns/2/editor/fetch")
    assert blocked.status_code == 409

    canceled = (await client.post("/api/v1/campaigns/2/editor/cancel")).json()
    assert canceled["dirty"] is False
    offers_after_cancel = {
        offer["offer_id"]: offer
        for stream in canceled["streams"]
        if stream["stream_id"] == 102
        for offer in stream["offers"]
    }
    assert set(offers_after_cancel) == {3749, 3717}
    assert offers_after_cancel[3749]["share"] == 60
    assert offers_after_cancel[3717]["share"] == 40

    await client.post(
        "/api/v1/campaigns/2/editor/streams/102/offers",
        json={"offer_id": 104},
    )
    published = (await client.post("/api/v1/campaigns/2/editor/publish")).json()
    assert published["dirty"] is False
    offers_after_publish = {
        offer["offer_id"]: offer
        for stream in published["streams"]
        if stream["stream_id"] == 102
        for offer in stream["offers"]
    }
    assert set(offers_after_publish) == {3749, 3717, 104}
    assert {offer["status"] for offer in offers_after_publish.values()} == {"active"}
    assert len(STORE.streams[102]["offers"]) == 3


async def test_removed_offer_is_archived_and_can_be_brought_back(
    client: httpx.AsyncClient,
) -> None:
    from mock_keitaro.main import STORE

    await client.post("/api/v1/campaigns/2/editor/fetch")

    removed = (await client.delete("/api/v1/campaigns/2/editor/streams/102/offers/3717")).json()
    removed_offer = next(offer for offer in removed["offers"] if offer["offer_id"] == 3717)
    assert removed_offer["status"] == "removed"
    assert removed_offer["share"] == 0
    assert removed["dirty"] is True
    assert len(STORE.streams[102]["offers"]) == 2

    published = (await client.post("/api/v1/campaigns/2/editor/publish")).json()
    archived = next(
        offer
        for stream in published["streams"]
        if stream["stream_id"] == 102
        for offer in stream["offers"]
        if offer["offer_id"] == 3717
    )
    assert archived["status"] == "archived"
    assert [offer["offer_id"] for offer in STORE.streams[102]["offers"]] == [3749]

    restored = (await client.post("/api/v1/campaigns/2/editor/streams/102/offers/3717/restore")).json()
    restored_offer = next(offer for offer in restored["offers"] if offer["offer_id"] == 3717)
    assert restored_offer["status"] == "pending"
    assert restored["dirty"] is True

    republished = (await client.post("/api/v1/campaigns/2/editor/publish")).json()
    assert republished["dirty"] is False
    assert {offer["offer_id"] for offer in STORE.streams[102]["offers"]} == {3749, 3717}


async def test_fetch_marks_externally_deleted_offers_as_archived(
    client: httpx.AsyncClient,
) -> None:
    from mock_keitaro.main import STORE

    await client.post("/api/v1/campaigns/2/editor/fetch")
    STORE.streams[102]["offers"] = [
        offer for offer in STORE.streams[102]["offers"] if offer["offer_id"] != 3717
    ]

    fetched = (await client.post("/api/v1/campaigns/2/editor/fetch")).json()
    offers = {
        offer["offer_id"]: offer
        for stream in fetched["streams"]
        if stream["stream_id"] == 102
        for offer in stream["offers"]
    }
    assert offers[3749]["status"] == "active"
    assert offers[3717]["status"] == "archived"
    assert offers[3717]["share"] == 0
    assert fetched["dirty"] is False


async def test_fetch_removes_externally_deleted_streams(client: httpx.AsyncClient) -> None:
    from mock_keitaro.main import STORE

    await client.post("/api/v1/campaigns/2/editor/fetch")
    del STORE.streams[101]

    fetched = (await client.post("/api/v1/campaigns/2/editor/fetch")).json()
    assert [stream["stream_id"] for stream in fetched["streams"]] == [102]


async def test_pinned_weight_survives_recalculations(client: httpx.AsyncClient) -> None:
    await client.post("/api/v1/campaigns/2/editor/fetch")
    pinned = (
        await client.post(
            "/api/v1/campaigns/2/editor/streams/102/offers/3749/pin",
            json={"pinned": True},
        )
    ).json()
    assert next(offer for offer in pinned["offers"] if offer["offer_id"] == 3749)["pinned_share"] == 60

    added = (
        await client.post(
            "/api/v1/campaigns/2/editor/streams/102/offers",
            json={"offer_id": 104},
        )
    ).json()
    shares = {offer["offer_id"]: offer["share"] for offer in added["offers"]}
    assert shares[3749] == 60
    assert sum(shares.values()) == 100
    assert shares[3717] + shares[104] == 40


async def test_offer_cannot_be_added_to_stream_without_offers(
    client: httpx.AsyncClient,
) -> None:
    await client.post("/api/v1/campaigns/2/editor/fetch")
    response = await client.post(
        "/api/v1/campaigns/2/editor/streams/101/offers",
        json={"offer_id": 104},
    )
    assert response.status_code == 422
