from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PlaItem(BaseModel):
    """Shopping (PLA) item in search results"""

    pos: int | None = None
    url: str | None = None
    price: str | None = None
    title: str | None = None
    seller: str | None = None
    url_image: str | None = None
    image_data: str | None = None
    instalment_price: str | None = None


class Sitelink(BaseModel):
    """Inline sitelink in search results"""

    url: str | None = None
    title: str | None = None


class SiteLinks(BaseModel):
    """Sitelinks container"""

    inline: list[Sitelink] | None = None


class OrganicResult(BaseModel):
    """Organic search result"""

    pos: int | None = None
    url: str | None = None
    desc: str | None = None
    title: str | None = None
    price: float | None = None
    currency: str | None = None
    sitelinks: SiteLinks | None = None
    url_shown: str | None = None
    pos_overall: int | None = None
    favicon_text: str | None = None
    additional_info: list[str] | None = None


class TopStoryItem(BaseModel):
    """Top story item"""

    pos: int | None = None
    url: str | None = None
    title: str | None = None
    source: str | None = None
    timeframe: str | None = None


class TopStories(BaseModel):
    """Top stories section"""

    items: list[TopStoryItem] | None = None
    pos_overall: int | None = None


class RelatedSearches(BaseModel):
    """Related searches section"""

    pos_overall: int | None = None
    related_searches: list[str] | None = None


class RelatedQuestionSource(BaseModel):
    """Source for related question"""

    url: str | None = None
    title: str | None = None
    url_shown: str | None = None


class RelatedQuestion(BaseModel):
    """Related question item"""

    pos: int | None = None
    answer: str | None = None
    source: RelatedQuestionSource | None = None
    question: str | None = None


class RelatedQuestions(BaseModel):
    """Related questions section"""

    items: list[RelatedQuestion] | None = None
    pos_overall: int | None = None


class SearchInformation(BaseModel):
    """Search information"""

    query: str | None = None
    showing_results_for: str | None = None
    total_results_count: int | None = None


class SearchResults(BaseModel):
    """Complete search results"""

    pla: dict[str, list[PlaItem]] | None = None
    paid: list[Any] | None = None
    organic: list[OrganicResult] | None = None
    top_stories: TopStories | None = None
    related_searches: RelatedSearches | None = None
    related_questions: RelatedQuestions | None = None
    search_information: SearchInformation | None = None
    total_results_count: int | None = None


class GoogleSearchContent(BaseModel):
    """Content of search response"""

    url: str | None = None
    page: int | None = None
    results: SearchResults
    last_visible_page: int | None = None
    parse_status_code: int | None = None


class QueryResult(BaseModel):
    """Query result information"""

    content: GoogleSearchContent
    created_at: datetime | None = None
    updated_at: datetime | None = None
    page: int | None = None
    url: str | None = None
    job_id: str | None = None
    status_code: int | None = None


class OxyGoogleSearchResponse(BaseModel):
    """Complete Oxylabs Google search response"""

    results: list[QueryResult]
    job: dict[str, Any] | None = None
