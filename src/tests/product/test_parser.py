# type: ignore
import json
from datetime import datetime
from pathlib import Path

from product.parser import parse_amazon_product
from scraper.bright_data.amazon import Product as AmazonProduct


def test_parse_amazon_product():
    """Test parsing Amazon product data to Product model"""

    # Load test data
    test_data_path = Path("tests/product/data/amazon_product.json")
    with open(test_data_path) as f:
        raw_data = json.load(f)

    # Create AmazonProduct instance
    amazon_product = AmazonProduct(**raw_data[0])

    # Parse to Product model
    product = parse_amazon_product(amazon_product)

    # Assert basic product information
    assert product.title == (
        "BAOMING G9 LED Bulb Dimmable 4W, 40 Watt T4 G9 Halogen "
        "Equivalent, 2700K Soft Warm White, 120V No-Flicker, "
        "Chandelier Lighting 450LM (5 Pack)"
    )
    assert product.brand == "BAOMING"
    assert product.seller_name == "BAOMING LED BULB"

    # Assert description (using startswith since it's a long text)
    assert product.description.startswith("G9 LED Bulb Dimmable Application Scenario")

    # Assert input data
    assert product.identifiers.asin == "B089M1BH1K"

    # Assert timestamps are present
    assert isinstance(product.created_at, datetime)
    assert isinstance(product.updated_at, datetime)
