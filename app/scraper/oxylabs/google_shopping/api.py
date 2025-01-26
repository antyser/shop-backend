import httpx
from dotenv import load_dotenv
from loguru import logger

from app.config import get_settings
from app.scraper.oxylabs.google_shopping.models import (
    GoogleProductOffersResponse,
    GoogleProductResponse,
    GoogleProductReviewsResponse,
    GoogleProductSpecsResponse,
    GoogleShoppingResponse,
)


def search_google_shopping(
    query: str,
    location: str = "United States",
    gl: str = "us",
    hl: str = "en",
    page: int = 1,
    shoprs: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    condition: str | None = None,
) -> GoogleShoppingResponse:
    """
    Search Google Shopping using SearchAPI.io's new layout
    Documentation Reference:
        https://www.searchapi.io/docs/google-shopping-new

    Args:
        query (str): Search query term
        location (str, optional): Location for search results. Defaults to "United States".
        gl (str, optional): Google location parameter. Defaults to "us".
        hl (str, optional): Interface language. Defaults to "en".
        page (int, optional): Results page number. Defaults to 1.
        shoprs (str, optional): Encoded filter values for strict filtering
        price_min (float, optional): Minimum price filter
        price_max (float, optional): Maximum price filter
        condition (str, optional): Product condition filter ('new' or 'used')

    Returns:
        GoogleShoppingResponse: Validated response containing shopping results
    """
    settings = get_settings()
    api_key = settings.SEARCHAPI_API_KEY
    if not api_key:
        raise ValueError("SEARCHAPI_API_KEY not found in settings")

    url = "https://www.searchapi.io/api/v1/search"

    params: dict[str, str | int | float] = {
        "engine": "google_shopping",
        "q": query,
        "location": location,
        "gl": gl,
        "hl": hl,
        "page": page,
        "api_key": api_key,
    }

    if shoprs:
        params["shoprs"] = shoprs
    if price_min:
        params["price_min"] = price_min
    if price_max:
        params["price_max"] = price_max
    if condition:
        params["condition"] = condition

    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        return GoogleShoppingResponse(**response.json())
    except httpx.RequestError as e:
        raise Exception(f"Error searching Google Shopping: {str(e)}") from e


def get_google_product(product_id: str, location: str = "United States", gl: str = "us", hl: str = "en") -> GoogleProductResponse:
    """
    Get detailed product information using SearchAPI.io's Google Product API
    Documentation Reference:
        https://www.searchapi.io/docs/google-product

    API Documentation:
    - Base endpoint: https://www.searchapi.io/api/v1/search?engine=google_product
    - Returns comprehensive product details including:
        * Basic product info (title, description, images)
        * Reviews and ratings
        * Product variations and configurations
        * Offers from different merchants
        * Specifications
        * Related products
        * Typical price ranges

    Args:
        product_id (str): Google Shopping product ID
        location (str, optional): Location for search results. Defaults to "United States".
        gl (str, optional): Google location parameter. Defaults to "us".
        hl (str, optional): Interface language. Defaults to "en".

    Returns:
        GoogleProductResponse: Validated Pydantic model containing complete product details
    """
    settings = get_settings()
    api_key = settings.SEARCHAPI_API_KEY
    if not api_key:
        raise ValueError("SEARCHAPI_API_KEY not found in settings")

    url = "https://www.searchapi.io/api/v1/search"

    params: dict[str, str | int | float] = {
        "engine": "google_product",
        "product_id": product_id,
        "location": location,
        "gl": gl,
        "hl": hl,
        "api_key": api_key,
    }

    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        return GoogleProductResponse(**response.json())
    except httpx.RequestError as e:
        raise Exception(f"Error fetching product details: {str(e)}") from e


def get_product_specifications(
    product_id: str,
    location: str = "United States",
    gl: str = "us",
    hl: str = "en",
    prds: str | None = None,
) -> GoogleProductSpecsResponse:
    """
    Get product specifications using SearchAPI.io's Google Product Specifications API
    Documentation Reference:
        https://www.searchapi.io/docs/google-product-specifications

    Args:
        product_id (str): Google Shopping product ID
        location (str, optional): Location for search results. Defaults to "United States".
        gl (str, optional): Google location parameter. Defaults to "us".
        hl (str, optional): Interface language. Defaults to "en".
        prds (str, optional): Custom product filter parameter

    Returns:
        GoogleProductSpecsResponse: Validated response containing product specifications
    """
    settings = get_settings()
    api_key = settings.SEARCHAPI_API_KEY
    if not api_key:
        raise ValueError("SEARCHAPI_API_KEY not found in settings")

    url = "https://www.searchapi.io/api/v1/search"

    params: dict[str, str | int | float] = {
        "engine": "google_product_specs",
        "product_id": product_id,
        "location": location,
        "gl": gl,
        "hl": hl,
        "api_key": api_key,
    }

    if prds:
        params["prds"] = prds

    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        return GoogleProductSpecsResponse(**response.json())
    except httpx.RequestError as e:
        raise Exception(f"Error fetching product specifications: {str(e)}") from e


def get_product_offers(
    product_id: str,
    location: str = "United States",
    gl: str = "us",
    hl: str = "en",
    page: int = 1,
    sort_by: str | None = None,
    durability: str | None = None,
    filters: list[str] | None = None,
    prds: str | None = None,
) -> GoogleProductOffersResponse:
    """
    Get product offers using SearchAPI.io's Google Product Offers API
    Documentation Reference:
        https://www.searchapi.io/docs/google-product-offers

    Args:
        product_id (str): Google Shopping product ID
        location (str, optional): Location for search results. Defaults to "United States".
        gl (str, optional): Google location parameter. Defaults to "us".
        hl (str, optional): Interface language. Defaults to "en".
        page (int, optional): Results page number. Defaults to 1.
        sort_by (str, optional): Sort order ('base_price', 'total_price', etc.)
        durability (str, optional): Product condition filter ('new' or 'used')
        filters (List[str], optional): List of filters ('free_delivery', 'nearby', etc.)
        prds (str, optional): Custom product filter parameter

    Returns:
        GoogleProductOffersResponse: Validated response containing product offers
    """
    settings = get_settings()
    api_key = settings.SEARCHAPI_API_KEY
    if not api_key:
        raise ValueError("SEARCHAPI_API_KEY not found in settings")

    url = "https://www.searchapi.io/api/v1/search"

    params: dict[str, str | int | float] = {
        "engine": "google_product_offers",
        "product_id": product_id,
        "location": location,
        "gl": gl,
        "hl": hl,
        "page": page,
        "api_key": api_key,
    }

    if sort_by and not prds:
        params["sort_by"] = sort_by
    if durability and not prds:
        params["durability"] = durability
    if filters and not prds:
        params["filters"] = ",".join(filters)
    if prds:
        params["prds"] = prds

    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        return GoogleProductOffersResponse(**response.json())
    except httpx.RequestError as e:
        raise Exception(f"Error fetching product offers: {str(e)}") from e


def get_product_reviews(
    product_id: str,
    location: str = "United States",
    gl: str = "us",
    hl: str = "en",
    rating: int | None = None,
    num: int = 10,
    next_page_token: str | None = None,
) -> GoogleProductReviewsResponse:
    """
    Get product reviews using SearchAPI.io

    Args:
        product_id (str): Google Shopping product ID
        location (str, optional): Location for search results. Defaults to "United States".
        gl (str, optional): Google location parameter. Defaults to "us".
        hl (str, optional): Interface language. Defaults to "en".
        rating (int, optional): Filter by rating (1-5)
        num (int, optional): Number of reviews per page (1-100). Defaults to 10.
        next_page_token (str, optional): Token for pagination

    Returns:
        GoogleProductReviewsResponse: Product reviews data
    """
    settings = get_settings()
    api_key = settings.SEARCHAPI_API_KEY
    if not api_key:
        raise ValueError("SEARCHAPI_API_KEY not found in settings")

    url = "https://www.searchapi.io/api/v1/search"

    params: dict[str, str | int | float] = {
        "engine": "google_product_reviews",
        "product_id": product_id,
        "location": location,
        "gl": gl,
        "hl": hl,
        "num": num,
        "api_key": api_key,
    }

    if rating:
        params["rating"] = rating
    if next_page_token:
        params["next_page_token"] = next_page_token

    try:
        response = httpx.get(url, params=params)
        response.raise_for_status()
        return GoogleProductReviewsResponse(**response.json())
    except httpx.RequestError as e:
        raise Exception(f"Error fetching product reviews: {str(e)}") from e


# Example usage
if __name__ == "__main__":
    load_dotenv()
    try:
        # Example product ID and search query
        product_id = "16127099509847096080"  # AirPods Pro 2nd Gen
        search_query = "airpods pro 2nd generation"

        # 1. Test Google Shopping Search
        logger.info("\n=== Testing Google Shopping Search ===")
        search_results = search_google_shopping(query=search_query, price_min=200, price_max=300)
        logger.info(f"Found {len(search_results.shopping_results or [])} products")

        # Safely display first 3 results
        for result in (search_results.shopping_results or [])[:3]:
            logger.info(f"- {result.title or 'No title'}")
            logger.info(f"  Price: {result.price or 'N/A'}")
            # Safely access merchant name
            merchant_name = result.merchant.get("name", "Unknown Merchant") if result.merchant else "Unknown Merchant"
            logger.info(f"  Merchant: {merchant_name}")

        logger.info("\n=== Testing Complete Product Details ===")
        product_details = get_google_product(product_id)

        logger.info("Basic Information:")
        if product_details.product:
            logger.info(f"- Title: {product_details.product.title}")
            if product_details.product.rating is not None and product_details.product.reviews is not None:
                logger.info(f"- Rating: {product_details.product.rating} " f"({product_details.product.reviews} reviews)")

        if product_details.typical_prices:
            logger.info(f"- Price Range: {product_details.typical_prices.low_price} - " f"{product_details.typical_prices.high_price}")

        if product_details.product and product_details.product.variations and product_details.product.variations.options:
            logger.info("\nAvailable Variations:")
            for var in product_details.product.variations.options:
                logger.info(f"- {var.title}")

        if product_details.product and product_details.product.highlights:
            logger.info("\nHighlights:")
            for highlight in product_details.product.highlights:
                logger.info(f"- {highlight}")

        if product_details.related_products:
            logger.info("\nRelated Products:")
            for related in product_details.related_products[:3]:
                logger.info(f"- {related.title}")
                logger.info(f"  Price: {related.price}")
                if related.rating:
                    logger.info(f"  Rating: {related.rating}★ ({related.reviews} reviews)")

    except Exception as e:
        logger.exception(f"Error: {e}")
