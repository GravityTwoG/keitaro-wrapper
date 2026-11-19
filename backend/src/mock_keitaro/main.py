from __future__ import annotations

import copy
import os
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse

API_PREFIX = "/admin_api/v1"
API_KEY = os.getenv("MOCK_KEITARO_API_KEY", "dev-api-key")


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class Store:
    campaigns: dict[int, dict[str, Any]] = field(default_factory=dict)
    streams: dict[int, dict[str, Any]] = field(default_factory=dict)
    offers: dict[int, dict[str, Any]] = field(default_factory=dict)
    domains: dict[int, dict[str, Any]] = field(default_factory=dict)
    groups: dict[int, dict[str, Any]] = field(default_factory=dict)
    sources: dict[int, dict[str, Any]] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)

    def next_id(self, entity: str, start: int = 1) -> int:
        value = self.counters.get(entity, start)
        self.counters[entity] = value + 1
        return value


def _seed() -> Store:
    store = Store()
    store.counters = {
        "campaigns": 10,
        "streams": 1000,
        "offers": 1000,
        "filters": 1,
    }
    store.domains[1] = {
        "id": 1,
        "name": "https://in.posdk.xyz/",
        "state": "active",
        "group_id": None,
        "group": "No group",
        "is_ssl": True,
        "created_at": "2026-01-10 10:00:00",
        "updated_at": "2026-01-10 10:00:00",
    }
    store.groups[1] = {"id": 1, "name": "FORESTS", "position": 1, "type": "campaigns"}
    store.groups[2] = {"id": 2, "name": "FORESTS", "position": 1, "type": "offers"}
    store.sources[1] = {
        "id": 1,
        "name": "FORESTS",
        "state": "active",
        "postback_url": "",
        "template_name": "custom",
        "created_at": "2026-01-10 10:00:00",
        "updated_at": "2026-01-10 10:00:00",
    }

    offers = [
        (
            3749,
            "MiAflow [BEAUTY-RO-BE_0009] [pl - - spin ro -] 2. Основной, Румыния JS",
        ),
        (3717, "MiAflow [BEAUTY-RO-BE_0008] [pl - - prize ro -] 1. Основной, Румыния JS"),
        (101, "E2E Offer Alpha"),
        (102, "E2E Offer Beta"),
        (103, "E2E Offer Gamma"),
        (104, "E2E Offer Delta"),
    ]
    for offer_id, name in offers:
        store.offers[offer_id] = {
            "id": offer_id,
            "name": name,
            "group_id": 2,
            "state": "active",
            "action_type": "http",
            "action_payload": f"https://offers.example/{offer_id}",
            "payout_value": 12.5,
            "payout_currency": "USD",
            "payout_type": "CPA",
            "affiliate_network_id": 1,
            "affiliate_network": "Example Network",
            "country": ["RO"],
            "notes": "",
            "created_at": "2026-01-10 10:00:00",
            "updated_at": "2026-01-10 10:00:00",
        }

    store.campaigns[2] = {
        "id": 2,
        "alias": "austral-test",
        "name": "Austral Test",
        "type": "position",
        "position": 1,
        "cookies_ttl": 24,
        "state": "active",
        "cost_type": "CPC",
        "cost_value": "0.0000",
        "cost_currency": "USD",
        "group_id": 1,
        "traffic_source_id": 1,
        "domain_id": 1,
        "bind_visitors": "s",
        "token": secrets.token_hex(8),
        "created_at": "2026-02-01 09:00:00",
        "updated_at": "2026-02-01 09:00:00",
    }
    store.streams[101] = {
        "id": 101,
        "campaign_id": 2,
        "name": "AU → Google",
        "type": "regular",
        "position": 1,
        "weight": 100,
        "chance": 50,
        "state": "active",
        "action_type": "http",
        "action_payload": "https://google.com",
        "action_options": None,
        "comments": "",
        "schema": "redirect",
        "collect_clicks": True,
        "filter_or": False,
        "filters": [
            {
                "id": 1,
                "stream_id": 101,
                "name": "country",
                "mode": "accept",
                "payload": ["AU"],
            }
        ],
        "offers": [],
        "landings": [],
        "updated_at": "2026-02-01 09:00:00",
    }
    store.streams[102] = {
        "id": 102,
        "campaign_id": 2,
        "name": "Оффер",
        "type": "default",
        "position": 2,
        "weight": 100,
        "chance": 50,
        "state": "active",
        "action_type": "http",
        "action_payload": "https://offers.example/3749",
        "action_options": None,
        "comments": "",
        "schema": "landings",
        "collect_clicks": True,
        "filter_or": False,
        "filters": [],
        "offers": [
            {
                "id": 1,
                "stream_id": 102,
                "offer_id": 3749,
                "share": 60,
                "state": "active",
            },
            {
                "id": 2,
                "stream_id": 102,
                "offer_id": 3717,
                "share": 40,
                "state": "active",
            },
        ],
        "landings": [],
        "updated_at": "2026-02-01 09:00:00",
    }

    store.campaigns[3] = {
        "id": 3,
        "alias": "empty-campaign",
        "name": "Пустая кампания",
        "type": "position",
        "position": 2,
        "cookies_ttl": 24,
        "state": "disabled",
        "cost_type": "CPC",
        "cost_value": "0.0000",
        "cost_currency": "USD",
        "group_id": 1,
        "traffic_source_id": 1,
        "domain_id": 1,
        "bind_visitors": None,
        "token": secrets.token_hex(8),
        "created_at": "2026-02-02 09:00:00",
        "updated_at": "2026-02-02 09:00:00",
    }

    return store


STORE = _seed()


def reset_store() -> None:
    global STORE
    STORE = _seed()


def verify_api_key(api_key: str | None = Header(default=None, alias="Api-Key")) -> None:
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail={"error": {"message": "Invalid API key"}},
        )


router = APIRouter(prefix=API_PREFIX, dependencies=[Depends(verify_api_key)])


def _error(status_code: int, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": {"message": message}})


def _find_campaign(campaign_id: int) -> dict[str, Any]:
    campaign = STORE.campaigns.get(campaign_id)
    if campaign is None or campaign["state"] == "deleted":
        raise _error(404, f"Campaign #{campaign_id} not found")
    return campaign


def _find_stream(stream_id: int) -> dict[str, Any]:
    stream = STORE.streams.get(stream_id)
    if stream is None or stream["state"] == "deleted":
        raise _error(404, f"Stream #{stream_id} not found")
    return stream


def _stream_payload(stream: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    updated = copy.deepcopy(stream)
    for key in (
        "name",
        "type",
        "position",
        "weight",
        "state",
        "action_type",
        "action_payload",
        "action_options",
        "comments",
        "schema",
        "collect_clicks",
        "filter_or",
    ):
        if key in body:
            updated[key] = body[key]

    if "filters" in body:
        filters: list[dict[str, Any]] = []
        for item in body.get("filters") or []:
            filters.append(
                {
                    "id": item.get("id") or STORE.next_id("filters"),
                    "stream_id": stream["id"],
                    "name": item["name"],
                    "mode": item.get("mode", "accept"),
                    "payload": item.get("payload") or [],
                }
            )
        updated["filters"] = filters

    if "offers" in body:
        offers: list[dict[str, Any]] = []
        existing = {item["offer_id"]: item for item in stream.get("offers", [])}
        for item in body.get("offers") or []:
            offer_id = int(item["offer_id"])
            if offer_id not in STORE.offers:
                raise _error(400, f"Offer #{offer_id} not found")
            previous = existing.get(offer_id)
            offers.append(
                {
                    "id": previous["id"] if previous else STORE.next_id("offer_links", 5000),
                    "stream_id": stream["id"],
                    "offer_id": offer_id,
                    "share": int(item.get("share", 100)),
                    "state": item.get("state", "active"),
                    "created_at": previous.get("created_at", _now()) if previous else _now(),
                    "updated_at": _now(),
                }
            )
        updated["offers"] = offers

    if "triggers" in body:
        triggers: list[dict[str, Any]] = []
        for item in body.get("triggers") or []:
            trigger = dict(item)
            trigger["id"] = trigger.get("id") or STORE.next_id("triggers", 9000)
            trigger["stream_id"] = stream["id"]
            triggers.append(trigger)
        updated["triggers"] = triggers

    updated["updated_at"] = _now()
    return updated


@router.get("/campaigns")
def list_campaigns(limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
    campaigns = [item for item in STORE.campaigns.values() if item["state"] != "deleted"]
    campaigns.sort(key=lambda item: item["id"])
    return campaigns[offset : offset + limit]


@router.post("/campaigns")
def create_campaign(body: dict[str, Any]) -> dict[str, Any]:
    name = str(body.get("name") or "").strip()
    if not name:
        raise _error(400, "Campaign name is required")
    alias = str(body.get("alias") or "").strip()
    if not alias:
        raise _error(400, "Campaign alias is required")
    if any(item["alias"] == alias for item in STORE.campaigns.values()):
        raise _error(400, "Campaign alias must be unique")

    campaign_id = STORE.next_id("campaigns")
    campaign = {
        "id": campaign_id,
        "alias": alias,
        "name": name,
        "type": body.get("type", "position"),
        "position": 9999,
        "cookies_ttl": body.get("cookies_ttl", 24),
        "state": body.get("state", "active"),
        "cost_type": body.get("cost_type", "CPC"),
        "cost_value": str(body.get("cost_value", 0)),
        "cost_currency": body.get("cost_currency", "USD"),
        "group_id": body.get("group_id"),
        "traffic_source_id": body.get("traffic_source_id"),
        "domain_id": body.get("domain_id"),
        "bind_visitors": body.get("bind_visitors"),
        "token": secrets.token_hex(16),
        "created_at": _now(),
        "updated_at": _now(),
    }
    STORE.campaigns[campaign_id] = campaign
    return campaign


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int) -> dict[str, Any]:
    return _find_campaign(campaign_id)


@router.delete("/campaigns/{campaign_id}")
def delete_campaign(campaign_id: int) -> dict[str, Any]:
    campaign = _find_campaign(campaign_id)
    campaign["state"] = "deleted"
    campaign["updated_at"] = _now()
    return campaign


@router.get("/campaigns/{campaign_id}/streams")
def list_streams(campaign_id: int) -> list[dict[str, Any]]:
    _find_campaign(campaign_id)
    streams = [
        item
        for item in STORE.streams.values()
        if item["campaign_id"] == campaign_id and item["state"] != "deleted"
    ]
    streams.sort(key=lambda item: (item.get("position") or 0, item["id"]))
    return streams


@router.post("/streams")
def create_stream(body: dict[str, Any]) -> dict[str, Any]:
    campaign_id = int(body.get("campaign_id") or 0)
    _find_campaign(campaign_id)
    for required in ("name", "type", "schema", "action_type"):
        if not body.get(required):
            raise _error(400, f"Field '{required}' is required")
    stream_id = STORE.next_id("streams", 1000)
    stream: dict[str, Any] = {
        "id": stream_id,
        "campaign_id": campaign_id,
        "name": body["name"],
        "type": body["type"],
        "position": body.get("position", 9999),
        "weight": body.get("weight", 100),
        "chance": 50,
        "state": body.get("state", "active"),
        "action_type": body["action_type"],
        "action_payload": body.get("action_payload"),
        "action_options": body.get("action_options"),
        "comments": body.get("comments", ""),
        "schema": body["schema"],
        "collect_clicks": body.get("collect_clicks", False),
        "filter_or": body.get("filter_or", False),
        "filters": [],
        "offers": [],
        "landings": [],
        "triggers": [],
        "updated_at": _now(),
    }
    STORE.streams[stream_id] = stream
    updated = _stream_payload(stream, body)
    STORE.streams[stream_id] = updated
    return updated


@router.get("/streams/{stream_id}")
def get_stream(stream_id: int) -> dict[str, Any]:
    return _find_stream(stream_id)


@router.put("/streams/{stream_id}")
def update_stream(stream_id: int, body: dict[str, Any]) -> dict[str, Any]:
    stream = _find_stream(stream_id)
    updated = _stream_payload(stream, body)
    STORE.streams[stream_id] = updated
    return updated


@router.delete("/streams/{stream_id}")
def delete_stream(stream_id: int) -> dict[str, Any]:
    stream = _find_stream(stream_id)
    stream["state"] = "deleted"
    stream["updated_at"] = _now()
    return stream


@router.get("/offers")
def list_offers() -> list[dict[str, Any]]:
    return [item for item in STORE.offers.values() if item["state"] != "deleted"]


@router.get("/offers/{offer_id}")
def get_offer(offer_id: int) -> dict[str, Any]:
    offer = STORE.offers.get(offer_id)
    if offer is None or offer["state"] == "deleted":
        raise _error(404, f"Offer #{offer_id} not found")
    return offer


@router.get("/domains")
def list_domains() -> list[dict[str, Any]]:
    return list(STORE.domains.values())


@router.get("/groups")
def list_groups(type: str = Query(default="campaigns")) -> list[dict[str, Any]]:
    return [item for item in STORE.groups.values() if item.get("type") == type]


@router.get("/traffic_sources")
def list_traffic_sources() -> list[dict[str, Any]]:
    return list(STORE.sources.values())


app = FastAPI(
    title="Keitaro Admin API (mock)",
    version="1.0.0",
    description="Deterministic in-memory imitation of the Keitaro Admin API for demo and e2e.",
)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, dict) else {"error": {"message": str(exc.detail)}}
    return JSONResponse(status_code=exc.status_code, content=detail)
