import asyncio
from typing import Any

from loguru import logger

from tools.google_shopping.api import get_google_product, search_google_shopping
from tools.parser.product_parser import get_product_name


async def research(url: str) -> dict[str, Any]:
    """
    Research a product by extracting its name and fetching additional details from Google Shopping.

    This function performs the following steps:
    1. Extracts the product name from the provided URL using multiple methods:
       - Structured data (JSON-LD, microdata)
       - Meta tags or title
       - First H1 tag as fallback
    2. Searches Google Shopping using the extracted product name
    3. Retrieves detailed product information using Google Shopping's product ID

    Args:
        url (str): Product URL from any supported shopping site

    Returns:
        dict[str, Any]: A dictionary containing:
            - original_details: Product name from the original URL
            - google_shopping_details: Additional product information from Google Shopping

    Raises:
        ValueError: In the following cases:
            - Product name cannot be extracted from the URL
            - No shopping results found on Google Shopping
            - No product ID found in the first search result

    Example:
        ```python
        url = "https://www.amazon.com/product-name/dp/B12345"
        result = await research(url)
        # Returns: {
        #     "original_details": {"product_name": "Example Product"},
        #     "google_shopping_details": {...}
        # }
        ```
    """
    # Extract product name using the new function
    logger.info(f"Extracting product name from URL: {url}")
    product_name = await get_product_name(url)

    if not product_name:
        raise ValueError("Could not extract product name from URL")

    # Search Google Shopping using the extracted product name
    logger.info(f"Searching Google Shopping for: {product_name}")
    search_results = search_google_shopping(query=product_name)
    logger.info(f"Search results: {search_results}")

    if not search_results.shopping_results or len(search_results.shopping_results) == 0:
        raise ValueError("No shopping results found")

    # Get the first result's product ID
    first_result = search_results.shopping_results[0]
    if not first_result.product_id:
        raise ValueError("No product ID found in first result")

    # Get detailed product information
    logger.info(f"Fetching detailed product information for ID: {first_result.product_id}")
    product_details = get_google_product(first_result.product_id)

    return {
        "original_details": {"product_name": product_name},
        "google_shopping_details": product_details,
    }


# Example usage
if __name__ == "__main__":
    import sys

    # Default URL if none provided
    default_url = "https://www.amazon.com/Aquaphor-Advanced-Therapy-Ointment-Protectant/dp/B0107QP1VE"

    # Get URL from command line argument if provided, otherwise use default
    product_url = sys.argv[1] if len(sys.argv) > 1 else default_url

    logger.info(f"Researching product URL: {product_url}")
    result: dict[str, Any] = asyncio.run(research(product_url))
    logger.info(f"Research results: {result}")
