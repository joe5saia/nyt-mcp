"""End-to-end tests that hit the real NYT API.

These tests require a valid API_KEY in the .env file and network access.
Run with:  uv run pytest tests/test_e2e.py -v
"""

from __future__ import annotations

import asyncio

import pytest
import pytest_asyncio

from nyt_mcp.client import NYTClient
from nyt_mcp.config import Settings
from nyt_mcp.models import (
    ArchiveRequest,
    ArticleSearchRequest,
    BestsellersRequest,
    MostPopularRequest,
    MostPopularType,
    NewswireRequest,
    NewswireSource,
    TopStoriesRequest,
    TopStoriesSection,
)


@pytest.fixture(scope="module")
def settings() -> Settings:
    """Load real settings from .env."""
    s = Settings()
    if not s.api_key:
        pytest.skip("No API_KEY configured - skipping e2e tests")
    return s


@pytest_asyncio.fixture
async def client(settings: Settings):
    """Provide a real NYTClient and close it after each test.

    Includes a small delay after each test to respect the NYT API rate limit
    (typically 5 requests per minute for free-tier keys).
    """
    c = NYTClient(settings)
    try:
        yield c
    finally:
        await c.close()
        await asyncio.sleep(6)


class TestSearchArticlesE2E:
    @pytest.mark.asyncio
    async def test_search_returns_results(self, client: NYTClient):
        results = await client.search_articles(
            ArticleSearchRequest(query="climate change", page=0)
        )
        assert len(results) > 0
        first = results[0]
        assert first.headline
        assert first.web_url.startswith("https://")

    @pytest.mark.asyncio
    async def test_search_with_filters(self, client: NYTClient):
        results = await client.search_articles(
            ArticleSearchRequest(
                query="election",
                sort="newest",
                begin_date="20240101",
                end_date="20241231",
                page=0,
            )
        )
        assert len(results) > 0


class TestTopStoriesE2E:
    @pytest.mark.asyncio
    async def test_home_section(self, client: NYTClient):
        results = await client.get_top_stories(
            TopStoriesRequest(section=TopStoriesSection.HOME)
        )
        assert len(results) > 0
        first = results[0]
        assert first.title
        assert first.url

    @pytest.mark.asyncio
    async def test_world_section(self, client: NYTClient):
        results = await client.get_top_stories(
            TopStoriesRequest(section=TopStoriesSection.WORLD)
        )
        assert len(results) > 0


class TestMostPopularE2E:
    @pytest.mark.asyncio
    async def test_viewed_1_day(self, client: NYTClient):
        results = await client.get_most_popular(
            MostPopularRequest(popularity_type=MostPopularType.VIEWED, period=1)
        )
        assert len(results) > 0
        first = results[0]
        assert first.title
        assert first.url

    @pytest.mark.asyncio
    async def test_emailed_7_days(self, client: NYTClient):
        results = await client.get_most_popular(
            MostPopularRequest(popularity_type=MostPopularType.EMAILED, period=7)
        )
        assert len(results) > 0


class TestNewswireE2E:
    @pytest.mark.asyncio
    async def test_all_sources(self, client: NYTClient):
        results = await client.get_newswire(
            NewswireRequest(source=NewswireSource.ALL, section="all")
        )
        assert len(results) > 0
        first = results[0]
        assert first.title
        assert first.url


class TestBestsellersE2E:
    @pytest.mark.asyncio
    async def test_hardcover_fiction(self, client: NYTClient):
        results = await client.get_bestsellers(
            BestsellersRequest(list_name="hardcover-fiction", date="current")
        )
        assert len(results) > 0
        first = results[0]
        assert first.title
        assert first.author
        assert first.rank >= 1


class TestArchiveE2E:
    @pytest.mark.asyncio
    async def test_recent_month(self, client: NYTClient):
        results = await client.get_archive(ArchiveRequest(year=2024, month=1))
        assert len(results) > 0
        assert len(results) <= 50  # client caps at 50
        first = results[0]
        assert first.headline
        assert first.web_url

