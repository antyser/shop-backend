import json

import httpx
from loguru import logger
from pydantic import ValidationError

from app.config import get_settings
from app.scraper.oxylabs.walmart.models import (
    OxyWalmartResponse,
    parse_walmart_response,
)


async def fetch_walmart_product(product_url: str) -> OxyWalmartResponse:
    """
    Fetch Walmart product details using Oxylabs API

    Args:
        product_url: Full Walmart product URL

    Returns:
        OxyWalmartResponse: Complete Oxylabs response data

    Raises:
        HTTPError: If API request fails
        ValueError: If credentials are missing
    """
    settings = get_settings()
    username = settings.OXYLABS_USERNAME
    password = settings.OXYLABS_PASSWORD

    if not username or not password:
        raise ValueError("Oxylabs credentials required. Set OXYLABS_USERNAME and " "OXYLABS_PASSWORD env vars or pass directly.")

    api_url = "https://realtime.oxylabs.io/v1/queries"
    payload = {
        "source": "universal",
        "url": product_url,
        "geo_location": "United States",
        "parse": True,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, auth=(username, password), timeout=30.0)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched data for URL: {product_url}")

            # Log raw response for debugging
            logger.info(f"Raw response: {json.dumps(data, indent=2)}")

            # Parse response into OxyWalmartResponse model
            try:
                return parse_walmart_response(data)
            except ValidationError as e:
                logger.error(f"Validation error parsing response: {e.errors()}")
                raise

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching URL {product_url}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error fetching URL {product_url}: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio
    from pathlib import Path

    # Create debug directory
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)

    # Test URL
    url = "https://www.walmart.com/ip/Keurig-K-elite-Brewer-Slate/225142139"

    try:
        response = asyncio.run(fetch_walmart_product(url))

        # Save response to debug file
        debug_file = debug_dir / "walmart_product_response.json"
        with open(debug_file, "w") as f:
            json.dump(response.model_dump(), f, indent=2, default=str)
        logger.info(f"Response saved to {debug_file}")

    except Exception as e:
        logger.error(f"Failed to fetch product: {str(e)}", exc_info=True)
