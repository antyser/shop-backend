import json
import os
from typing import Any

import agentql
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright
from playwright_dompath.dompath_sync import xpath_path
from scraper.crawler.html_fetcher import fetch
from tools.parser.models.product_metadata import ProductMetadata
from tools.parser.product_metadata_parser import extract_product_metadata

# Load environment variables from .env file
load_dotenv()

# Configure loguru
logger.add("scraper.log", rotation="500 MB", level="INFO")


async def parse_product_details(url: str) -> dict[str, str | None]:
    """Extract basic product information from a product page using AgentQL.

    Args:
        url (str): URL of the product page to parse

    Returns:
        Dict[str, Optional[str]]: Product information including name, description, rating, and price

    Raises:
        ValueError: If AGENTQL_API_KEY is not found in environment variables
    """
    # Verify API key is set
    if not os.getenv("AGENTQL_API_KEY"):
        logger.error("AGENTQL_API_KEY not found in environment variables")
        raise ValueError("AGENTQL_API_KEY not found in environment variables")

    logger.info(f"Starting to parse product details from: {url}")
    try:
        async with (
            async_playwright() as playwright,
            await playwright.chromium.launch(headless=True) as browser,  # Run in headless mode for production
        ):
            # Create and wrap page with AgentQL
            page = await agentql.wrap_async(browser.new_page())
            await page.goto(url)
            logger.debug(f"Successfully loaded page: {url}")

            # Query for product details
            product_query = """
            {
                product_name
                description
                rating
                price
            }
            """

            product_data = await page.query_elements(product_query)

            result: dict[str, str | None] = {
                "product_name": ((await product_data.product_name.text_content()).strip() if product_data.product_name else None),
                "description": ((await product_data.description.text_content()).strip() if product_data.description else None),
                "rating": ((await product_data.rating.text_content()).strip() if product_data.rating else None),
                "price": ((await product_data.price.text_content()).strip() if product_data.price else None),
            }
            logger.info(f"product_name xpath: {xpath_path(product_data.product_name)}")

            logger.info(f"Product data: {product_data}")

            # Log warning for any missing fields
            for field, value in result.items():
                if value is None:
                    logger.warning(f"Failed to extract {field} from {url}")

            logger.success(f"Successfully parsed product details: {result}")
            return result

    except Exception as e:
        logger.exception(f"Error parsing product details: {str(e)}")
        raise  # Re-raise the exception instead of returning None


def get_title_from_html(html: str) -> str | None:
    """Extract title from HTML content"""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Try meta tags first
        meta_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "title"})
        if meta_title and meta_title.get("content"):
            content = meta_title.get("content")
            return str(content).strip() if content else None

        # Fall back to title tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title_string = title_tag.string
            return str(title_string).strip() if title_string else None

        return None
    except Exception as e:
        logger.error(f"Failed to parse HTML title: {str(e)}")
        return None


async def get_product_name(url: str) -> str | None:
    """Get the product name from the product page using multiple fallback methods:
    1. Try to extract from structured data (JSON-LD, microdata)
    2. Try to get from meta tags or title
    3. Finally, try to get from the first h1 tag

    Args:
        url (str): URL of the product page

    Returns:
        Optional[str]: Product name if found, None otherwise
    """
    # Get HTML content
    html_content = await fetch(url)
    if not html_content:
        return None

    try:
        # First try to extract structured product metadata
        product_metadata = extract_product_metadata(html_content)
        if product_metadata and product_metadata.name:
            name = str(product_metadata.name)
            logger.info(f"Found product name from structured data: {name}")
            return name

        # If no structured data, try to get title from HTML
        title = get_title_from_html(html_content)
        if title:
            title_str = str(title)
            logger.info(f"Found product name from HTML title: {title_str}")
            return title_str

        # Last resort: try to get the first h1 tag
        soup = BeautifulSoup(html_content, "html.parser")
        h1_tag = soup.find("h1")
        if h1_tag:
            h1_text = h1_tag.get_text(strip=True)
            if h1_text:
                text = str(h1_text)
                logger.info(f"Found product name from H1 tag: {text}")
                return text

        logger.warning(f"No product name found for URL: {url}")
        return None

    except Exception as e:
        logger.error(f"Error getting product name from {url}: {str(e)}")
        return None


def get_amazon_product_details(url: str) -> dict[str, Any | None]:
    """
    Scrape Amazon product details using requests and BeautifulSoup4.

    Args:
        url: The Amazon product URL to scrape

    Returns:
        Dictionary containing product details or empty dict if scraping fails
    """
    # Headers to mimic browser request
    headers = {
        "dnt": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "referer": "https://www.amazon.com/",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30, verify=True)

        if response.status_code > 500:
            logger.error(f"Request blocked by Amazon. Status code: {response.status_code}")
            return {}

        soup = BeautifulSoup(response.content, "html.parser")

        product_data: dict[str, Any | None] = {
            "product_name": _extract_text(soup, "#productTitle"),
            "price": _extract_text(soup, "#price_inside_buybox"),
            "rating": _extract_text(soup, "span.arp-rating-out-of-text"),
            "short_description": _extract_text(soup, "#featurebullets_feature_div"),
            "product_description": _extract_text(soup, "#productDescription"),
            "sales_rank": _extract_text(soup, "li#SalesRank"),
            "number_of_reviews": _extract_text(soup, "a.a-link-normal h2"),
            "images": _extract_images(soup, ".imgTagWrapper img"),
            "variants": _extract_variants(soup, "form.a-section li"),
        }

        logger.info(f"Successfully extracted product data from {url}")
        logger.debug(f"Product data: {json.dumps(product_data, indent=2)}")

        return product_data

    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        return {}
    except Exception as e:
        logger.exception(f"Error processing {url}: {str(e)}")
        return {}


def _extract_text(soup: BeautifulSoup, selector: str) -> str | None:
    """Extract and clean text content from a CSS selector."""
    element = soup.select_one(selector)
    if element and element.text:
        return " ".join(element.get_text(strip=True).split())
    return None


def _extract_images(soup: BeautifulSoup, selector: str) -> dict[str, str] | None:
    """Extract image URLs from data-a-dynamic-image attribute."""
    element = soup.select_one(selector)
    if element and element.get("data-a-dynamic-image"):
        try:
            image_data = json.loads(element["data-a-dynamic-image"])
            return {str(k): str(v) for k, v in image_data.items()}
        except json.JSONDecodeError:
            return None
    return None


def _extract_variants(soup: BeautifulSoup, selector: str) -> list[dict[str, str]] | None:
    """Extract product variants information."""
    variants: list[dict[str, str]] = []
    elements = soup.select(selector)

    for element in elements:
        name = element.get("title")
        asin = element.get("data-defaultasin")
        if name and asin:
            variants.append({"name": str(name), "asin": str(asin)})

    return variants if variants else None


async def parse_product_page(url: str) -> ProductMetadata | None:
    """
    Parse product page and extract metadata

    Args:
        url: Product page URL

    Returns:
        ProductMetadata if successful, None otherwise
    """
    try:
        # Fetch HTML content and await the result
        html_content = await fetch(url)
        if not html_content:
            logger.error(f"Failed to fetch content from {url}")
            return None

        # Now html_content is str, not a coroutine
        metadata = extract_product_metadata(html_content)
        if not metadata:
            logger.error(f"Failed to extract metadata from {url}")
            return None

        title = get_title_from_html(html_content)
        if not title:
            logger.error(f"Failed to extract title from {url}")
            return None

        # Create a new dict with all metadata fields and update title
        metadata_dict = metadata.model_dump()
        metadata_dict["name"] = title

        return ProductMetadata(**metadata_dict)

    except Exception as e:
        logger.error(f"Error parsing product page: {e}")
        return None


# Example usage
if __name__ == "__main__":
    import asyncio

    load_dotenv()
    links = [
        "https://www.amazon.com/Biodance-Bio-Collagen-Tightening-Hydrating-Molecular/dp/B0B2RM68G2",
        "https://www.ebay.com/itm/166865692877",
        "https://www.walmart.com/ip/Fresh-Hass-Avocados-Each/44390949",
        "https://www.moncler.com/en-us/men/outerwear/short-down-jackets/barbustel-hooded-short-down-jacket-black-J20911A00103596K7U99.html",
        "https://shop.lululemon.com/p/jackets-and-hoodies-jackets/StretchSeal-Sleet-Street-Long-Jacket/_/prod11570507?color=0001",
        "https://www.temu.com/golf-club-cover-head-cover-protective-cover-driver--wooden--cover-pusher-cover--edition-g-601099598085262.html",
        "https://www.nike.com/t/gato-mens-shoes-zRHXm1/HQ6019-001",
    ]

    async def fetch_and_log_product_names(links: list[str]) -> None:
        for link in links:
            result = await get_product_name(link)
            if result:
                logger.info(f"Product name: {result}")

    asyncio.run(fetch_and_log_product_names(links))
