import asyncio

from loguru import logger

from app.scraper.crawler.html_fetcher import fetch_batch
from app.scraper.models import (
    ScrapeProductResponse,
    ScrapeResponse,
    ScrapeSearchResponse,
)
from app.scraper.oxylabs.amazon.product_scraper import fetch_amazon_product
from app.scraper.oxylabs.amazon.utils import (
    convert_to_unified_product as convert_amazon_product,
)
from app.scraper.oxylabs.walmart.product_scraper import fetch_walmart_product
from app.scraper.oxylabs.walmart.utils import (
    convert_to_unified_product as convert_walmart_product,
)
from app.scraper.searchapi.google_search import search_google
from app.scraper.utils import (
    extract_asin_and_slug,
    extract_walmart_id_and_slug,
    is_amazon_url,
    is_walmart_url,
    normalize_url,
)


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
        url: Product URL (Amazon or Walmart)

    Returns:
        ScrapeProductResponse containing product and search information

    Raises:
        ValueError: If URL is invalid or scraping fails
    """
    url = normalize_url(url)
    try:
        if is_amazon_url(url):
            asin, slug = extract_asin_and_slug(url)

            if slug:
                # Convert slug to search query and run tasks in parallel
                search_query = f"{slug.replace('-', ' ')} review"
                product_task = fetch_amazon_product(asin)
                search_task = search_google(query=search_query, scrape_content=True)
                product_data, search_response = await asyncio.gather(product_task, search_task)
                unified_product = convert_amazon_product(product_data.results[0].content)

            else:
                # Fetch product first to get title for search
                product_data = await fetch_amazon_product(asin)
                unified_product = convert_amazon_product(product_data.results[0].content)

                # Search using product title
                search_response = await search_google(query=f"{unified_product.title} review", scrape_content=True)

        elif is_walmart_url(url):
            # Extract product ID and slug
            product_id, slug = extract_walmart_id_and_slug(url)

            if slug:
                # Convert slug to search query and run tasks in parallel
                search_query = f"{slug.replace('-', ' ')} review"
                product_task = fetch_walmart_product(url)
                search_task = search_google(query=search_query, scrape_content=True)
                product_data, search_response = await asyncio.gather(product_task, search_task)
                unified_product = convert_walmart_product(product_data.results[0].content)
            else:
                # Fetch product first to get title for search
                product_data = await fetch_walmart_product(url)
                unified_product = convert_walmart_product(product_data.results[0].content)

                # Search using product title
                search_response = await search_google(query=f"{unified_product.title} review", scrape_content=True)

        else:
            raise ValueError("Only Amazon and Walmart URLs are supported")

        return ScrapeProductResponse(
            url=url,
            product=unified_product,
            search_results=search_response,
        )

    except Exception as e:
        logger.error(f"Failed to scrape product: {str(e)}")
        raise


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
