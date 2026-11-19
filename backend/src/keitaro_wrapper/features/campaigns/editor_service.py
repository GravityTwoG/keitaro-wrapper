from __future__ import annotations

import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from keitaro_wrapper.core.errors import ConflictError, NotFoundError, ValidationError
from keitaro_wrapper.features.campaigns.editor_models import (
    CampaignOffer,
    CampaignOfferStatus,
    CampaignStream,
)
from keitaro_wrapper.features.campaigns.editor_repository import CampaignEditorRepository
from keitaro_wrapper.features.campaigns.editor_schemas import (
    CampaignEditorView,
    CampaignOfferView,
    CampaignStreamView,
)
from keitaro_wrapper.integrations.keitaro.client import KeitaroClient
from keitaro_wrapper.integrations.keitaro.schemas import (
    Offer,
    Stream,
    StreamFilter,
    StreamOffer,
    StreamWrite,
)

_INCLUDED = {CampaignOfferStatus.ACTIVE, CampaignOfferStatus.PENDING}


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [value]
    return []


def _to_stream_write(stream: Stream, offers: list[StreamOffer]) -> StreamWrite:
    stream_type = stream.type if stream.type in {"regular", "forced", "default"} else "regular"
    schema = stream.schema_ if stream.schema_ in {"redirect", "landings", "action"} else "landings"
    return StreamWrite(
        campaign_id=stream.campaign_id,
        name=stream.name,
        type=stream_type,  # type: ignore[arg-type]
        position=stream.position,
        weight=stream.weight,
        state=stream.state,
        action_type=stream.action_type or "http",
        action_payload=stream.action_payload,
        action_options=stream.action_options,
        comments=stream.comments,
        schema_=schema,  # type: ignore[arg-type]
        collect_clicks=stream.collect_clicks,
        filter_or=stream.filter_or,
        filters=[
            StreamFilter(
                id=item.id,
                name=item.name,
                mode=item.mode,
                payload=_as_list(item.payload),
            )
            for item in stream.filters
        ],
        offers=offers,
        landings=stream.landings,
        triggers=stream.triggers,
    )


class CampaignEditorService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        client: KeitaroClient,
    ) -> None:
        self._session = session
        self._client = client
        self._repo = CampaignEditorRepository(session)

    async def get_editor(self, campaign_id: int) -> CampaignEditorView:
        streams = await self._repo.list_streams(campaign_id)
        return self._view(streams)

    async def fetch_streams(self, campaign_id: int) -> CampaignEditorView:
        if await self._repo.has_dirty(campaign_id):
            raise ConflictError(
                "Есть неопубликованные изменения. Опубликуйте их или отмените перед загрузкой потоков"
            )

        await self._client.get_campaign(campaign_id)
        keitaro_streams, offers = await asyncio.gather(
            self._client.list_streams(campaign_id),
            self._client.list_offers(),
        )
        offer_names = {offer.id: offer.name for offer in offers}
        local_streams = await self._repo.list_streams(campaign_id)
        by_stream_id = {stream.stream_id: stream for stream in local_streams}

        for keitaro_stream in keitaro_streams:
            local = by_stream_id.get(keitaro_stream.id)
            if local is None:
                local = CampaignStream(
                    campaign_id=campaign_id,
                    stream_id=keitaro_stream.id,
                )
                self._session.add(local)
                local_streams.append(local)

            local.name = keitaro_stream.name
            local.position = keitaro_stream.position or 0
            local.dirty = False

            keitaro_offer_ids = {item.offer_id for item in keitaro_stream.offers}
            local_by_offer = {offer.offer_id: offer for offer in local.offers}

            for index, keitaro_offer in enumerate(keitaro_stream.offers):
                offer = local_by_offer.get(keitaro_offer.offer_id)
                if offer is None:
                    offer = CampaignOffer(
                        offer_id=keitaro_offer.offer_id,
                        offer_name=offer_names.get(
                            keitaro_offer.offer_id,
                            f"Offer #{keitaro_offer.offer_id}",
                        ),
                    )
                    local.offers.append(offer)
                offer.offer_name = offer_names.get(
                    keitaro_offer.offer_id,
                    offer.offer_name,
                )
                offer.status = CampaignOfferStatus.ACTIVE
                offer.share = keitaro_offer.share
                offer.pinned_share = None
                offer.baseline_status = CampaignOfferStatus.ACTIVE
                offer.baseline_share = offer.share
                offer.baseline_pinned_share = None
                offer.order_index = index

            for offer in local.offers:
                if offer.offer_id not in keitaro_offer_ids:
                    offer.status = CampaignOfferStatus.ARCHIVED
                    offer.share = 0
                    offer.pinned_share = None
                    offer.baseline_status = CampaignOfferStatus.ARCHIVED
                    offer.baseline_share = 0
                    offer.baseline_pinned_share = None

            local.has_offers = bool(keitaro_stream.offers) or bool(local.offers)

        keitaro_stream_ids = {stream.id for stream in keitaro_streams}
        for local in list(local_streams):
            if local.stream_id not in keitaro_stream_ids:
                await self._session.delete(local)
                local_streams.remove(local)

        await self._repo.commit()
        return self._view(local_streams)

    async def add_offer(
        self,
        campaign_id: int,
        stream_id: int,
        offer_id: int,
    ) -> CampaignStreamView:
        stream = await self._require_stream(campaign_id, stream_id)
        if not stream.has_offers:
            raise ValidationError("В поток без офферов нельзя добавить оффер")
        offer = await self._get_offer(offer_id)
        if any(item.offer_id == offer_id for item in stream.offers):
            raise ConflictError("Оффер уже есть в потоке. Используйте «Вернуть» для архивного оффера")

        next_index = max((item.order_index for item in stream.offers), default=-1) + 1
        stream.offers.append(
            CampaignOffer(
                offer_id=offer.id,
                offer_name=offer.name,
                status=CampaignOfferStatus.PENDING,
                share=0,
                order_index=next_index,
            )
        )
        self._recalculate(stream)
        await self._repo.commit()
        return self._stream_view(stream)

    async def remove_offer(
        self,
        campaign_id: int,
        stream_id: int,
        offer_id: int,
    ) -> CampaignStreamView:
        stream = await self._require_stream(campaign_id, stream_id)
        offer = self._find_offer(stream, offer_id)
        if offer.status not in _INCLUDED:
            raise ConflictError("Оффер уже удалён из потока")

        if offer.baseline_status is None:
            stream.offers.remove(offer)
        elif offer.baseline_status == CampaignOfferStatus.ARCHIVED:
            offer.status = CampaignOfferStatus.ARCHIVED
            offer.share = 0
        else:
            offer.status = CampaignOfferStatus.REMOVED
            offer.share = 0

        self._recalculate(stream)
        await self._repo.commit()
        return self._stream_view(stream)

    async def restore_offer(
        self,
        campaign_id: int,
        stream_id: int,
        offer_id: int,
    ) -> CampaignStreamView:
        stream = await self._require_stream(campaign_id, stream_id)
        offer = self._find_offer(stream, offer_id)
        if offer.status not in {CampaignOfferStatus.REMOVED, CampaignOfferStatus.ARCHIVED}:
            raise ConflictError("Оффер уже активен")

        if offer.baseline_status == CampaignOfferStatus.ACTIVE:
            offer.status = CampaignOfferStatus.ACTIVE
        else:
            offer.status = CampaignOfferStatus.PENDING
        self._recalculate(stream)
        await self._repo.commit()
        return self._stream_view(stream)

    async def pin_offer(
        self,
        campaign_id: int,
        stream_id: int,
        offer_id: int,
        *,
        pinned: bool,
    ) -> CampaignStreamView:
        stream = await self._require_stream(campaign_id, stream_id)
        offer = self._find_offer(stream, offer_id)
        if offer.status not in _INCLUDED:
            raise ValidationError("Нельзя закрепить вес удалённого оффера")
        offer.pinned_share = offer.share if pinned else None
        await self._repo.commit()
        return self._stream_view(stream)

    async def publish(self, campaign_id: int) -> CampaignEditorView:
        streams = await self._repo.list_streams(campaign_id)
        dirty_streams = [stream for stream in streams if stream.dirty]
        for stream in dirty_streams:
            current = await self._client.get_stream(stream.stream_id)
            included = [
                item
                for item in sorted(stream.offers, key=lambda offer: offer.order_index)
                if item.status in _INCLUDED
            ]
            updated = await self._client.update_stream(
                stream.stream_id,
                _to_stream_write(
                    current,
                    [
                        StreamOffer(offer_id=item.offer_id, share=item.share, state="active")
                        for item in included
                    ],
                ),
            )
            returned = {item.offer_id: item for item in updated.offers}
            for offer in stream.offers:
                if offer.status in _INCLUDED:
                    if offer.offer_id in returned:
                        offer.share = returned[offer.offer_id].share
                    offer.status = CampaignOfferStatus.ACTIVE
                    offer.baseline_status = CampaignOfferStatus.ACTIVE
                    offer.baseline_share = offer.share
                    offer.baseline_pinned_share = offer.pinned_share
                elif offer.status == CampaignOfferStatus.REMOVED:
                    offer.status = CampaignOfferStatus.ARCHIVED
                    offer.share = 0
                    offer.baseline_status = CampaignOfferStatus.ARCHIVED
                    offer.baseline_share = 0
                    offer.baseline_pinned_share = offer.pinned_share
                else:
                    offer.baseline_status = CampaignOfferStatus.ARCHIVED
                    offer.baseline_share = 0
                    offer.baseline_pinned_share = offer.pinned_share
            stream.dirty = False
            await self._repo.commit()

        return self._view(streams)

    async def cancel(self, campaign_id: int) -> CampaignEditorView:
        streams = await self._repo.list_streams(campaign_id)
        for stream in streams:
            for offer in list(stream.offers):
                if offer.baseline_status is None:
                    stream.offers.remove(offer)
                else:
                    offer.status = offer.baseline_status
                    offer.share = offer.baseline_share or 0
                    offer.pinned_share = offer.baseline_pinned_share
            stream.dirty = False
        await self._repo.commit()
        return self._view(streams)

    async def _require_stream(self, campaign_id: int, stream_id: int) -> CampaignStream:
        stream = await self._repo.get_stream(campaign_id, stream_id)
        if stream is None:
            raise NotFoundError("Поток не загружен. Сначала нажмите «Загрузить потоки»")
        return stream

    @staticmethod
    def _find_offer(stream: CampaignStream, offer_id: int) -> CampaignOffer:
        for offer in stream.offers:
            if offer.offer_id == offer_id:
                return offer
        raise NotFoundError("Оффер не найден в потоке")

    async def _get_offer(self, offer_id: int) -> Offer:
        try:
            return await self._client.get_offer(offer_id)
        except NotFoundError as exc:
            raise NotFoundError(
                f"Оффер с ID {offer_id} не найден в Keitaro",
                details=exc.details,
            ) from exc

    @staticmethod
    def _recalculate(stream: CampaignStream) -> None:
        included = [item for item in stream.offers if item.status in _INCLUDED]
        for offer in stream.offers:
            if offer.status not in _INCLUDED:
                offer.share = 0

        pinned = [item for item in included if item.pinned_share is not None]
        pinned_total = sum(item.pinned_share or 0 for item in pinned)
        for offer in pinned:
            offer.share = offer.pinned_share or 0

        free = [item for item in included if item.pinned_share is None]
        remaining = max(0, 100 - pinned_total)
        if free:
            base, remainder = divmod(remaining, len(free))
            for index, offer in enumerate(free):
                offer.share = base + (1 if index < remainder else 0)

        stream.dirty = CampaignEditorService._compute_dirty(stream)

    @staticmethod
    def _compute_dirty(stream: CampaignStream) -> bool:
        for offer in stream.offers:
            if offer.status in {
                CampaignOfferStatus.PENDING,
                CampaignOfferStatus.REMOVED,
            }:
                return True
            if offer.baseline_status is None:
                return True
            if (
                offer.status == CampaignOfferStatus.ACTIVE
                and offer.baseline_status == CampaignOfferStatus.ACTIVE
                and offer.share != (offer.baseline_share or 0)
            ):
                return True
        return False

    def _view(self, streams: list[CampaignStream]) -> CampaignEditorView:
        stream_views = [self._stream_view(stream) for stream in streams]
        return CampaignEditorView(
            loaded=bool(streams),
            dirty=any(stream.dirty for stream in streams),
            streams=stream_views,
        )

    @staticmethod
    def _stream_view(stream: CampaignStream) -> CampaignStreamView:
        offers = (
            [
                CampaignOfferView(
                    offer_id=offer.offer_id,
                    name=offer.offer_name,
                    share=offer.share,
                    pinned_share=offer.pinned_share,
                    status=offer.status.value,
                    can_remove=offer.status in _INCLUDED,
                    can_restore=offer.status in {CampaignOfferStatus.REMOVED, CampaignOfferStatus.ARCHIVED},
                )
                for offer in sorted(stream.offers, key=lambda item: item.order_index)
            ]
            if stream.has_offers
            else []
        )
        return CampaignStreamView(
            stream_id=stream.stream_id,
            name=stream.name,
            position=stream.position,
            has_offers=stream.has_offers,
            dirty=stream.dirty,
            offers=offers,
        )
