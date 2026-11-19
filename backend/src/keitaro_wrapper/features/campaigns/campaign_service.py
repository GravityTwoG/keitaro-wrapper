from __future__ import annotations

import asyncio
import uuid

from slugify import slugify

from keitaro_wrapper.core.config import Settings
from keitaro_wrapper.core.errors import AppError, NotFoundError, ValidationError
from keitaro_wrapper.core.logging import get_logger
from keitaro_wrapper.features.campaigns.campaign_schemas import (
    CampaignListResponse,
    CampaignSummary,
    CreateCampaignRequest,
    OfferSearchItem,
    OfferSearchResponse,
)
from keitaro_wrapper.integrations.keitaro.client import KeitaroClient
from keitaro_wrapper.integrations.keitaro.schemas import (
    Campaign,
    CampaignWrite,
    Offer,
    Stream,
    StreamFilter,
    StreamOffer,
    StreamWrite,
)

logger = get_logger(__name__)


class CampaignService:
    def __init__(
        self,
        *,
        client: KeitaroClient,
        settings: Settings,
    ) -> None:
        self._client = client
        self._settings = settings

    # ------------------------------------------------------------------ listing

    async def list_campaigns(self, *, limit: int, offset: int) -> CampaignListResponse:
        # Request one extra row to know whether the next page exists without a
        # separate count request (Keitaro does not return a total).
        campaigns = await self._client.list_campaigns(limit=limit + 1, offset=offset)
        has_more = len(campaigns) > limit
        items = [
            CampaignSummary(
                id=campaign.id,
                name=campaign.name,
                alias=campaign.alias,
                state=campaign.state,
            )
            for campaign in campaigns[:limit]
        ]
        return CampaignListResponse(items=items, offset=offset, has_more=has_more)

    async def get_detail(self, campaign_id: int) -> CampaignSummary:
        campaign = await self._client.get_campaign(campaign_id)
        return CampaignSummary(
            id=campaign.id,
            name=campaign.name,
            alias=campaign.alias,
            state=campaign.state,
        )

    # ------------------------------------------------------------------ creation

    async def create_campaign(self, payload: CreateCampaignRequest) -> CampaignSummary:
        offer, (domain_id, group_id, source_id) = await asyncio.gather(
            self._get_offer(payload.offer_id),
            self._resolve_catalog(),
        )

        alias = self._build_alias(payload.name)

        campaign: Campaign | None = None
        google_stream: Stream | None = None
        offer_stream: Stream | None = None
        try:
            campaign = await self._client.create_campaign(
                CampaignWrite(
                    name=payload.name,
                    alias=alias,
                    type="position",
                    state="active",
                    group_id=group_id,
                    traffic_source_id=source_id,
                    domain_id=domain_id,
                    cost_type="CPC",
                    cost_value=0,
                )
            )
            google_stream = await self._client.create_stream(
                StreamWrite(
                    campaign_id=campaign.id,
                    name=f"{', '.join(payload.geo)} → Google",
                    type="regular",
                    position=1,
                    schema_="redirect",
                    action_type="http",
                    action_payload=self._settings.geo_redirect_url,
                    collect_clicks=True,
                    filters=[
                        StreamFilter(
                            name="country",
                            mode="accept",
                            payload=payload.geo,
                        )
                    ],
                )
            )
            offer_stream = await self._client.create_stream(
                StreamWrite(
                    campaign_id=campaign.id,
                    name="Оффер",
                    type="default",
                    position=2,
                    schema_="landings",
                    action_type="http",
                    action_payload=None,
                    collect_clicks=True,
                    offers=[StreamOffer(offer_id=offer.id, share=100, state="active")],
                )
            )
        except Exception:
            await self._rollback_creation(campaign, google_stream, offer_stream)
            raise

        return await self.get_detail(campaign.id)

    async def _rollback_creation(
        self,
        campaign: Campaign | None,
        google_stream: Stream | None,
        offer_stream: Stream | None,
    ) -> None:
        for stream in (offer_stream, google_stream):
            if stream is None:
                continue
            try:
                await self._client.delete_stream(stream.id)
            except AppError:
                logger.warning("Failed to archive stream %s during rollback", stream.id)
        if campaign is not None:
            try:
                await self._client.delete_campaign(campaign.id)
            except AppError:
                logger.warning("Failed to archive campaign %s during rollback", campaign.id)

    async def search_offers(
        self,
        search: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> OfferSearchResponse:
        offers = await self._client.list_offers()
        active = [offer for offer in offers if offer.state != "deleted"]
        query = search.strip().casefold()
        if query:
            active = [offer for offer in active if query in offer.name.casefold()]
        active.sort(key=lambda offer: offer.name.casefold())
        total = len(active)
        page = active[offset : offset + limit]
        items = [
            OfferSearchItem(
                id=offer.id,
                name=offer.name,
                payout_value=offer.payout_value,
                payout_currency=offer.payout_currency,
                country=offer.country or [],
            )
            for offer in page
        ]
        return OfferSearchResponse(
            items=items,
            total=total,
            offset=offset,
            has_more=offset + len(items) < total,
        )

    # ------------------------------------------------------------------ helpers

    async def _get_offer(self, offer_id: int) -> Offer:
        try:
            return await self._client.get_offer(offer_id)
        except NotFoundError as exc:
            raise NotFoundError(
                f"Оффер с ID {offer_id} не найден в Keitaro",
                details=exc.details,
            ) from exc

    async def _resolve_catalog(self) -> tuple[int, int, int]:
        domains, groups, sources = await asyncio.gather(
            self._client.list_domains(),
            self._client.list_groups("campaigns"),
            self._client.list_traffic_sources(),
        )
        active_domains = [domain for domain in domains if domain.state == "active"]
        active_sources = [source for source in sources if source.state == "active"]

        resolved_domain = self._settings.default_domain_id
        if resolved_domain is None and active_domains:
            resolved_domain = min(active_domains, key=lambda item: item.id).id
        if resolved_domain is None:
            raise ValidationError("В Keitaro нет активных доменов. Добавьте домен, чтобы создать кампанию")
        if not any(item.id == resolved_domain for item in active_domains):
            raise ValidationError(f"Домен с ID {resolved_domain} не найден или отключён")

        resolved_group = self._settings.default_campaign_group_id
        if resolved_group is None and groups:
            resolved_group = min(groups, key=lambda item: item.id).id
        if resolved_group is None:
            raise ValidationError("В Keitaro нет групп кампаний. Создайте группу, чтобы создать кампанию")
        if not any(item.id == resolved_group for item in groups):
            raise ValidationError(f"Группа с ID {resolved_group} не найдена")

        resolved_source = self._settings.default_traffic_source_id
        if resolved_source is None and active_sources:
            resolved_source = min(active_sources, key=lambda item: item.id).id
        if resolved_source is None:
            raise ValidationError(
                "В Keitaro нет активных источников трафика. Создайте источник, чтобы создать кампанию"
            )
        if not any(item.id == resolved_source for item in active_sources):
            raise ValidationError(f"Источник с ID {resolved_source} не найден или отключён")

        return resolved_domain, resolved_group, resolved_source

    @staticmethod
    def _build_alias(name: str) -> str:
        base = slugify(name, max_length=40) or "campaign"
        return f"{base}-{uuid.uuid4().hex[:6]}"
