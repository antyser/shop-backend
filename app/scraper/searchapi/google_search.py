import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field, model_validator

from app.config import get_settings
from app.scraper.crawler.html_fetcher import fetch_batch


class SearchMetadata(BaseModel):
    """Metadata about the search request"""

    id: str | None = None
    status: str | None = None
    created_at: str | None = None
    request_time_taken: float | None = None
    parsing_time_taken: float | None = None
    total_time_taken: float | None = None
    request_url: str | None = None
    html_url: str | None = None
    json_url: str | None = None


class SearchParameters(BaseModel):
    """Parameters used for the search"""

    engine: str | None = None
    q: str | None = None
    device: str | None = None
    location: str | None = None
    location_used: str | None = None
    google_domain: str | None = None
    hl: str | None = None
    gl: str | None = None


class SearchInformation(BaseModel):
    """Information about the search results"""

    query_displayed: str | None = None
    total_results: int | None = None
    time_taken_displayed: float | None = None
    detected_location: str | None = None


class RelatedSearch(BaseModel):
    """Related search query"""

    query: str | None = None
    link: str | None = None


class Pagination(BaseModel):
    """Pagination information"""

    current: int | None = None
    next: str | None = None
    other_pages: dict[str, str] | None = None


class Cite(BaseModel):
    """Citation information"""

    domain: str | None = None
    span: str | None = None


class SiteLink(BaseModel):
    """Site link information"""

    title: str | None = None
    link: str | None = None
    snippet: str | None = None


class SiteLinks(BaseModel):
    """Site links container"""

    expanded: list[SiteLink] | None = None
    inline: list[SiteLink] | None = None
    list_items: list[SiteLink] | None = Field(None, alias="list")


class KnowledgeGraphLink(BaseModel):
    """Knowledge graph link information"""

    text: str | None = None
    link: str | None = None


class Manufacturer(BaseModel):
    """Manufacturer information"""

    title: str | None = None
    link: str | None = None
    name: str | None = None
    type: str | None = None


class TypicalPrices(BaseModel):
    """Typical price range"""

    currency: str | None = None
    min: float | None = None
    max: float | None = None


class InstallmentPlan(BaseModel):
    """Installment payment plan"""

    down_payment: str | None = None
    months: int | None = None
    cost_per_month: str | None = None


class Merchant(BaseModel):
    """Merchant information"""

    name: str | None = None
    domain: str | None = None
    country_code: str | None = None
    rating: float | None = None
    reviews: int | None = None
    link: str | None = None
    favicon: str | None = None


class Offer(BaseModel):
    """Product offer"""

    product_id: str | None = None
    name: str | None = None
    link: str | None = None
    return_days: int | None = None
    initial_price: str | None = None
    installment: InstallmentPlan | None = None
    delivery_price: str | None = None
    total_price: str | None = None
    merchant: Merchant | None = None


class Feature(BaseModel):
    """Product feature"""

    name: str | None = None
    value: str | None = None


class SpecAttribute(BaseModel):
    """Product specification attribute"""

    name: str | None = None
    value: str | None = None


class Specification(BaseModel):
    """Product specification category"""

    category: str | None = None
    attributes: list[SpecAttribute] | None = None


class ProductDetails(BaseModel):
    """Detailed product information"""

    description: str | None = None
    specifications: list[Specification] | None = None


class WebReview(BaseModel):
    """Web review information"""

    title: str | None = None
    link: str | None = None
    rating_text: str | None = None
    rating: float | None = None
    rating_out_of: int | None = None


class ReviewUser(BaseModel):
    """Review user information"""

    name: str | None = None
    image: str | None = None


class TopReview(BaseModel):
    """Top product review"""

    review: str | None = None
    date: str | None = None
    rating: float | None = None
    source: str | None = None
    user: ReviewUser | None = None


class ProductReviews(BaseModel):
    """Product reviews information"""

    rating: float | None = None
    reviews: int | None = None
    reviews_histogram: dict[str, str] | None = None
    top_review: TopReview | None = None
    popular_questions: list[str] | None = None


class EditorialReview(BaseModel):
    """Editorial review"""

    title: str | None = None
    rating_text: str | None = None
    rating: float | None = None
    rating_out_of: int | None = None
    review: str | None = None
    link: str | None = None


class KnowledgeGraph(BaseModel):
    """Knowledge graph information"""

    kgmid: str | None = None
    knowledge_graph_type: str | None = None
    title: str | None = None
    type: str | None = None
    rating: float | None = None
    reviews: int | None = None
    description: str | None = None
    manufacturer: Manufacturer | None = None
    typical_prices: TypicalPrices | None = None
    offers: list[Offer] | None = None
    features: list[Feature] | None = None
    details: ProductDetails | None = None
    web_reviews: list[WebReview] | None = None
    product_reviews: ProductReviews | None = None
    editorial_reviews: list[EditorialReview] | None = None
    images: list[str] | None = None
    source: dict | None = None
    initial_release_date: str | None = None
    programming_language: str | None = None
    programming_language_links: list[KnowledgeGraphLink] | None = None
    developers: str | None = None
    developers_links: list[KnowledgeGraphLink] | None = None
    engine: str | None = None
    engine_links: list[KnowledgeGraphLink] | None = None
    license: str | None = None
    platform: str | None = None
    platform_links: list[KnowledgeGraphLink] | None = None
    stable_release: str | None = None
    image: str | None = None


class KeyMoment(BaseModel):
    """Video key moment information"""

    time: str | None = None
    seconds: int | None = None
    title: str | None = None
    link: str | None = None
    thumbnail: str | None = None


class OrganicResult(BaseModel):
    """Individual organic search result"""

    position: int | None = None
    title: str | None = None
    link: str | None = None
    source: str | None = None
    domain: str | None = None
    displayed_link: str | None = None
    snippet: str | None = None
    snippet_highlighted_words: list[str] | None = None
    date: str | None = None
    sitelinks: SiteLinks | None = None
    favicon: str | None = None
    content: str | None = None


class AnswerBox(BaseModel):
    """Featured snippet or answer box"""

    type: str | None = None
    title: str | None = None
    answer: str | None = None
    link: str | None = None
    displayed_link: str | None = None
    snippet: str | None = None
    about_this_result: dict | None = None
    about_page_link: str | None = None
    source: str | None = None
    source_info_link: str | None = None
    thumbnail: str | None = None
    table: list[list[str]] | None = None
    list_items: list[str] | None = Field(None, alias="list")


class DiscussionForum(BaseModel):
    """Discussion or forum result"""

    title: str | None = None
    link: str | None = None
    source: str | None = None
    date: str | None = None
    posts: str | None = None
    community: str | None = None
    favicon: str | None = None
    content: str | None = None


class InlineVideo(BaseModel):
    """Inline video result"""

    position: int | None = None
    title: str | None = None
    link: str | None = None
    source: str | None = None
    channel: str | None = None
    date: str | None = None
    length: str | None = None
    image: str | None = None
    key_moments: list[KeyMoment] | None = None
    content: str | None = None


class TweetAuthor(BaseModel):
    """Tweet author information"""

    name: str | None = None
    screen_name: str | None = None
    link: str | None = None
    thumbnail: str | None = None


class Tweet(BaseModel):
    """Individual tweet"""

    tweet_id: str | None = None
    link: str | None = None
    snippet: str | None = None
    date: str | None = None
    author: TweetAuthor | None = None


class InlineTweets(BaseModel):
    """Inline tweets section"""

    title: str | None = None
    link: str | None = None
    displayed_link: str | None = None
    tweets: list[Tweet] | None = None


class ImageSource(BaseModel):
    """Image source information"""

    name: str | None = None
    link: str | None = None


class OriginalImage(BaseModel):
    """Original image details"""

    link: str | None = None
    height: int | None = None
    width: int | None = None
    size: str | None = None


class ImageSuggestion(BaseModel):
    """Image search suggestion"""

    title: str | None = None
    link: str | None = None
    chips: str | None = None
    thumbnail: str | None = None


class Image(BaseModel):
    """Individual image result"""

    title: str | None = None
    source: ImageSource | None = None
    original: OriginalImage | None = None
    thumbnail: str | None = None


class InlineImages(BaseModel):
    """Inline images section"""

    suggestions: list[ImageSuggestion] | None = None
    images: list[Image] | None = None


class Recipe(BaseModel):
    """Recipe information"""

    title: str | None = None
    link: str | None = None
    rating: float | None = None
    reviews: int | None = None
    ingredients: list[str] | None = None
    source: str | None = None
    duration: str | None = None
    thumbnail: str | None = None


class TopStory(BaseModel):
    """Top story article"""

    title: str | None = None
    link: str | None = None
    source: str | None = None
    date: str | None = None
    thumbnail: str | None = None


class Perspective(BaseModel):
    """Social media perspective"""

    link: str | None = None
    author: str | None = None
    source: str | None = None
    date: str | None = None
    snippet: str | None = None
    reactions: str | None = None
    thumbnail: str | None = None
    title: str | None = None
    content: str | None = None


class Course(BaseModel):
    """Online course"""

    title: str | None = None
    link: str | None = None
    source: str | None = None
    rating: float | None = None
    reviews: int | None = None
    extensions: list[str] | None = None
    thumbnail: str | None = None


class AboutResult(BaseModel):
    """About this result information"""

    source: dict | None = None
    keywords: list[str] | None = None
    languages: list[str] | None = None
    regions: list[str] | None = None
    source_info_link: str | None = None
    description: str | None = None
    last_updated: str | None = None


class Brand(BaseModel):
    """Brand information"""

    name: str | None = None
    link: str | None = None
    thumbnail: str | None = None
    rating: float | None = None
    reviews: int | None = None
    price_range: str | None = None


class Question(BaseModel):
    """Q&A question"""

    question: str | None = None
    link: str | None = None
    date: str | None = None
    answers: int | None = None
    source: str | None = None


class WebSource(BaseModel):
    """Web source article"""

    title: str | None = None
    link: str | None = None
    source: str | None = None
    date: str | None = None
    snippet: str | None = None
    thumbnail: str | None = None


class InlineShoppingItem(BaseModel):
    """Shopping item"""

    title: str | None = None
    link: str | None = None
    source: str | None = None
    price: str | None = None
    rating: float | None = None
    reviews: int | None = None
    thumbnail: str | None = None
    merchant: str | None = None
    delivery: str | None = None


class RelatedQuestionSource(BaseModel):
    """Source information for related questions"""

    title: str | None = None
    link: str | None = None
    source: str | None = None
    domain: str | None = None
    displayed_link: str | None = None
    favicon: str | None = None
    content: str | None = None


class RelatedQuestion(BaseModel):
    """Related question information"""

    question: str | None = None
    answer: str | None = None
    answer_highlight: str | None = None
    date: str | None = None
    source: RelatedQuestionSource | None = None


class GoogleSearchResponse(BaseModel):
    """Complete response from Google Search API"""

    search_metadata: SearchMetadata | None = None
    search_parameters: SearchParameters | None = None
    search_information: SearchInformation | None = None
    knowledge_graph: KnowledgeGraph | None = None
    organic_results: list[OrganicResult] | None = []
    discussions_and_forums: list[DiscussionForum] | None = None
    inline_videos: list[InlineVideo] | None = None
    inline_videos_more_link: str | None = None
    inline_tweets: InlineTweets | None = None
    inline_images: InlineImages | None = None
    inline_recipes: list[Recipe] | None = None
    inline_shopping: list[InlineShoppingItem] | None = None
    top_stories: list[TopStory] | None = None
    perspectives: list[Perspective] | None = None
    courses: list[Course] | None = None
    questions_and_answers: list[Question] | None = None
    web_sources: list[WebSource] | None = None
    explore_brands: list[Brand] | None = None
    related_searches: list[RelatedSearch] | None = []
    pagination: Pagination | None = None
    related_questions: list[RelatedQuestion] = Field(default_factory=list, validate_default=True)

    class Config:
        extra = "ignore"

    @model_validator(mode="before")
    def check_unknown_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Check for fields in raw JSON that aren't defined in the model

        Args:
            values: Raw dictionary of values

        Returns:
            Dict[str, Any]: Validated values
        """
        model_fields = cls.model_fields.keys()
        unknown_fields = set(values.keys()) - set(model_fields)

        if unknown_fields:
            logger.warning("Found fields in JSON not defined in Product model: " f"{', '.join(unknown_fields)}")

            # Log the values of unknown fields for analysis
            for field in unknown_fields:
                logger.warning(f"Unknown field '{field}' has value: {values[field]}")

        return values

    @model_validator(mode="before")
    def filter_none_values(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Filter out None values from related_questions list"""
        if "related_questions" in values and values["related_questions"]:
            values["related_questions"] = [q for q in values["related_questions"] if q is not None]
        return values


async def search_google(
    query: str,
    location: str = "California,United States",
    language: str = "en",
    country: str = "us",
    num_results: int = 10,
    start_index: int = 0,
    save_debug: bool = True,
    scrape_content: bool = False,
) -> GoogleSearchResponse:
    """
    Search Google using SearchAPI.io and fetch content for relevant links

    Args:
        query: Search query string
        location: Search location string
        language: Language code
        country: Country code
        num_results: Number of results to return (max 100)
        start_index: Starting index for pagination
        save_debug: Whether to save debug directory
        scrape_content: Whether to fetch content from links

    Returns:
        GoogleSearchResponse object containing search results with fetched content

    Raises:
        httpx.HTTPError: If the API request fails
        ValueError: If API key is not found
    """
    url = "https://www.searchapi.io/api/v1/search"

    settings = get_settings()
    api_key = settings.SEARCHAPI_API_KEY
    if not api_key:
        raise ValueError("SEARCHAPI_API_KEY not found in settings")

    params = {
        "engine": "google",
        "q": query,
        "location": location,
        "gl": country,
        "hl": language,
        "num": min(num_results, 100),
        "start": start_index,
        "api_key": api_key,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()

        response_json = response.json()
        search_response = GoogleSearchResponse.model_validate(response_json)

        # Save initial response if debug is enabled
        if save_debug:
            debug_dir = Path("debug/google_search")
            debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            initial_file = debug_dir / f"{timestamp}_initial.json"
            initial_file.write_text(json.dumps(search_response.model_dump(), indent=2))
            logger.info(f"Saved initial response to {initial_file}")

        if scrape_content:
            logger.info(f"Starting content scraping for query: {query}")
            links_to_fetch = set()

            if search_response.organic_results:
                organic_links = {result.link for result in search_response.organic_results if result.link}
                logger.debug(f"Found {len(organic_links)} organic result links")
                links_to_fetch.update(organic_links)

            if search_response.discussions_and_forums:
                forum_links = {forum.link for forum in search_response.discussions_and_forums if forum.link}
                logger.debug(f"Found {len(forum_links)} discussion forum links")
                links_to_fetch.update(forum_links)

            if search_response.inline_videos:
                video_links = {video.link for video in search_response.inline_videos if video.link}
                logger.debug(f"Found {len(video_links)} video links")
                links_to_fetch.update(video_links)

            if search_response.perspectives:
                perspective_links = {perspective.link for perspective in search_response.perspectives if perspective.link}
                logger.debug(f"Found {len(perspective_links)} perspective links")
                links_to_fetch.update(perspective_links)

            if search_response.related_questions:
                question_links = {question.source.link for question in search_response.related_questions if question.source and question.source.link}
                logger.debug(f"Found {len(question_links)} related question links")
                links_to_fetch.update(question_links)

            logger.info(f"Total unique links to fetch: {len(links_to_fetch)}")

            if links_to_fetch:
                logger.info("Starting batch fetch of content")
                fetched_contents = await fetch_batch(list(links_to_fetch))
                logger.info(f"Successfully fetched {len(fetched_contents)} contents")

                # Update content fields
                updated_count = 0
                if search_response.organic_results:
                    for result in search_response.organic_results:
                        if result.link in fetched_contents:
                            result.content = fetched_contents[result.link]
                            updated_count += 1

                if search_response.discussions_and_forums:
                    for forum in search_response.discussions_and_forums:
                        if forum.link in fetched_contents:
                            forum.content = fetched_contents[forum.link]
                            updated_count += 1

                if search_response.inline_videos:
                    for video in search_response.inline_videos:
                        if video.link in fetched_contents:
                            video.content = fetched_contents[video.link]
                            updated_count += 1

                if search_response.perspectives:
                    for perspective in search_response.perspectives:
                        if perspective.link in fetched_contents:
                            perspective.content = fetched_contents[perspective.link]
                            updated_count += 1

                if search_response.related_questions:
                    for question in search_response.related_questions:
                        if question.source and question.source.link in fetched_contents:
                            question.source.content = fetched_contents[question.source.link]
                            updated_count += 1

                logger.info(f"Updated content for {updated_count} results")

        if save_debug:
            debug_dir = Path("debug/searchapi/google_search")
            debug_dir.mkdir(parents=True, exist_ok=True)

            filename = f"{query[:50]}.json".replace(" ", "_")
            filepath = debug_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(search_response.model_dump(exclude_none=True), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved debug response to {filepath}")

        return search_response  # type: ignore

    except httpx.HTTPError as e:
        logger.error(f"API request failed: {str(e)}")
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Response text: {e.response.text}")
        raise


async def fetch_url(url: str, client: httpx.AsyncClient) -> str:
    """
    Fetch content from a single URL

    Args:
        url: URL to fetch
        client: httpx AsyncClient instance

    Returns:
        Fetched content as string
    """
    try:
        response = await client.get(url, follow_redirects=True)
        response.raise_for_status()
        text = str(response.text)
        return text
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return ""


if __name__ == "__main__":
    load_dotenv()
    # init_logfire()
    queries = [
        "Murad Retinol Youth Renewal Serum",
        "Samsonite Freeform 21-Inch Hardside Carry-On Luggage with Spinner Wheels",
        "Orgain Organic Vegan 21g Protein Powder",
        "NEW Lego Friends Central Perk Cafe (21319) BRAND",
        "Nespresso Vertuo Pop+ Combination Espresso and Coffee Maker",
        "Big Daisy Earrings with Opal in Sterling Silver, Woodstock Festival Statement Jewelry",
        "Nike Free Metcon 6",
        "Sharper Image Power Percussion Pro+ Hot + Cold Percussion Massager",
        "LG - Counter-Depth MAX 25.5 Cu. Ft. French Door Smart Refrigerator with Dual Ice - Stainless Steel",
        "Galaxy Z Flip6",
        "Aquaphor Aquaphor Healing Ointment",
        "Insta360 X4 Standard Bundle - Waterproof 8K 360 Action Camera",
        "BÅRSLÖV",
        "Side Knot Sleeveless Sheath Midi Dress",
        "RYOBI ONE+ 18V Lithium-Ion 4.0 Ah Battery, 2.0 Ah Battery, and Charger Kit with ONE+ Hybrid WHISPER SERIES 7-1/2 in. Fan review",
        "Bones & Chews All-Natural Beef Lung Dehydrated Dog Treats",
        "MICHAEL Michael Kors Sallie Medium Crossbody",
        "Cestar Coffee Table",
        "Gap Modern Rib Cropped T-Shirt",
        "Zara TRF DENIM OVERSHIRT",
    ]
    for query in queries:
        results = asyncio.run(search_google(query + " review", scrape_content=True))
        if results and results.organic_results:
            logger.info(f"Found {len(results.organic_results)} results")
            for result in results.organic_results[:3]:
                logger.info(f"Title: {result.title}")
                logger.info(f"Link: {result.link}")
                logger.info("---")
        else:
            logger.warning("No search results found")
