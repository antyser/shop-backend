from product.model import Product
from product.parser import parse_amazon_product

from app.scraper.bright_data.amazon import scrape_amazon_product


def is_amazon_url(url: str) -> bool:
    """Check if the URL is from Amazon

    Args:
        url: The URL to check

    Returns:
        bool: True if URL is from Amazon, False otherwise
    """
    return "amazon." in url.lower()


async def get_product(url: str) -> Product | None:
    """Get product metadata from URL

    Args:
        url: Product URL to scrape

    Returns:
        Product | None: Parsed product metadata or None if not found

    Raises:
        ValueError: If website is not supported
    """
    if not is_amazon_url(url):
        raise ValueError("Only Amazon products are supported")

    response = await scrape_amazon_product([url])
    if not response or not response.products:
        return None
    return parse_amazon_product(response.products[0])
