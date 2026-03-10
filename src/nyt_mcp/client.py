"""Async HTTP client for the New York Times APIs."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import httpx

from nyt_mcp.models import (
    ArchiveRequest,
    ArchiveResult,
    ArticleResult,
    ArticleSearchRequest,
    BestsellerResult,
    BestsellersRequest,
    MostPopularRequest,
    MostPopularResult,
    NewswireRequest,
    NewswireResult,
    TopStoriesRequest,
    TopStoryResult,
)

if TYPE_CHECKING:
    from nyt_mcp.config import Settings


class NYTClient:
    """Thin async wrapper around the NYT public APIs.

    Each method validates inputs via Pydantic, calls the API, and returns
    a list of typed result models.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the client with NYT API settings.

        Args:
            settings: Application settings containing the API key and base URL.
        """
        self._settings = settings
        self._http = httpx.AsyncClient(
            base_url=settings.api_base_url,
            timeout=settings.request_timeout,
            params={"api-key": settings.api_key},
        )

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._http.aclose()

    # ------------------------------------------------------------------
    # Article Search
    # ------------------------------------------------------------------

    async def search_articles(self, request: ArticleSearchRequest) -> list[ArticleResult]:
        """Search for articles by keyword and optional filters.

        Args:
            request: Validated search parameters.

        Returns:
            A list of matching articles (max 10 per page).
        """
        params: dict[str, Any] = {"q": request.query, "sort": request.sort, "page": request.page}
        if request.filter_query:
            params["fq"] = request.filter_query
        if request.begin_date:
            params["begin_date"] = request.begin_date
        if request.end_date:
            params["end_date"] = request.end_date

        resp = await self._http.get("/search/v2/articlesearch.json", params=params)
        resp.raise_for_status()
        docs: list[dict[str, Any]] = resp.json().get("response", {}).get("docs", [])
        return [_parse_article_doc(doc) for doc in docs]

    # ------------------------------------------------------------------
    # Top Stories
    # ------------------------------------------------------------------

    async def get_top_stories(self, request: TopStoriesRequest) -> list[TopStoryResult]:
        """Fetch the current top stories for a given section.

        Args:
            request: Validated top-stories parameters.

        Returns:
            A list of top-story articles.
        """
        resp = await self._http.get(f"/topstories/v2/{request.section.value}.json")
        resp.raise_for_status()
        results: list[dict[str, Any]] = resp.json().get("results", [])
        return [
            TopStoryResult(
                title=r.get("title", ""),
                abstract=r.get("abstract", ""),
                url=r.get("url", ""),
                byline=r.get("byline", ""),
                section=r.get("section", ""),
                published_date=r.get("published_date", ""),
            )
            for r in results
        ]

    # ------------------------------------------------------------------
    # Most Popular
    # ------------------------------------------------------------------

    async def get_most_popular(self, request: MostPopularRequest) -> list[MostPopularResult]:
        """Fetch the most popular articles (emailed / shared / viewed).

        Args:
            request: Validated most-popular parameters.

        Returns:
            A list of popular articles.
        """
        resp = await self._http.get(
            f"/mostpopular/v2/{request.popularity_type.value}/{request.period}.json"
        )
        resp.raise_for_status()
        results: list[dict[str, Any]] = resp.json().get("results", [])
        return [
            MostPopularResult(
                title=r.get("title", ""),
                abstract=r.get("abstract", ""),
                url=r.get("url", ""),
                byline=r.get("byline", ""),
                section=r.get("section", ""),
                published_date=r.get("published_date", ""),
            )
            for r in results
        ]

    # ------------------------------------------------------------------
    # Times Newswire
    # ------------------------------------------------------------------

    async def get_newswire(self, request: NewswireRequest) -> list[NewswireResult]:
        """Fetch the latest articles from the Times Newswire.

        Args:
            request: Validated newswire parameters.

        Returns:
            A list of recently published articles.
        """
        resp = await self._http.get(
            f"/news/v3/content/{request.source.value}/{request.section}.json"
        )
        resp.raise_for_status()
        results: list[dict[str, Any]] = resp.json().get("results", [])
        return [
            NewswireResult(
                title=r.get("title", ""),
                abstract=r.get("abstract", ""),
                url=r.get("url", ""),
                byline=r.get("byline", ""),
                section=r.get("section", ""),
                published_date=r.get("published_date", ""),
                source=r.get("source", ""),
            )
            for r in results
        ]

    # ------------------------------------------------------------------
    # Books / Best Sellers
    # ------------------------------------------------------------------

    async def get_bestsellers(self, request: BestsellersRequest) -> list[BestsellerResult]:
        """Fetch a Best Sellers list.

        Args:
            request: Validated bestsellers parameters.

        Returns:
            A list of books on the requested Best Sellers list.
        """
        resp = await self._http.get(f"/books/v3/lists/{request.date}/{request.list_name}.json")
        resp.raise_for_status()
        books: list[dict[str, Any]] = resp.json().get("results", {}).get("books", [])
        return [
            BestsellerResult(
                title=b.get("title", ""),
                author=b.get("author", ""),
                description=b.get("description", ""),
                rank=b.get("rank", 0),
                weeks_on_list=b.get("weeks_on_list", 0),
                publisher=b.get("publisher", ""),
                primary_isbn13=b.get("primary_isbn13", ""),
                amazon_product_url=b.get("amazon_product_url", ""),
            )
            for b in books
        ]

    # ------------------------------------------------------------------
    # Archive
    # ------------------------------------------------------------------

    async def get_archive(self, request: ArchiveRequest) -> list[ArchiveResult]:
        """Fetch article metadata for a given month from the Archive API.

        Args:
            request: Validated archive parameters.

        Returns:
            A list of article metadata entries for the month.

        Note:
            This endpoint can return thousands of results. The response is
            truncated to the first 50 articles to keep context manageable.
        """
        resp = await self._http.get(f"/archive/v1/{request.year}/{request.month}.json")
        resp.raise_for_status()
        docs: list[dict[str, Any]] = resp.json().get("response", {}).get("docs", [])
        # Truncate to avoid overwhelming context windows.
        return [_parse_article_doc(doc) for doc in docs[:50]]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_article_doc(doc: dict[str, Any]) -> ArticleResult:
    """Convert a raw Article Search / Archive doc dict into an ``ArticleResult``."""
    headline_obj = doc.get("headline", {})
    headline = headline_obj.get("main", "") if isinstance(headline_obj, dict) else str(headline_obj)

    byline_obj = doc.get("byline", {})
    byline = byline_obj.get("original", "") if isinstance(byline_obj, dict) else str(byline_obj)

    return ArticleResult(
        web_url=doc.get("web_url", ""),
        snippet=doc.get("snippet", doc.get("abstract", "")),
        headline=headline,
        byline=byline,
        pub_date=doc.get("pub_date", ""),
        section=doc.get("section_name", ""),
        word_count=doc.get("word_count", 0),
    )
