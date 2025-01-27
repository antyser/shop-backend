import httpx
from loguru import logger
from pydantic import ValidationError

from app.config import get_settings
from app.scraper.oxylabs.walmart.models import OxyWalmartResponse, QueryResult, WalmartProductContent


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

            # Extract product details
            product_content = WalmartProductContent(
                url=product_url,
                product_id=data.get("product_id"),
                title=data.get("title"),
                description=data.get("description"),
                brand=data.get("brand"),
                specifications=data.get("specifications"),
                price=data.get("price"),
                rating=data.get("rating"),
                fulfillment=data.get("fulfillment"),
                seller=data.get("seller"),
            )

            # Validate required fields with proper null checks
            if not product_content.price or product_content.price.price is None:
                raise ValueError("Missing required field: price")
            if not product_content.rating or product_content.rating.rating is None or product_content.rating.count is None:
                raise ValueError("Missing required field: rating")
            if not product_content.fulfillment or product_content.fulfillment.shipping is None:
                raise ValueError("Missing required field: fulfillment")
            if not product_content.seller or product_content.seller.name is None:
                raise ValueError("Missing required field: seller")

            return OxyWalmartResponse(results=[QueryResult(content=product_content)])

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching URL {product_url}: {str(e)}, " f"response: {response.text}")
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {e.errors()}")
        raise
    except Exception as e:
        logger.error(f"Error fetching URL {product_url}: {str(e)}")
        raise


if __name__ == "__main__":
    import asyncio
    import json
    from pathlib import Path

    from dotenv import load_dotenv

    load_dotenv(override=True)

    # Test URLs
    test_urls = [
        "https://www.walmart.com/ip/Orgain-Organic-Plant-Based-Protein-Powder-Sweet-Vanilla-Bean/553332207",
        "https://www.walmart.com/ip/Therabody-Theragun-Mini-2nd-Gen-Handheld-Percussive-Massager-Portable-Deep-Tissue-Massager-Gray/5150283577",
        "https://www.walmart.com/ip/Luxe-Weavers-Modern-Area-Rug-Abstract-Pattern-Dark-Blue-Light-Blue-8-x-10/3615138636",
        "https://www.walmart.com/ip/360-Oscillating-Toothbrush-Black-Black/5726850536",
        "https://www.walmart.com/ip/Coach-Women-s-Kristy-Shoulder-Bag/2100858768",
        "https://www.walmart.com/ip/Keurig-K-elite-Brewer-Slate/225142139",
        "https://www.walmart.com/ip/Cooper-Discoverer-All-Terrain-275-60R20-115T-All-Terrain-Tire/1090134873",
        "https://www.walmart.com/ip/Evenflo-Advanced-Double-Electric-Breast-Pump-with-Breastshields-and-Milk-Storage-Bottles-Clear/795240370",
    ]

    try:
        # Create output directory
        output_dir = Path("tests/data/walmart")
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, test_url in enumerate(test_urls):
            try:
                logger.info(f"\nFetching product {i+1}: {test_url}")
                response = asyncio.run(fetch_walmart_product(test_url))

                # Save response to a JSON file for testing
                output_file = output_dir / f"product_response_{i+1}.json"
                with open(output_file, "w") as f:
                    json.dump(response.model_dump(), f, indent=2, default=str)

            except Exception as e:
                logger.error(f"Failed to fetch product {i+1}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Failed to process products: {str(e)}")
        raise
