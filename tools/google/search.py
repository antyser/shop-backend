import os
from typing import Any

import requests
from dotenv import load_dotenv
from loguru import logger

from tools.crawler.html import OutputFormat, fetch_batch
from tools.google.models import OxyGoogleSearchResponse


def search_google(query: str, **kwargs: dict[str, Any]) -> OxyGoogleSearchResponse | None:
    """
    Search Google using Oxylabs API

    Args:
        query: Search query string
        **kwargs: Additional parameters for the search

    Returns:
        OxyGoogleSearchResponse if successful, None otherwise

    Raises:
        requests.RequestException: If the request fails
    """
    username = os.getenv("OXYLABS_USERNAME")
    password = os.getenv("OXYLABS_PASSWORD")

    if not username or not password:
        logger.error("Missing Oxylabs credentials")
        return None

    url = "https://realtime.oxylabs.io/v1/queries"

    payload = {"source": "google_search", "domain": "com", "query": query, "parse": True, **kwargs}

    try:
        response = requests.post(url, json=payload, auth=(username, password), timeout=30.0)
        response.raise_for_status()

        return OxyGoogleSearchResponse(**response.json())

    except requests.RequestException as e:
        logger.error(f"Request error occurred: {e}")
        return None
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        return None


async def crawl_search_results(
    response: OxyGoogleSearchResponse, max_workers: int = 5, output_format: OutputFormat = OutputFormat.MARKDOWN
) -> list[dict[str, str | None]]:
    """
    Crawl organic search results in parallel

    Args:
        response: Oxylabs search response
        max_workers: Maximum number of concurrent requests
        output_format: Desired output format for content

    Returns:
        List of dictionaries containing URL and content
    """
    if not response or not response.results:
        logger.error("Invalid search response")
        return []

    # Safely handle potentially None organic_results
    organic_results = response.results[0].content.results.organic if (response.results and response.results[0].content.results.organic) else []

    urls = [result.url for result in organic_results if result and result.url]

    url_content_map = await fetch_batch(urls, output_format=output_format, max_concurrent=max_workers)

    return [{"url": url, "content": content} for url, content in url_content_map.items()]


async def main() -> None:
    """Run the main search and crawl process"""
    load_dotenv()

    response = search_google("iphone 16 pro review")

    if response:
        crawled_results = await crawl_search_results(response, output_format=OutputFormat.MARKDOWN)

        for result in crawled_results:
            print(f"\nURL: {result['url']}")
            if result["content"]:
                print("Content preview:", result["content"][:1000] + "...")
            else:
                print("Failed to fetch content")
            print("-" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
