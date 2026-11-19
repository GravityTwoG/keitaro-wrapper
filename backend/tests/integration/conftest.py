from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
from asgi_lifespan import LifespanManager
from sqlalchemy import text
from testcontainers.community.postgres import PostgresContainer

from keitaro_wrapper.core.config import Settings
from keitaro_wrapper.core.database import Database
from keitaro_wrapper.main import create_app
from mock_keitaro.main import app as mock_keitaro_app
from mock_keitaro.main import reset_store

BACKEND_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    container = PostgresContainer("postgres:17-alpine", driver="asyncpg")
    container.start()
    url = container.get_connection_url()
    env = {**os.environ, "DATABASE_URL": url}
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        container.stop()
        raise RuntimeError(f"Alembic failed:\n{result.stdout}\n{result.stderr}")
    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def settings(postgres_container: PostgresContainer) -> Settings:
    return Settings(
        environment="test",
        database_url=postgres_container.get_connection_url(),
        keitaro_base_url="http://keitaro-mock/admin_api/v1",
        keitaro_api_key="dev-api-key",
        default_domain_id=None,
        default_campaign_group_id=None,
        default_traffic_source_id=None,
        log_level="WARNING",
    )


@pytest.fixture
async def app(settings: Settings):
    reset_store()
    transport = httpx.ASGITransport(app=mock_keitaro_app)
    application = create_app(settings, keitaro_transport=transport)
    async with LifespanManager(application):
        yield application


@pytest.fixture
async def client(app) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://api.test") as http_client:
        yield http_client


@pytest.fixture(autouse=True)
async def clean_database(settings: Settings) -> None:
    database = Database(settings)
    async with database.session() as session:
        await session.execute(text("TRUNCATE TABLE campaign_offers, campaign_streams"))
    await database.dispose()
