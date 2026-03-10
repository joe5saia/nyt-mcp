"""Tests for Pydantic request / response models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nyt_mcp.models import (
    ArchiveRequest,
    ArticleResult,
    ArticleSearchRequest,
    BestsellersRequest,
    MostPopularRequest,
    NewswireRequest,
    TopStoriesRequest,
    TopStoriesSection,
)


class TestArticleSearchRequest:
    def test_defaults(self):
        req = ArticleSearchRequest(query="climate")
        assert req.query == "climate"
        assert req.sort == "newest"
        assert req.page == 0
        assert req.filter_query is None

    def test_all_fields(self):
        req = ArticleSearchRequest(
            query="election",
            filter_query='section.name:"Politics"',
            begin_date="20240101",
            end_date="20241231",
            sort="oldest",
            page=5,
        )
        assert req.begin_date == "20240101"
        assert req.sort == "oldest"

    def test_page_out_of_range(self):
        with pytest.raises(ValidationError):
            ArticleSearchRequest(query="test", page=101)

    def test_invalid_date_format(self):
        with pytest.raises(ValidationError):
            ArticleSearchRequest(query="test", begin_date="2024-01-01")


class TestTopStoriesRequest:
    def test_default_section(self):
        req = TopStoriesRequest()
        assert req.section.value == "home"

    def test_explicit_section(self):
        req = TopStoriesRequest(section=TopStoriesSection.WORLD)
        assert req.section.value == "world"


class TestMostPopularRequest:
    def test_defaults(self):
        req = MostPopularRequest()
        assert req.popularity_type.value == "viewed"
        assert req.period == 1

    def test_invalid_period(self):
        with pytest.raises(ValidationError):
            MostPopularRequest(period=2)  # type: ignore[arg-type]


class TestNewswireRequest:
    def test_defaults(self):
        req = NewswireRequest()
        assert req.source.value == "all"
        assert req.section == "all"


class TestBestsellersRequest:
    def test_defaults(self):
        req = BestsellersRequest()
        assert req.list_name == "hardcover-fiction"
        assert req.date == "current"


class TestArchiveRequest:
    def test_valid(self):
        req = ArchiveRequest(year=2024, month=6)
        assert req.year == 2024
        assert req.month == 6

    def test_year_too_early(self):
        with pytest.raises(ValidationError):
            ArchiveRequest(year=1800, month=1)

    def test_month_out_of_range(self):
        with pytest.raises(ValidationError):
            ArchiveRequest(year=2024, month=13)


class TestArticleResult:
    def test_defaults(self):
        result = ArticleResult()
        assert result.web_url == ""
        assert result.word_count == 0

    def test_with_data(self):
        result = ArticleResult(
            web_url="https://nytimes.com/article",
            headline="Test",
            snippet="A snippet",
            word_count=500,
        )
        assert result.word_count == 500
