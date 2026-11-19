from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from keitaro_wrapper.features.campaigns.editor_models import CampaignStream


class CampaignEditorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_streams(self, campaign_id: int) -> list[CampaignStream]:
        result = await self._session.execute(
            select(CampaignStream)
            .where(CampaignStream.campaign_id == campaign_id)
            .options(selectinload(CampaignStream.offers))
            .order_by(CampaignStream.position, CampaignStream.stream_id)
        )
        return list(result.scalars().unique())

    async def get_stream(
        self,
        campaign_id: int,
        stream_id: int,
    ) -> CampaignStream | None:
        result = await self._session.execute(
            select(CampaignStream)
            .where(
                CampaignStream.campaign_id == campaign_id,
                CampaignStream.stream_id == stream_id,
            )
            .options(selectinload(CampaignStream.offers))
        )
        return result.scalar_one_or_none()

    async def has_dirty(self, campaign_id: int) -> bool:
        result = await self._session.execute(
            select(CampaignStream.id)
            .where(
                CampaignStream.campaign_id == campaign_id,
                CampaignStream.dirty.is_(True),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def commit(self) -> None:
        await self._session.commit()
