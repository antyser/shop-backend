import httpx
from loguru import logger
from pydantic import BaseModel, Field


class ProductDetails(BaseModel):
    """Pydantic model for Amazon product details"""

    os: str | None = None
    ram: str | None = None
    asin: str
    color: str | None = None
    batteries: str | None = None
    form_factor: str | None = None
    item_weight: str | None = None
    manufacturer: str | None = None
    customer_reviews: str | None = None
    whats_in_the_box: str | None = None
    best_sellers_rank: str | None = None
    country_of_origin: str | None = None
    item_model_number: str | None = None
    product_dimensions: str | None = None
    battery_power_rating: str | None = None
    date_first_available: str | None = None
    other_display_features: str | None = None
    memory_storage_capacity: str | None = None
    connectivity_technologies: str | None = None
    ram_memory_installed_size: str | None = None
    standing_screen_display_size: str | None = None


class AmazonProduct(BaseModel):
    """Pydantic model for Amazon product response"""

    product_details: ProductDetails
    title: str
    price: float | None = None
    currency: str | None = None
    description: str | None = None
    images: list[str] | None = Field(default_factory=list)


async def fetch_amazon_product(asin: str, username: str, password: str, geo_location: str = "90210") -> AmazonProduct:
    """
    Fetch Amazon product details using Oxylabs API

    Args:
        asin: Amazon product ASIN
        username: Oxylabs API username
        password: Oxylabs API password
        geo_location: Geographic location for pricing

    Returns:
        AmazonProduct: Structured product data

    Raises:
        HTTPError: If API request fails
    """
    url = "https://realtime.oxylabs.io/v1/queries"

    payload = {"source": "amazon_product", "query": asin, "geo_location": geo_location, "parse": True}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, auth=(username, password), timeout=30.0)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Successfully fetched data for ASIN: {asin}")

            return AmazonProduct(**data["results"][0])

    except Exception as e:
        logger.error(f"Error fetching product {asin}: {str(e)}")
        raise
