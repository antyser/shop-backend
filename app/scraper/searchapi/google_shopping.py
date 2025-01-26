import asyncio
from decimal import Decimal

import httpx
from loguru import logger
from pydantic import BaseModel, Field

from app.config import get_settings


class SearchMetadata(BaseModel):
    """Metadata about the search request"""

    id: str | None = None
    status: str | None = None
    created_at: str | None = None
    request_time_taken: float | None = None
    parsing_time_taken: float | None = None
    total_time_taken: float | None = None
    request_url: str | None = None
    html_url: str | None = None
    json_url: str | None = None


class SearchParameters(BaseModel):
    """Parameters used for the search"""

    engine: str | None = None
    q: str | None = None
    location: str | None = None
    location_used: str | None = None
    google_domain: str | None = None
    hl: str | None = None
    gl: str | None = None


class FilterOption(BaseModel):
    """Individual filter option"""

    text: str | None = None
    shoprs: str | None = None


class Filter(BaseModel):
    """Filter category with options"""

    type: str | None = None
    options: list[FilterOption] | None = []


class ShoppingAd(BaseModel):
    """Shopping advertisement item"""

    position: int | None = None
    block_position: str | None = None
    title: str | None = None
    seller: str | None = None
    link: str | None = None
    price: str | None = None
    extracted_price: Decimal | None = None
    rating: float | None = None
    reviews: int | None = None
    image: str | None = None


class ShoppingResult(BaseModel):
    """Shopping search result item"""

    position: int | None = None
    product_id: str | None = None
    title: str | None = None
    product_link: str | None = None
    seller: str | None = None
    offers: str | None = None
    extracted_offers: int | None = None
    offers_link: str | None = None
    price: str | None = None
    extracted_price: Decimal | None = None
    rating: float | None = None
    reviews: int | None = None
    delivery: str | None = None
    durability: str | None = None
    thumbnail: str | None = None
    prds: str | None = None


class GoogleShoppingResponse(BaseModel):
    """Complete response from Google Shopping API"""

    search_metadata: SearchMetadata | None = None
    search_parameters: SearchParameters | None = None
    filters: list[Filter] | None = []
    shopping_ads: list[ShoppingAd] | None = []
    shopping_results: list[ShoppingResult] | None = []

    class Config:
        extra = "ignore"


async def search_products(
    query: str, location: str = "California,United States", language: str = "en", country: str = "us"
) -> GoogleShoppingResponse:
    """
    Search for products using Google Shopping API

    Args:
        query: Search query string
        location: Search location string
        language: Language code
        country: Country code

    Returns:
        GoogleShoppingResponse object containing search results

    Raises:
        httpx.HTTPError: If the API request fails
    """
    settings = get_settings()
    api_key = settings.SEARCHAPI_API_KEY
    if not api_key:
        raise ValueError("SEARCHAPI_API_KEY not found in settings")

    url = "https://www.searchapi.io/api/v1/search"

    params = {"engine": "google_shopping", "q": query, "gl": country, "hl": language, "location": location, "api_key": api_key}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            return GoogleShoppingResponse.model_validate(response.json())  # type: ignore

        except httpx.HTTPError as e:
            logger.error(f"API request failed: {str(e)}")
            raise


class ReviewHistogram(BaseModel):
    """Review rating distribution"""

    one: int | None = Field(None, alias="1")
    two: int | None = Field(None, alias="2")
    three: int | None = Field(None, alias="3")
    four: int | None = Field(None, alias="4")
    five: int | None = Field(None, alias="5")


class ProductVariation(BaseModel):
    """Product variation details"""

    title: str | None = None
    image: str | None = None


class ProductVariations(BaseModel):
    """Product variations section"""

    current: ProductVariation | None = None
    options: list[ProductVariation] | None = []


class ConfigurationOption(BaseModel):
    """Product configuration option"""

    title: str | None = None
    link: str | None = None


class Configuration(BaseModel):
    """Product configuration section"""

    title: str | None = None
    options: list[ConfigurationOption] | None = []


class ProductDetails(BaseModel):
    """Detailed product information"""

    product_id: str | None = None
    title: str | None = None
    reviews: int | None = None
    rating: float | None = None
    reviews_histogram: ReviewHistogram | None = None
    highlights: list[str] | None = []
    description: str | None = None
    variations: ProductVariations | None = None
    configurations: list[Configuration] | None = []
    extensions: list[str] | None = []
    images: list[str] | None = []


class Merchant(BaseModel):
    """Merchant information"""

    name: str | None = None
    rating: float | None = None
    reviews: int | None = None
    link: str | None = None
    badge: str | None = None


class Offer(BaseModel):
    """Product offer details"""

    position: int | None = None
    link: str | None = None
    price: str | None = None
    extracted_price: Decimal | None = None
    delivery_price: str | None = None
    extracted_delivery_price: Decimal | None = None
    tax_price: str | None = None
    extracted_tax_price: Decimal | None = None
    total_price: str | None = None
    extracted_total_price: Decimal | None = None
    delivery_return: str | None = None
    merchant: Merchant | None = None
    tag: str | None = None
    original_price: str | None = None
    extracted_original_price: Decimal | None = None


class TypicalPrices(BaseModel):
    """Typical price ranges"""

    low_price: str | None = None
    extracted_low_price: Decimal | None = None
    high_price: str | None = None
    extracted_high_price: Decimal | None = None
    popular_choice: str | None = None
    popular_choice_link: str | None = None
    popular_choice_price: str | None = None
    extracted_popular_choice_price: Decimal | None = None


class Review(BaseModel):
    """Product review"""

    username: str | None = None
    source: str | None = None
    date: str | None = None
    rating: int | None = None
    text: str | None = None
    title: str | None = None


class ReviewFilter(BaseModel):
    """Review filter option"""

    title: str | None = None
    link: str | None = None
    description: str | None = None
    reviews: int | None = None


class ReviewResults(BaseModel):
    """Product review results"""

    reviews: list[Review] | None = []
    reviews_link: str | None = None
    filters: list[ReviewFilter] | None = []


class SpecAttribute(BaseModel):
    """Product specification attribute"""

    name: str | None = None
    value: str | None = None


class Specification(BaseModel):
    """Product specification category"""

    category: str | None = None
    attributes: list[SpecAttribute] | None = []


class GoogleProductResponse(BaseModel):
    """Complete response from Google Product API"""

    search_metadata: SearchMetadata | None = None
    search_parameters: SearchParameters | None = None
    product: ProductDetails | None = None
    offers: list[Offer] | None = []
    offers_link: str | None = None
    typical_prices: TypicalPrices | None = None
    review_results: ReviewResults | None = None
    specifications: list[Specification] | None = []
    specifications_link: str | None = None
    related_products: list[ShoppingResult] | None = []

    class Config:
        extra = "ignore"


async def get_product_details(product_id: str, prds: str | None = None, language: str = "en", country: str = "us") -> GoogleProductResponse:
    """
    Get detailed product information using Google Product API

    Args:
        product_id: Product ID to fetch details for
        prds: Optional prds parameter for product variations
        language: Language code
        country: Country code

    Returns:
        GoogleProductResponse object containing product details

    Raises:
        httpx.HTTPError: If the API request fails
        ValueError: If API key is not found
    """
    url = "https://www.searchapi.io/api/v1/search"

    settings = get_settings()
    api_key = settings.SEARCHAPI_API_KEY
    if not api_key:
        raise ValueError("SEARCHAPI_API_KEY not found in settings")

    params = {"engine": "google_product", "product_id": product_id, "gl": country, "hl": language, "api_key": api_key}

    if prds:
        params["prds"] = prds

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            return GoogleProductResponse.model_validate(response.json())  # type: ignore

        except httpx.HTTPError as e:
            logger.error(f"API request failed: {str(e)}")
            raise


async def search_product_details(
    query: str, location: str = "California,United States", language: str = "en", country: str = "us"
) -> GoogleProductResponse | None:
    """
    Search for products and get details of the first result

    Args:
        query: Search query string
        location: Search location string
        language: Language code
        country: Country code

    Returns:
        GoogleProductResponse object for first product or None if no results

    Raises:
        httpx.HTTPError: If the API request fails
        ValueError: If API key is not found
    """
    search_results = await search_products(query=query, location=location, language=language, country=country)

    if not search_results.shopping_results:
        logger.warning(f"No results found for query: {query}")
        return None

    first_result = search_results.shopping_results[0]
    if not first_result.product_id:
        logger.warning("First result has no product ID")
        return None

    return await get_product_details(product_id=first_result.product_id, prds=first_result.prds, language=language, country=country)


if __name__ == "__main__":
    try:
        product = asyncio.run(search_product_details("PS5 Digital Edition"))
        if product and product.product:
            logger.info(f"Found product: {product.product.title}")
            logger.info(f"Rating: {product.product.rating} " f"({product.product.reviews} reviews)")
            logger.debug(product.model_dump_json(indent=2))
        else:
            logger.warning("No product details found")
    except Exception as e:
        logger.error(f"Operation failed: {str(e)}")
