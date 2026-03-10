"""Pydantic models for NYT API requests and responses."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TopStoriesSection(StrEnum):
    """Sections available in the Top Stories API."""

    ARTS = "arts"
    AUTOMOBILES = "automobiles"
    BOOKS_REVIEW = "books/review"
    BUSINESS = "business"
    FASHION = "fashion"
    FOOD = "food"
    HEALTH = "health"
    HOME = "home"
    INSIDER = "insider"
    MAGAZINE = "magazine"
    MOVIES = "movies"
    NYREGION = "nyregion"
    OBITUARIES = "obituaries"
    OPINION = "opinion"
    POLITICS = "politics"
    REALESTATE = "realestate"
    SCIENCE = "science"
    SPORTS = "sports"
    SUNDAYREVIEW = "sundayreview"
    TECHNOLOGY = "technology"
    THEATER = "theater"
    T_MAGAZINE = "t-magazine"
    TRAVEL = "travel"
    UPSHOT = "upshot"
    US = "us"
    WORLD = "world"


class MostPopularType(StrEnum):
    """Types of most-popular rankings."""

    EMAILED = "emailed"
    SHARED = "shared"
    VIEWED = "viewed"


class NewswireSource(StrEnum):
    """Content sources for the Times Newswire API."""

    ALL = "all"
    NYT = "nyt"
    INYT = "inyt"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ArticleSearchRequest(BaseModel):
    """Parameters for the Article Search API."""

    query: str = Field(..., description="Search query string.")
    filter_query: str | None = Field(
        None,
        description=(
            "Lucene-syntax filter. "
            "E.g. 'section.name:\"Books\"' or 'source.vernacular:\"The New York Times\"'."
        ),
    )
    begin_date: str | None = Field(
        None,
        description="Start date in YYYYMMDD format.",
        pattern=r"^\d{8}$",
    )
    end_date: str | None = Field(
        None,
        description="End date in YYYYMMDD format.",
        pattern=r"^\d{8}$",
    )
    sort: Literal["newest", "oldest", "relevance"] = Field(
        "newest",
        description="Sort order for results.",
    )
    page: int = Field(
        0,
        ge=0,
        le=100,
        description="Page number (0-indexed, max 100). Each page has 10 results.",
    )


class TopStoriesRequest(BaseModel):
    """Parameters for the Top Stories API."""

    section: TopStoriesSection = Field(
        TopStoriesSection.HOME,
        description="NYT section to retrieve top stories from.",
    )


class MostPopularRequest(BaseModel):
    """Parameters for the Most Popular API."""

    popularity_type: MostPopularType = Field(
        MostPopularType.VIEWED,
        description="Type of popularity ranking.",
    )
    period: Literal[1, 7, 30] = Field(
        1,
        description="Time period in days (1, 7, or 30).",
    )


class NewswireRequest(BaseModel):
    """Parameters for the Times Newswire API."""

    source: NewswireSource = Field(
        NewswireSource.ALL,
        description="Content source filter.",
    )
    section: str = Field(
        "all",
        description="Section name, or 'all' for every section.",
    )


class BestsellersRequest(BaseModel):
    """Parameters for the Books / Best Sellers API."""

    list_name: str = Field(
        "hardcover-fiction",
        description="Best-seller list slug (e.g. 'hardcover-fiction').",
    )
    date: str = Field(
        "current",
        description="Published date (YYYY-MM-DD) or 'current' for the latest.",
    )


class ArchiveRequest(BaseModel):
    """Parameters for the Archive API."""

    year: int = Field(..., ge=1851, description="Year (>= 1851).")
    month: int = Field(..., ge=1, le=12, description="Month (1-12).")


# ---------------------------------------------------------------------------
# Response models (trimmed to the most useful fields)
# ---------------------------------------------------------------------------


class ArticleResult(BaseModel):
    """A single article returned by the Article Search API."""

    web_url: str = ""
    snippet: str = ""
    headline: str = ""
    byline: str = ""
    pub_date: str = ""
    section: str = ""
    word_count: int = 0


class TopStoryResult(BaseModel):
    """A single article from the Top Stories API."""

    title: str = ""
    abstract: str = ""
    url: str = ""
    byline: str = ""
    section: str = ""
    published_date: str = ""


class MostPopularResult(BaseModel):
    """A single article from the Most Popular API."""

    title: str = ""
    abstract: str = ""
    url: str = ""
    byline: str = ""
    section: str = ""
    published_date: str = ""


class NewswireResult(BaseModel):
    """A single article from the Times Newswire API."""

    title: str = ""
    abstract: str = ""
    url: str = ""
    byline: str = ""
    section: str = ""
    published_date: str = ""
    source: str = ""


class BestsellerResult(BaseModel):
    """A single book from a Best Sellers list."""

    title: str = ""
    author: str = ""
    description: str = ""
    rank: int = 0
    weeks_on_list: int = 0
    publisher: str = ""
    primary_isbn13: str = ""
    amazon_product_url: str = ""


ArchiveResult = ArticleResult
"""Archive articles share the same schema as Article Search results."""
