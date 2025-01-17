import asyncio
import os
import sys
from datetime import datetime

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel
from scraper.crawler.html_fetcher import fetch_batch

# Load environment variables
load_dotenv()

# Get proxy config from environment
PROXY_HOST = "brd.superproxy.io"
PROXY_PORT = "33335"
PROXY_USERNAME = os.getenv("BRIGHT_DATA_USERNAME")
PROXY_PASSWORD = os.getenv("BRIGHT_DATA_PASSWORD")


class GeneralInfo(BaseModel):
    """General information about the search"""

    search_engine: str
    language: str
    location: str | None = None
    results_area: str | None = None
    mobile: bool
    basic_view: bool
    search_type: str | None = None
    page_title: str | None = None
    timestamp: datetime | None = None


class InputInfo(BaseModel):
    """Input parameters for the search"""

    original_url: str
    request_id: str


class NavigationLink(BaseModel):
    """Navigation link in search results"""

    title: str
    href: str


class Extension(BaseModel):
    """Extension for organic search result"""

    type: str
    link: str | None = None
    text: str | None = None
    rank: int | None = None


class OrganicResult(BaseModel):
    """Organic search result"""

    link: str
    display_link: str
    title: str
    description: str | None = None
    extensions: list[Extension] | None = None
    rank: int
    global_rank: int
    image: str | None = None
    image_alt: str | None = None
    image_base64: str | None = None
    last_modified_date: str | None = None
    content: str | None = None


class RelatedSearch(BaseModel):
    """Related search suggestion"""

    text: str | None = None
    link: str | None = None
    items: list[dict] | None = None
    rank: int
    global_rank: int


class TableCell(BaseModel):
    """Cell in a table answer"""

    text: str


class AnswerListItem(BaseModel):
    """Item in an ordered list answer"""

    value: str
    rank: int


class AnswerValue(BaseModel):
    """Value field in an answer"""

    text: str | None = None


class Answer(BaseModel):
    """Answer content for people also ask"""

    type: str
    value: AnswerValue | None = None
    link: str | None = None
    title: str | None = None
    items: list[AnswerListItem] | list[list[TableCell]] | None = None
    rank: int

    class Config:
        """Allow extra fields in response"""

        extra = "ignore"


class PeopleAlsoAsk(BaseModel):
    """Question and answers in people also ask section"""

    question: str
    answer_source: str
    answer_link: str
    answer_display_link: str
    answers: list[Answer]
    rank: int
    global_rank: int

    class Config:
        extra = "ignore"


class GoogleSearchResult(BaseModel):
    """Complete Google search result"""

    general: GeneralInfo
    input: InputInfo
    navigation: list[NavigationLink] | None = None
    organic: list[OrganicResult]
    related: list[RelatedSearch] | None = None
    people_also_ask: list[PeopleAlsoAsk] | None = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
        extra = "ignore"


async def google_search(query: str, scrape_content: bool = False) -> GoogleSearchResult | None:
    """
    Scrape Google search results using Bright Data proxy

    Args:
        query: Search query string
        scrape_content: If True, scrapes content from organic result links

    Returns:
        GoogleSearchResult object containing parsed results
        or None if request fails
    """
    try:
        # Validate proxy credentials exist
        if not all([PROXY_USERNAME, PROXY_PASSWORD]):
            logger.error("Missing proxy credentials in environment")
            return None

        # Format proxy auth and URL
        proxy_auth = aiohttp.BasicAuth(PROXY_USERNAME, PROXY_PASSWORD)
        url = f"https://www.google.com/search?q={query}&gl=us&hl=en&brd_json=1"

        # Make request through proxy
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=f"http://{PROXY_HOST}:{PROXY_PORT}", proxy_auth=proxy_auth, ssl=False) as response:
                if response.status != 200:
                    logger.error(f"Google search failed with status {response.status}")
                    return None

                data = await response.json()
                # Debug: Print raw data structure
                logger.debug("Raw response data:")
                logger.debug(data)

                # Debug: Print people_also_ask structure specifically
                if "people_also_ask" in data:
                    logger.debug("People also ask structure:")
                    logger.debug(data["people_also_ask"])

                search_result = GoogleSearchResult(**data)

                # Optionally scrape content from organic results
                if scrape_content and search_result.organic:
                    urls = [r.link for r in search_result.organic]
                    url_to_content = await fetch_batch(urls)

                    # Update organic results with scraped content
                    for organic_result in search_result.organic:
                        organic_result.content = url_to_content.get(organic_result.link)

                return search_result

    except Exception as e:
        logger.error(f"Error scraping Google search: {str(e)}")
        return None


if __name__ == "__main__":
    # Set debug level for logger
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    result = asyncio.run(google_search("Apple AirPods Pro", True))
    if result:
        print(result.organic)
