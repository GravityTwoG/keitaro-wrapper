from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from keitaro_wrapper.core.config import Settings
from keitaro_wrapper.core.database import Database
from keitaro_wrapper.integrations.keitaro.client import KeitaroClient


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def get_database(request: Request) -> Database:
    database: Database = request.app.state.database
    return database


def get_keitaro(request: Request) -> KeitaroClient:
    client: KeitaroClient = request.app.state.keitaro
    return client


async def get_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    async with database.session() as session:
        yield session


SettingsDep = Annotated[Settings, Depends(get_settings)]
KeitaroDep = Annotated[KeitaroClient, Depends(get_keitaro)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]
