"""Tests for the NYTClient using httpx mocking."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from nyt_mcp.client import NYTClient, _parse_article_doc
from nyt_mcp.config import Settings
from nyt_mcp.models import (
    ArticleSearchRequest,
    BestsellersRequest,
    MostPopularRequest,
    NewswireRequest,
    TopStoriesRequest,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(api_key="test-key-123")


@pytest.fixture
def client(settings: Settings) -> NYTClient:
    return NYTClient(settings)


def _mock_response(data: dict[str, Any], status_code: int = 200) -> httpx.Response:
    """Create a mock httpx.Response."""
    return httpx.Response(
        status_code=status_code,
        json=data,
        request=httpx.Request("GET", "https://example.com"),
    )


class TestParseArticleDoc:
    def test_full_doc(self):
        doc = {
            "web_url": "https://nytimes.com/test",
            "snippet": "A test snippet",
            "headline": {"main": "Test Headline"},
            "byline": {"original": "By Author"},
            "pub_date": "2024-01-01T00:00:00Z",
            "section_name": "World",
            "word_count": 1000,
        }
        result = _parse_article_doc(doc)
        assert result.headline == "Test Headline"
        assert result.byline == "By Author"
        assert result.word_count == 1000

    def test_missing_fields(self):
        result = _parse_article_doc({})
        assert result.web_url == ""
        assert result.headline == ""

    def test_string_headline(self):
        result = _parse_article_doc({"headline": "Plain string"})
        assert result.headline == "Plain string"


class TestSearchArticles:
    @pytest.mark.asyncio
    async def test_search_returns_results(self, client: NYTClient):
        mock_data = {
            "response": {
                "docs": [
                    {
                        "web_url": "https://nytimes.com/1",
                        "headline": {"main": "Article 1"},
                        "byline": {"original": "By Test"},
                        "snippet": "Snippet 1",
                        "pub_date": "2024-06-01",
                        "section_name": "World",
                        "word_count": 500,
                    }
                ]
            }
        }
        with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(mock_data)
            results = await client.search_articles(ArticleSearchRequest(query="test"))
        assert len(results) == 1
        assert results[0].headline == "Article 1"

    @pytest.mark.asyncio
    async def test_search_empty_results(self, client: NYTClient):
        with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response({"response": {"docs": []}})
            results = await client.search_articles(ArticleSearchRequest(query="zzz"))
        assert results == []


class TestTopStories:
    @pytest.mark.asyncio
    async def test_returns_stories(self, client: NYTClient):
        mock_data = {
            "results": [
                {
                    "title": "Top Story",
                    "abstract": "Abstract",
                    "url": "https://nytimes.com/top",
                    "byline": "By Reporter",
                    "section": "World",
                    "published_date": "2024-06-01",
                }
            ]
        }
        with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(mock_data)
            results = await client.get_top_stories(TopStoriesRequest())
        assert len(results) == 1
        assert results[0].title == "Top Story"


class TestMostPopular:
    @pytest.mark.asyncio
    async def test_returns_popular(self, client: NYTClient):
        mock_data = {
            "results": [
                {
                    "title": "Popular Article",
                    "abstract": "Abstract",
                    "url": "https://nytimes.com/popular",
                    "byline": "By Author",
                    "section": "Opinion",
                    "published_date": "2024-06-01",
                }
            ]
        }
        with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(mock_data)
            results = await client.get_most_popular(MostPopularRequest())
        assert len(results) == 1
        assert results[0].title == "Popular Article"


class TestNewswire:
    @pytest.mark.asyncio
    async def test_returns_newswire(self, client: NYTClient):
        mock_data = {
            "results": [
                {
                    "title": "Breaking News",
                    "abstract": "Just in",
                    "url": "https://nytimes.com/wire",
                    "byline": "By Wire",
                    "section": "U.S.",
                    "published_date": "2024-06-01",
                    "source": "New York Times",
                }
            ]
        }
        with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(mock_data)
            results = await client.get_newswire(NewswireRequest())
        assert len(results) == 1
        assert results[0].source == "New York Times"


class TestBestsellers:
    @pytest.mark.asyncio
    async def test_returns_books(self, client: NYTClient):
        mock_data = {
            "results": {
                "books": [
                    {
                        "title": "A Great Book",
                        "author": "Author Name",
                        "description": "A description",
                        "rank": 1,
                        "weeks_on_list": 5,
                        "publisher": "Publisher",
                        "primary_isbn13": "9781234567890",
                        "amazon_product_url": "https://amazon.com/book",
                    }
                ]
            }
        }
        with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = _mock_response(mock_data)
            results = await client.get_bestsellers(BestsellersRequest())
        assert len(results) == 1
        assert results[0].rank == 1
        assert results[0].author == "Author Name"


class TestFetchArticleText:
    @pytest.mark.asyncio
    async def test_extracts_text(self, client: NYTClient):
        html = """
        <html>
        <body>
            <article>
                <p>First paragraph of article.</p>
                <p>Second paragraph of article.</p>
            </article>
        </body>
        </html>
        """
        resp = httpx.Response(
            status_code=200,
            text=html,
            request=httpx.Request("GET", "https://nytimes.com/article"),
        )
        with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = resp
            text = await client.fetch_article_text("https://nytimes.com/article")
        assert "First paragraph" in text
        assert "Second paragraph" in text
