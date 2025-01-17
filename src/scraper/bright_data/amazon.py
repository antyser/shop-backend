import asyncio
import os
from datetime import datetime
from typing import Any

import httpx
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field, field_validator, model_validator

from src.scraper.bright_data.management_api import get_snapshot_status

DATASET_ID = "gd_l7q7dkf244hwjntr0"
MAX_WAIT_TIME = 30
POLL_INTERVAL = 1


class ProductVariation(BaseModel):
    """Product variation details"""

    asin: str | None = None
    currency: str | None = None
    name: str | None = None
    price: float | None = None
    unit_price: str | None = None


class ProductDetail(BaseModel):
    """Product detail key-value pair"""

    type: str
    value: str


class ProductDescription(BaseModel):
    """Product description content"""

    type: str
    url: str


class OtherSellerPrice(BaseModel):
    """Other seller pricing information"""

    delivery: str
    num_of_ratings: int
    price: float
    price_per_unit: float | None = None
    seller_name: str
    seller_rating: float
    seller_url: str | None = None
    ships_from: str
    unit: str | None = None


class SubcategoryRank(BaseModel):
    """Subcategory ranking information"""

    subcategory_name: str
    subcategory_rank: int


class BuyboxPrices(BaseModel):
    """Buybox price details"""

    price: str | None = None
    unit_price: str | None = None
    currency: str | None = None


class PricesBreakdown(BaseModel):
    """Price breakdown information"""

    deal_type: str | None = None
    list_price: float | None = None
    typical_price: float | None = None


class Product(BaseModel):
    """Main product information schema"""

    title: str | None = None
    seller_name: str | None = None
    brand: str | None = None
    description: str | None = None
    initial_price: float | None = None
    final_price: float | None = None
    currency: str | None = None
    availability: str | None = None
    reviews_count: int | None = None
    categories: list[str] | None = None
    asin: str | None = None
    buybox_seller: str | None = None
    number_of_sellers: int | None = None
    root_bs_rank: int | None = None
    answered_questions: int | None = None
    domain: str | None = None
    images_count: int | None = None
    url: str | None = None
    video_count: int | None = None
    image_url: str | None = None
    item_weight: str | None = None
    rating: float | None = None
    product_dimensions: str | None = None
    seller_id: str | None = None
    date_first_available: str | None = None
    discount: float | None = None
    model_number: str | None = None
    manufacturer: str | None = None
    department: str | None = None
    plus_content: bool | None = None
    upc: str | None = None
    video: bool | None = None
    top_review: str | None = None
    variations: list[ProductVariation] | None = Field(default_factory=list, description="Product variations")
    delivery: list[str] | None = None
    features: list[str] | None = None
    format: list[dict[str, Any]] | None = None
    buybox_prices: BuyboxPrices | None = None
    parent_asin: str | None = None
    input_asin: str | None = None
    ingredients: str | None = None
    origin_url: str | None = None
    bought_past_month: int | None = None
    is_available: bool | None = None
    root_bs_category: str | None = None
    bs_category: str | None = None
    bs_rank: int | None = None
    badge: str | None = None
    subcategory_rank: list[SubcategoryRank] | None = None
    amazon_choice: bool | None = None
    images: list[str] | None = None
    product_details: list[ProductDetail] | None = None
    prices_breakdown: PricesBreakdown | None = None
    country_of_origin: str | None = None
    from_the_brand: list[str] | None = None
    product_description: list[ProductDescription] | None = None
    seller_url: str | None = None
    customer_says: str | None = None
    sustainability_features: list[dict[str, Any]] | None = None
    climate_pledge_friendly: bool | None = None
    videos: list[str] | None = None
    other_sellers_prices: list[dict[str, Any]] | None = Field(default_factory=list, description="Prices from other sellers")
    downloadable_videos: list[str] | None = None
    timestamp: datetime | None = None

    @model_validator(mode="before")  # type: ignore
    def check_unknown_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Check for fields in raw JSON that aren't defined in the model

        Args:
            values: Raw dictionary of values

        Returns:
            Dict[str, Any]: Validated values
        """
        model_fields = cls.model_fields.keys()
        unknown_fields = set(values.keys()) - set(model_fields)

        if unknown_fields:
            logger.warning("Found fields in JSON not defined in Product model: " f"{', '.join(unknown_fields)}")

            # Log the values of unknown fields for analysis
            for field in unknown_fields:
                logger.warning(f"Unknown field '{field}' has value: {values[field]}")

        return values

    @field_validator("discount", mode="before")  # type: ignore
    def parse_discount(cls, v: Any) -> float | None:
        """
        Parse discount from percentage string to float

        Args:
            v: Discount value (can be string like '-30%' or float)

        Returns:
            Optional[float]: Parsed discount as decimal (e.g., -30% -> 0.3)
        """
        if v is None:
            return None

        if isinstance(v, int | float):
            return abs(float(v))

        if isinstance(v, str):
            try:
                # Remove % sign and any spaces
                clean_value = v.replace("%", "").strip()
                # Convert to float and take absolute value
                # -30% or 30% both become 0.3
                return abs(float(clean_value)) / 100
            except ValueError:
                logger.warning(f"Could not parse discount value: {v}")
                return None

        return None

    @field_validator("product_details", mode="before")  # type: ignore
    def validate_product_details(cls, v: Any) -> list[dict[str, Any]]:
        """
        Validate product details and ensure no None values

        Args:
            v: Product details list

        Returns:
            List[Dict[str, Any]]: Validated product details
        """
        if not v:
            return []

        # Filter out details with None values
        return [detail for detail in v if detail.get("value") is not None]

    class Config:
        """Pydantic model configuration"""

        arbitrary_types_allowed = True
        validate_assignment = True


class ProductResponse(BaseModel):
    """Response containing list of products"""

    products: list[Product]


async def get_snapshot_data(snapshot_id: str) -> list[dict[str, Any]] | None:
    """
    Retrieve snapshot data from Bright Data API

    Args:
        snapshot_id: ID of the snapshot to retrieve
        token: Bright Data API token

    Returns:
        List of product data dictionaries or None if failed
    """
    token = os.getenv("BRIGHT_DATA_TOKEN")
    if not token:
        raise ValueError("BRIGHT_DATA_TOKEN not found in environment")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    snapshot_url = "https://api.brightdata.com/datasets/v3/snapshot" f"/{snapshot_id}?format=json"

    async with httpx.AsyncClient() as client:
        try:
            snapshot_response = await client.get(snapshot_url, headers=headers)
            snapshot_response.raise_for_status()

            raw_data: list[dict[str, Any]] = snapshot_response.json()
            if raw_data and len(raw_data) > 0:
                return raw_data
            return None

        except Exception as e:
            logger.error(f"Failed to get snapshot data: {str(e)}")
            return None


async def scrape_amazon_product(urls: list[str]) -> ProductResponse | None:
    """
    Scrape Amazon product data using Bright Data API

    Args:
        urls: List of Amazon product URLs to scrape

    Returns:
        ProductResponse object containing scraped data or None if failed
    """
    try:
        token = os.getenv("BRIGHT_DATA_TOKEN")
        if not token:
            raise ValueError("BRIGHT_DATA_TOKEN not found in environment")

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        trigger_url = "https://api.brightdata.com/datasets/v3/trigger" f"?dataset_id={DATASET_ID}&include_errors=true"

        url_list = [{"url": url} for url in urls]

        async with httpx.AsyncClient() as client:
            trigger_response = await client.post(trigger_url, headers=headers, json=url_list)
            trigger_response.raise_for_status()

            snapshot_id = trigger_response.json()["snapshot_id"]
            logger.info(f"Triggered scraping with snapshot ID: {snapshot_id}")

            # Wait for scraping to complete
            wait_time = 0
            while wait_time < MAX_WAIT_TIME:
                status = await get_snapshot_status(snapshot_id)

                if not status:
                    raise ValueError("Failed to get snapshot status")

                if status.status == "ready":
                    duration_str = f" in {status.collection_duration/1000:.1f} seconds" if status.collection_duration else ""
                    records_str = f" with {status.records} records" if status.records is not None else ""
                    logger.info(f"Scraping completed{records_str}{duration_str}")
                    break

                if status.status == "error":
                    raise ValueError("Scraping failed with errors")

                logger.info(f"Scraping in progress... " f"(waited {wait_time} seconds)")
                await asyncio.sleep(POLL_INTERVAL)
                wait_time += POLL_INTERVAL
            else:
                raise TimeoutError("Scraping timed out")

            # Get snapshot data
            raw_data = await get_snapshot_data(snapshot_id)
            if raw_data:
                return ProductResponse(products=raw_data)

            return None

    except Exception as e:
        logger.error(f"Error occurred: {str(e)}")
        return None


if __name__ == "__main__":
    load_dotenv()
    # resp = asyncio.run(get_snapshot_data('s_m61bwhkj1sallaiyw'))
    # print(resp)
    urls = [
        "https://www.amazon.com/AI-Engineering-Building-Applications-Foundation/dp/1098166302/",
    ]
    logger.info(f"Starting scraping for {len(urls)} products")
    response = asyncio.run(scrape_amazon_product(urls))
    if response and response.products:
        for idx, product in enumerate(response.products, 1):
            logger.info(f"Product {idx}: {product.title} - " f"${product.final_price}")
    else:
        logger.error("No products were scraped")
