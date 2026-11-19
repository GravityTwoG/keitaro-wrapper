from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from keitaro_wrapper.core.config import Settings, get_settings
from keitaro_wrapper.core.database import Database
from keitaro_wrapper.core.errors_handlers import register_exception_handlers
from keitaro_wrapper.core.logging import configure_logging, get_logger
from keitaro_wrapper.core.middleware import RequestContextMiddleware
from keitaro_wrapper.features.campaigns.router import router as campaigns_router
from keitaro_wrapper.features.health.router import router as health_router
from keitaro_wrapper.integrations.keitaro.client import KeitaroClient

logger = get_logger(__name__)

API_PREFIX = "/api/v1"


def create_app(
    settings: Settings | None = None,
    *,
    keitaro_transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(app_settings)
        keitaro = KeitaroClient(
            app_settings.keitaro_base_url,
            app_settings.keitaro_api_key,
            app_settings.keitaro_timeout_seconds,
            transport=keitaro_transport,
        )
        app.state.settings = app_settings
        app.state.database = database
        app.state.keitaro = keitaro
        logger.info(
            "Started %s (env=%s, keitaro=%s)",
            app_settings.app_name,
            app_settings.environment,
            app_settings.keitaro_base_url,
        )
        try:
            yield
        finally:
            await keitaro.aclose()
            await database.dispose()

    app = FastAPI(
        title=app_settings.app_name,
        version="0.1.0",
        description=(
            "Обёртка над Keitaro Admin API: создание кампаний и редактор офферов. "
            "Keitaro остаётся источником истины, локальная БД хранит изменения редактора до публикации."
        ),
        lifespan=lifespan,
        debug=app_settings.debug,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(health_router)
    api.include_router(campaigns_router)

    app.include_router(api)

    return app


app = create_app()
