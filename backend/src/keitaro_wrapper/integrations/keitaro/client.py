from __future__ import annotations

import time
from typing import Any, NoReturn, TypeVar

import httpx

from keitaro_wrapper.core.errors import (
    KeitaroApiError,
    KeitaroUnavailableError,
    NotFoundError,
)
from keitaro_wrapper.integrations.keitaro.schemas import (
    Campaign,
    CampaignWrite,
    Domain,
    Group,
    Offer,
    Stream,
    StreamWrite,
    TrafficSource,
)

_ModelT = TypeVar("_ModelT")

_OFFERS_TTL_SECONDS = 30.0


class KeitaroClient:
    """Thin async adapter around the Keitaro Admin API.

    The client translates transport failures into application errors and validates
    every response with Pydantic models, so the rest of the code never touches raw
    JSON.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 15.0,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Api-Key": api_key, "Accept": "application/json"},
            timeout=httpx.Timeout(timeout),
            transport=transport,
        )
        self._offers_cache: tuple[float, list[Offer]] | None = None

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = await self._client.request(method, path, json=json, params=params)
        except httpx.TimeoutException as exc:
            raise KeitaroUnavailableError("Keitaro не ответил вовремя") from exc
        except httpx.HTTPError as exc:
            raise KeitaroUnavailableError(
                "Не удалось подключиться к Keitaro",
                details={"reason": str(exc)},
            ) from exc

        if response.is_success:
            if not response.content:
                return None
            try:
                return response.json()
            except ValueError as exc:
                raise KeitaroApiError("Keitaro вернул некорректный JSON") from exc

        self._raise_for_status(response)
        raise AssertionError("unreachable")

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> NoReturn:
        try:
            body: Any = response.json()
        except ValueError:
            body = response.text

        message = "Keitaro отклонил запрос"
        if isinstance(body, dict):
            raw_error = body.get("error") or body.get("message")
            if isinstance(raw_error, dict):
                message = str(raw_error.get("message") or raw_error.get("title") or message)
            elif raw_error:
                message = str(raw_error)
        elif body:
            message = str(body)[:500]

        if response.status_code == 404:
            raise NotFoundError("Объект не найден в Keitaro", details={"upstream": message})
        if response.status_code in (401, 403):
            raise KeitaroApiError(
                "Не удалось авторизоваться в Keitaro. Проверьте KEITARO_API_KEY",
                status_code=502,
                details={"upstream_status": response.status_code},
            )
        raise KeitaroApiError(
            f"{message} (HTTP {response.status_code})",
            details={"upstream_status": response.status_code},
        )

    @staticmethod
    def _as_list(data: Any, key: str) -> list[Any]:
        if isinstance(data, dict):
            value = data.get(key) or data.get("data") or []
            return value if isinstance(value, list) else []
        return data if isinstance(data, list) else []

    @staticmethod
    def _as_model(data: Any, model: type[_ModelT]) -> _ModelT:
        if isinstance(data, list):
            data = data[0] if data else None
        if data is None:
            raise KeitaroApiError("Keitaro вернул пустой ответ")
        return model.model_validate(data)

    async def list_campaigns(self, *, limit: int = 100, offset: int = 0) -> list[Campaign]:
        data = await self._request(
            "GET",
            "/campaigns",
            params={"limit": limit, "offset": offset},
        )
        return [Campaign.model_validate(item) for item in self._as_list(data, "campaigns")]

    async def get_campaign(self, campaign_id: int) -> Campaign:
        data = await self._request("GET", f"/campaigns/{campaign_id}")
        return self._as_model(data, Campaign)

    async def create_campaign(self, payload: CampaignWrite) -> Campaign:
        data = await self._request(
            "POST",
            "/campaigns",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return self._as_model(data, Campaign)

    async def delete_campaign(self, campaign_id: int) -> None:
        await self._request("DELETE", f"/campaigns/{campaign_id}")

    async def list_streams(self, campaign_id: int) -> list[Stream]:
        data = await self._request("GET", f"/campaigns/{campaign_id}/streams")
        return [Stream.model_validate(item) for item in self._as_list(data, "streams")]

    async def get_stream(self, stream_id: int) -> Stream:
        data = await self._request("GET", f"/streams/{stream_id}")
        return self._as_model(data, Stream)

    async def create_stream(self, payload: StreamWrite) -> Stream:
        data = await self._request(
            "POST",
            "/streams",
            json=payload.model_dump(mode="json", exclude_none=True, by_alias=True),
        )
        return self._as_model(data, Stream)

    async def update_stream(self, stream_id: int, payload: StreamWrite) -> Stream:
        data = await self._request(
            "PUT",
            f"/streams/{stream_id}",
            json=payload.model_dump(mode="json", exclude_none=True, by_alias=True),
        )
        return self._as_model(data, Stream)

    async def delete_stream(self, stream_id: int) -> None:
        await self._request("DELETE", f"/streams/{stream_id}")

    async def list_offers(self) -> list[Offer]:
        now = time.monotonic()
        if self._offers_cache is not None:
            cached_at, offers = self._offers_cache
            if now - cached_at < _OFFERS_TTL_SECONDS:
                return offers

        data = await self._request("GET", "/offers")
        offers = [Offer.model_validate(item) for item in self._as_list(data, "offers")]
        self._offers_cache = (now, offers)
        return offers

    async def get_offer(self, offer_id: int) -> Offer:
        data = await self._request("GET", f"/offers/{offer_id}")
        return self._as_model(data, Offer)

    async def list_domains(self) -> list[Domain]:
        data = await self._request("GET", "/domains")
        return [Domain.model_validate(item) for item in self._as_list(data, "domains")]

    async def list_groups(self, group_type: str = "campaigns") -> list[Group]:
        data = await self._request("GET", "/groups", params={"type": group_type})
        return [Group.model_validate(item) for item in self._as_list(data, "groups")]

    async def list_traffic_sources(self) -> list[TrafficSource]:
        data = await self._request("GET", "/traffic_sources")
        return [TrafficSource.model_validate(item) for item in self._as_list(data, "sources")]

    async def ping(self) -> None:
        await self._request("GET", "/campaigns", params={"limit": 1})
