import asyncio
import os

import agentql
from dotenv import load_dotenv
from loguru import logger
from playwright.async_api import async_playwright

from util import timer

# Load environment variables from .env file
load_dotenv()

# Configure loguru
logger.add("scraper.log", rotation="500 MB", level="INFO")


@timer
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

            # Log warning for any missing fields
            for field, value in result.items():
                if value is None:
                    logger.warning(f"Failed to extract {field} from {url}")

            logger.success(f"Successfully parsed product details: {result}")
            return result

    except Exception as e:
        logger.exception(f"Error parsing product details: {str(e)}")
        raise  # Re-raise the exception instead of returning None


# Example usage
if __name__ == "__main__":
    product_url = "https://www.amazon.com/Unscented-Dishwasher-AspenClean-Plant-Based-Detergent/dp/B09X6FPH1L"
    result: dict[str, str | None] = asyncio.run(parse_product_details(product_url))
    if result:
        logger.info(f"Product Details: {result}")
