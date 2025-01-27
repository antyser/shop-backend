import json
from pathlib import Path

import pytest
from loguru import logger

from app.scraper.oxylabs.walmart.models import OxyWalmartResponse, WalmartProductContent


def get_test_files():
    """Get all test response files"""
    json_dir = Path("app/tests/data/walmart")
    if not json_dir.exists():
        pytest.skip("Sample response directory not found. Run product_scraper.py first.")

    files = sorted(json_dir.glob("product_response_*.json"))
    if not files:
        pytest.skip("No sample response files found. Run product_scraper.py first.")

    return files


@pytest.mark.parametrize("json_path", get_test_files())
def test_parse_walmart_response(json_path):
    """Test parsing Walmart product response JSONs into Pydantic models"""
    try:
        with open(json_path) as f:
            data = json.load(f)

        response = OxyWalmartResponse(**data)

        # Basic validation
        assert response.results
        product = response.results[0].content

        # Validate required fields
        assert product.price is not None
        if product.price.price is not None:
            assert isinstance(product.price.price, float)

        if product.rating:
            assert isinstance(product.rating.rating, float)
            assert isinstance(product.rating.count, int)

        if product.seller:
            assert product.seller.name or product.seller.official_name

        if product.fulfillment:
            assert isinstance(product.fulfillment.shipping, bool)
            assert isinstance(product.fulfillment.delivery, bool)
            assert isinstance(product.fulfillment.pickup, bool)

        # Log successful validation
        logger.info(f"Successfully validated response from {json_path.name}")
        logger.info(f"Price: ${product.price.price}")
        if product.rating:
            logger.info(f"Rating: {product.rating.rating}/5 ({product.rating.count} reviews)")
        if product.seller:
            logger.info(f"Seller: {product.seller.name}")

    except Exception as e:
        logger.error(f"Validation failed for {json_path.name}: {str(e)}")
        raise


def create_test_product(title: str | None = None) -> WalmartProductContent:
    """Create a test product with minimal required fields"""
    return WalmartProductContent(
        url="https://www.walmart.com/ip/123456",
        product_id="123456",
        title=title,
        description="Test Description",
        brand="Test Brand",
        specifications=[],
        price=None,
        rating=None,
        fulfillment=None,
        seller=None,
    )


@pytest.mark.parametrize(
    "title,expected",
    [
        ("Test Title", "Test Title"),
        (None, "Unknown Product"),
    ],
)
def test_get_title(title: str | None, expected: str) -> None:
    """Test getting product title"""
    product = create_test_product(title)
    assert product.get_title() == expected
