import httpx
from loguru import logger
from pydantic import ValidationError

from app.config import get_settings
from app.scraper.oxylabs.amazon.models import OxyAmazonProductResponse


async def fetch_amazon_product(asin: str) -> OxyAmazonProductResponse:
    """
    Fetch Amazon product details using Oxylabs API

    Args:
        asin: Amazon product ASIN
        geo_location: Geographic location for pricing
        username: Optional Oxylabs API username (defaults to env var)
        password: Optional Oxylabs API password (defaults to env var)

    Returns:
        OxyAmazonProductResponse: Complete Oxylabs response data

    Raises:
        HTTPError: If API request fails
        ValueError: If credentials are missing
    """
    settings = get_settings()
    username = settings.OXYLABS_USERNAME
    password = settings.OXYLABS_PASSWORD

    if not username or not password:
        raise ValueError("Oxylabs credentials required. Set OXYLABS_USERNAME and " "OXYLABS_PASSWORD env vars or pass directly.")

    url = "https://realtime.oxylabs.io/v1/queries"
    payload = {"source": "amazon_product", "query": asin, "parse": True}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, auth=(username, password), timeout=30.0)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched data for ASIN: {asin}")

            return OxyAmazonProductResponse(**data)

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching product {asin}: {str(e)}, response: {response.text}")
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise
    except Exception as e:
        logger.error(f"Error fetching product {asin}: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv

    load_dotenv(override=True)

    try:
        # Example ASIN for CeraVe Hydrating Facial Cleanser
        response = asyncio.run(fetch_amazon_product("B07SH6HN2X"))

        # Access and print some product details
        product = response.results[0].content
        logger.info(f"Product Title: {product.title}")
        logger.info(f"Price: ${product.price}")
        logger.info(f"Rating: {product.rating}/5 ({product.reviews_count} reviews)")
        logger.info(f"Stock Status: {product.stock}")

    except Exception as e:
        logger.error(f"Failed to fetch product: {str(e)}")
        raise
