"""NYT MCP server - exposes New York Times APIs as MCP tools."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP

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


@contextlib.asynccontextmanager
async def _lifespan(_server: FastMCP) -> AsyncIterator[dict[str, NYTClient]]:
    """Manage the ``NYTClient`` lifecycle.

    The client is created on startup and torn down on shutdown, making
    the underlying ``httpx.AsyncClient`` available to every tool via
    ``ctx.request_context.lifespan_context``.
    """
    settings = Settings()
    client = NYTClient(settings)
    try:
        yield {"nyt_client": client}
    finally:
        await client.close()


mcp = FastMCP(
    name="nyt-mcp",
    instructions=(
        "This server provides access to the New York Times APIs. "
        "You can search articles, get top stories, view most popular articles, "
        "read the Times Newswire, check best-seller lists, browse the archive, "
        "and read the full text of any NYT article."
    ),
    lifespan=_lifespan,
)


def _get_client(ctx: object) -> NYTClient:
    """Extract the ``NYTClient`` from the MCP request context.

    Args:
        ctx: The MCP ``Context`` object injected by FastMCP.

    Returns:
        The shared ``NYTClient`` instance.
    """
    return ctx.request_context.lifespan_context["nyt_client"]  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_articles(
    ctx: object,
    query: str,
    filter_query: str | None = None,
    begin_date: str | None = None,
    end_date: str | None = None,
    sort: str = "newest",
    page: int = 0,
) -> str:
    """Search NYT articles by keyword and optional filters.

    Args:
        ctx: MCP context (injected automatically).
        query: Search query string.
        filter_query: Lucene-syntax filter (e.g. 'section.name:"Books"').
        begin_date: Start date in YYYYMMDD format.
        end_date: End date in YYYYMMDD format.
        sort: Sort order - 'newest', 'oldest', or 'relevance'.
        page: Page number (0-indexed, max 100).

    Returns:
        Formatted search results.
    """
    client = _get_client(ctx)
    request = ArticleSearchRequest(
        query=query,
        filter_query=filter_query,
        begin_date=begin_date,
        end_date=end_date,
        sort=sort,  # type: ignore[arg-type]
        page=page,
    )
    results = await client.search_articles(request)
    if not results:
        return "No articles found."
    lines: list[str] = []
    for article in results:
        lines.append(
            f"**{article.headline}**\n"
            f"  {article.snippet}\n"
            f"  By: {article.byline} | {article.pub_date} | {article.section}\n"
            f"  URL: {article.web_url}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_top_stories(
    ctx: object,
    section: str = "home",
) -> str:
    """Get the current top stories for a given NYT section.

    Args:
        ctx: MCP context (injected automatically).
        section: Section name (e.g. 'home', 'world', 'science', 'politics').

    Returns:
        Formatted list of top stories.
    """
    client = _get_client(ctx)
    request = TopStoriesRequest(section=TopStoriesSection(section))
    results = await client.get_top_stories(request)
    if not results:
        return "No top stories found."
    lines: list[str] = []
    for story in results:
        lines.append(
            f"**{story.title}**\n"
            f"  {story.abstract}\n"
            f"  {story.byline} | {story.published_date}\n"
            f"  URL: {story.url}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_most_popular(
    ctx: object,
    popularity_type: str = "viewed",
    period: int = 1,
) -> str:
    """Get the most popular NYT articles (emailed, shared, or viewed).

    Args:
        ctx: MCP context (injected automatically).
        popularity_type: One of 'emailed', 'shared', or 'viewed'.
        period: Time period in days - 1, 7, or 30.

    Returns:
        Formatted list of popular articles.
    """
    client = _get_client(ctx)
    request = MostPopularRequest(
        popularity_type=MostPopularType(popularity_type),
        period=period,  # type: ignore[arg-type]
    )
    results = await client.get_most_popular(request)
    if not results:
        return "No popular articles found."
    lines: list[str] = []
    for article in results:
        lines.append(
            f"**{article.title}**\n"
            f"  {article.abstract}\n"
            f"  {article.byline} | {article.published_date}\n"
            f"  URL: {article.url}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_newswire(
    ctx: object,
    source: str = "all",
    section: str = "all",
) -> str:
    """Get the latest articles from the Times Newswire (live stream).

    Args:
        ctx: MCP context (injected automatically).
        source: Content source - 'all', 'nyt', or 'inyt'.
        section: Section name, or 'all' for everything.

    Returns:
        Formatted list of recent articles.
    """
    client = _get_client(ctx)
    request = NewswireRequest(source=NewswireSource(source), section=section)
    results = await client.get_newswire(request)
    if not results:
        return "No newswire articles found."
    lines: list[str] = []
    for article in results:
        lines.append(
            f"**{article.title}**\n"
            f"  {article.abstract}\n"
            f"  {article.byline} | {article.published_date} | Source: {article.source}\n"
            f"  URL: {article.url}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_bestsellers(
    ctx: object,
    list_name: str = "hardcover-fiction",
    date: str = "current",
) -> str:
    """Get the NYT Best Sellers list.

    Args:
        ctx: MCP context (injected automatically).
        list_name: List slug (e.g. 'hardcover-fiction', 'paperback-nonfiction').
        date: Published date (YYYY-MM-DD) or 'current' for the latest.

    Returns:
        Formatted best-seller list.
    """
    client = _get_client(ctx)
    request = BestsellersRequest(list_name=list_name, date=date)
    results = await client.get_bestsellers(request)
    if not results:
        return "No best sellers found."
    lines: list[str] = []
    for book in results:
        lines.append(
            f"#{book.rank} **{book.title}** by {book.author}\n"
            f"  {book.description}\n"
            f"  Publisher: {book.publisher} | Weeks on list: {book.weeks_on_list}\n"
            f"  ISBN: {book.primary_isbn13}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_archive(
    ctx: object,
    year: int,
    month: int,
) -> str:
    """Get article metadata from the NYT Archive for a given month.

    Results are capped at 50 articles to keep context manageable.

    Args:
        ctx: MCP context (injected automatically).
        year: Year (>= 1851).
        month: Month (1-12).

    Returns:
        Formatted list of archived articles.
    """
    client = _get_client(ctx)
    request = ArchiveRequest(year=year, month=month)
    results = await client.get_archive(request)
    if not results:
        return "No archive articles found."
    lines: list[str] = []
    for article in results:
        lines.append(
            f"**{article.headline}**\n"
            f"  {article.snippet}\n"
            f"  {article.byline} | {article.pub_date}\n"
            f"  URL: {article.web_url}\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def read_article(
    ctx: object,
    url: str,
) -> str:
    """Read the full text of an NYT article given its URL.

    Args:
        ctx: MCP context (injected automatically).
        url: Full URL of the NYT article (e.g. https://www.nytimes.com/...).

    Returns:
        The extracted article text, or an error message.
    """
    client = _get_client(ctx)
    text = await client.fetch_article_text(url)
    if not text:
        return "Could not extract article text. The article may require a subscription."
    return text


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the NYT MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
