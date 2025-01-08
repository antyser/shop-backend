import asyncio
from typing import Any

from loguru import logger

from tools.google_shopping.api import get_google_product, search_google_shopping
from tools.parser.parse_product import parse_product_details
from util import atimer


@atimer
async def research(url: str) -> dict[str, Any]:
    """
    Research a product by parsing its URL and fetching additional details from Google Shopping.

    This function performs the following steps:
    1. Parses the product details from the provided URL
    2. Searches Google Shopping using the extracted product name
    3. Retrieves detailed product information using Google Shopping's product ID

    Args:
        url (str): Product URL from any supported shopping site (e.g., Amazon, Walmart, etc.)

    Returns:
        dict[str, Any]: A dictionary containing:
            - original_details: Parsed information from the original URL
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
        #     "original_details": {...},
        #     "google_shopping_details": {...}
        # }
        ```
    """
    # Extract product details using the existing parser
    logger.info(f"Parsing product details from URL: {url}")
    parsed_details: dict[str, str | None] = await parse_product_details(url)

    if not parsed_details.get("product_name"):
        raise ValueError("Could not extract product name from URL")

    # Search Google Shopping using the extracted product name
    logger.info(f"Searching Google Shopping for: {parsed_details['product_name']}")
    if not parsed_details["product_name"]:
        raise ValueError("Could not extract product name from URL")
    search_results = search_google_shopping(query=parsed_details["product_name"])
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
        "original_details": parsed_details,
        "google_shopping_details": product_details,
    }


# Example usage
if __name__ == "__main__":
    product_url = "https://www.amazon.com/Aquaphor-Advanced-Therapy-Ointment-Protectant/dp/B0107QP1VE"
    result: dict[str, Any] = asyncio.run(research(product_url))
    logger.info(f"Research results: {result}")
