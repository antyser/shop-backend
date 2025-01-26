import asyncio

from loguru import logger

from app.scraper.crawler.html_fetcher import fetch_batch
from app.scraper.models import (
    ScrapeProductResponse,
    ScrapeResponse,
    ScrapeSearchResponse,
)
from app.scraper.oxylabs.amazon.product_scraper import fetch_amazon_product
from app.scraper.searchapi.google_search import search_google
from app.scraper.utils import extract_asin_and_slug, is_amazon_url


async def scrape_links(urls: list[str]) -> ScrapeResponse:
    """
    Scrape content from multiple URLs

    Args:
        urls: List of URLs to scrape

    Returns:
        ScrapeResponse containing mapping of URLs to their scraped content
    """
    results = await fetch_batch(urls)
    return ScrapeResponse(results=results)


async def scrape_product(url: str) -> ScrapeProductResponse:
    """
    Scrape product information and related search results using Oxylabs API
    and Google Search

    Args:
        url: Amazon product URL

    Returns:
        ScrapeProductResponse containing product and search information

    Raises:
        ValueError: If URL is invalid or scraping fails
    """
    if not is_amazon_url(url):
        raise ValueError("Only Amazon URLs are supported")

    try:
        asin, slug = extract_asin_and_slug(url)

        if slug:
            # Convert slug to search query and run tasks in parallel
            search_query = f"{slug} review"
            product_task = fetch_amazon_product(asin)
            search_task = search_google(query=search_query, scrape_content=True)
            product_data, search_response = await asyncio.gather(product_task, search_task)
            product = product_data.results[0].content.model_dump()

        else:
            # Fetch product first to get title for search
            product_data = await fetch_amazon_product(asin)
            product = product_data.results[0].content.model_dump()

            # Search using product title
            search_response = await search_google(query=f"{product['title']} review", scrape_content=True)

        return ScrapeProductResponse(
            product=product,
            url=url,
            search_results=search_response,
        )

    except Exception as e:
        logger.error(f"Error scraping product {url}: {str(e)}")
        raise ValueError(f"Failed to scrape product: {str(e)}") from e


async def scrape_search(query: str) -> ScrapeSearchResponse:
    """
    Scrape Google search results

    Args:
        query: Search query string

    Returns:
        ScrapeSearchResponse containing search results
    """
    search_response = await search_google(query=query, scrape_content=True)
    return ScrapeSearchResponse(results=search_response)
