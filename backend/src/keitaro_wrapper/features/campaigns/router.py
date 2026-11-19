from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from keitaro_wrapper.core.dependencies import KeitaroDep, SessionDep, SettingsDep
from keitaro_wrapper.features.campaigns.campaign_schemas import (
    CampaignListResponse,
    CampaignSummary,
    CreateCampaignRequest,
    OfferSearchResponse,
)
from keitaro_wrapper.features.campaigns.campaign_service import CampaignService
from keitaro_wrapper.features.campaigns.editor_schemas import (
    AddCampaignOfferRequest,
    CampaignEditorView,
    CampaignStreamView,
    PinCampaignOfferRequest,
)
from keitaro_wrapper.features.campaigns.editor_service import CampaignEditorService

router = APIRouter(tags=["campaigns"])


def get_campaign_service(
    client: KeitaroDep,
    settings: SettingsDep,
) -> CampaignService:
    return CampaignService(client=client, settings=settings)


def get_campaign_editor_service(
    session: SessionDep,
    client: KeitaroDep,
) -> CampaignEditorService:
    return CampaignEditorService(session=session, client=client)


CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]
CampaignEditorServiceDep = Annotated[
    CampaignEditorService,
    Depends(get_campaign_editor_service),
]


@router.get("/campaigns", response_model=CampaignListResponse)
async def list_campaigns(
    service: CampaignServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CampaignListResponse:
    return await service.list_campaigns(limit=limit, offset=offset)


@router.post("/campaigns", response_model=CampaignSummary, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CreateCampaignRequest,
    service: CampaignServiceDep,
) -> CampaignSummary:
    return await service.create_campaign(payload)


@router.get("/campaigns/{campaign_id}", response_model=CampaignSummary)
async def get_campaign(campaign_id: int, service: CampaignServiceDep) -> CampaignSummary:
    return await service.get_detail(campaign_id)


@router.get("/offers", response_model=OfferSearchResponse)
async def search_offers(
    service: CampaignServiceDep,
    search: Annotated[str, Query(max_length=160)] = "",
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OfferSearchResponse:
    return await service.search_offers(search, limit, offset)


@router.get("/campaigns/{campaign_id}/editor", response_model=CampaignEditorView)
async def get_editor(
    campaign_id: int,
    service: CampaignEditorServiceDep,
) -> CampaignEditorView:
    return await service.get_editor(campaign_id)


@router.post("/campaigns/{campaign_id}/editor/fetch", response_model=CampaignEditorView)
async def fetch_streams(
    campaign_id: int,
    service: CampaignEditorServiceDep,
) -> CampaignEditorView:
    return await service.fetch_streams(campaign_id)


@router.post(
    "/campaigns/{campaign_id}/editor/streams/{stream_id}/offers",
    response_model=CampaignStreamView,
    status_code=status.HTTP_201_CREATED,
)
async def add_offer(
    campaign_id: int,
    stream_id: int,
    payload: AddCampaignOfferRequest,
    service: CampaignEditorServiceDep,
) -> CampaignStreamView:
    return await service.add_offer(campaign_id, stream_id, payload.offer_id)


@router.delete(
    "/campaigns/{campaign_id}/editor/streams/{stream_id}/offers/{offer_id}",
    response_model=CampaignStreamView,
)
async def remove_offer(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    service: CampaignEditorServiceDep,
) -> CampaignStreamView:
    return await service.remove_offer(campaign_id, stream_id, offer_id)


@router.post(
    "/campaigns/{campaign_id}/editor/streams/{stream_id}/offers/{offer_id}/restore",
    response_model=CampaignStreamView,
)
async def restore_offer(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    service: CampaignEditorServiceDep,
) -> CampaignStreamView:
    return await service.restore_offer(campaign_id, stream_id, offer_id)


@router.post(
    "/campaigns/{campaign_id}/editor/streams/{stream_id}/offers/{offer_id}/pin",
    response_model=CampaignStreamView,
)
async def pin_offer(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    payload: PinCampaignOfferRequest,
    service: CampaignEditorServiceDep,
) -> CampaignStreamView:
    return await service.pin_offer(campaign_id, stream_id, offer_id, pinned=payload.pinned)


@router.post("/campaigns/{campaign_id}/editor/publish", response_model=CampaignEditorView)
async def publish(
    campaign_id: int,
    service: CampaignEditorServiceDep,
) -> CampaignEditorView:
    return await service.publish(campaign_id)


@router.post("/campaigns/{campaign_id}/editor/cancel", response_model=CampaignEditorView)
async def cancel(
    campaign_id: int,
    service: CampaignEditorServiceDep,
) -> CampaignEditorView:
    return await service.cancel(campaign_id)
