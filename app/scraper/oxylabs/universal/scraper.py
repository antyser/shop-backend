"""Universal scraper using Oxylabs API"""

import json
from pathlib import Path

import httpx
from loguru import logger

from app.config import get_settings


def save_debug_response(url: str, data: dict) -> None:
    """Save raw response data for debugging

    Args:
        url: Target URL that was scraped
        data: Raw response data to save
    """
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)

    # Create safe filename from URL
    safe_name = "".join(c if c.isalnum() else "_" for c in url.split("//")[-1])[:100]
    json_path = debug_dir / f"{safe_name}_response.json"

    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Saved raw response to {json_path}")


async def fetch_universal_raw(target_url: str) -> dict:
    """Make a raw API call to Oxylabs universal scraper and return the complete response

    Args:
        target_url: Target URL to scrape

    Returns:
        dict: Complete JSON response from Oxylabs API

    Raises:
        HTTPError: If API request fails
        ValueError: If credentials are missing
    """
    settings = get_settings()
    username = settings.OXYLABS_USERNAME
    password = settings.OXYLABS_PASSWORD

    if not username or not password:
        raise ValueError("Oxylabs credentials required. Set OXYLABS_USERNAME and OXYLABS_PASSWORD env vars.")

    api_url = "https://realtime.oxylabs.io/v1/queries"
    payload = {"source": "universal", "url": target_url, "parse": False}  # Get raw HTML

    logger.info(f"Fetching {target_url} via Oxylabs universal scraper")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, auth=(username, password), timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching {target_url}: {str(e)}")
        raise


async def fetch_universal(target_url: str) -> str:
    """Fetch any webpage using Oxylabs universal scraper and return raw HTML

    Args:
        target_url: Target URL to scrape

    Returns:
        str: Raw HTML content from the webpage

    Raises:
        HTTPError: If API request fails
        ValueError: If credentials are missing or no content returned
    """
    try:
        data = await fetch_universal_raw(target_url)

        # Debug the actual structure
        logger.debug(f"Response structure: {json.dumps(data, indent=2)[:500]}...")

        # Extract HTML content from response
        if "results" not in data or not data["results"]:
            logger.error("No results found in response")
            raise ValueError("No results found in response")

        result = data["results"][0]

        # Debug the result structure
        logger.debug(f"Result structure: {json.dumps(result, indent=2)[:500]}...")

        # Check if content is a string or dict
        if "content" not in result:
            logger.error("No content found in result")
            raise ValueError("No content found in result")

        content = result["content"]

        # Handle different response formats
        if isinstance(content, str):
            # Content is directly a string
            html_content = content
        elif isinstance(content, dict):
            # Content is a dictionary, try to get html field
            if "html" not in content:
                logger.error("No HTML content found in dictionary")
                raise ValueError("No HTML content found")
            html_content = content["html"]
        else:
            logger.error(f"Unexpected content type: {type(content)}")
            raise ValueError(f"Unexpected content type: {type(content)}")

        if not isinstance(html_content, str):
            raise ValueError("Invalid HTML content type")

        return html_content

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Failed to extract HTML content: {e}")
        if "data" in locals():
            logger.debug(f"Raw response: {data}")
        raise ValueError("Invalid response structure from Oxylabs API") from e


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv

    load_dotenv(override=True)

    # Test Reddit URL
    reddit_url = "https://www.reddit.com/r/keurig/comments/ytv37m/ksupreme_vs_kelite/"

    try:
        response = asyncio.run(fetch_universal(reddit_url))

        # Access and print content
        logger.info(f"Content Length: {len(response)}")
        logger.info(f"Content Preview: {response[:500]}...")

    except Exception as e:
        logger.error(f"Failed to fetch URL: {str(e)}")
        raise
