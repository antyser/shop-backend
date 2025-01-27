"""Tests for scraper service"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from app.scraper.models import ProductSource
from app.scraper.oxylabs.amazon.models import OxyAmazonProductResponse
from app.scraper.oxylabs.walmart.models import OxyWalmartResponse
from app.scraper.searchapi.google_search import GoogleSearchResponse
from app.scraper.service import (
    extract_walmart_id_and_slug,
    is_amazon_url,
    is_walmart_url,
    scrape_product,
)


def load_test_response(filename: str) -> dict[str, Any]:
    """Load test response from JSON file"""
    json_path = Path("app/tests/data") / filename
    if not json_path.exists():
        pytest.skip(f"Test response file not found: {filename}")

    with open(json_path) as f:
        return json.load(f)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.amazon.com/dp/B07SH6HN2X", True),
        ("https://amazon.co.uk/dp/B07SH6HN2X", True),
        ("https://www.walmart.com/ip/123456", False),
        ("https://example.com", False),
    ],
)
def test_is_amazon_url(url: str, expected: bool):
    """Test Amazon URL detection"""
    assert is_amazon_url(url) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.walmart.com/ip/123456", True),
        ("https://walmart.com/ip/123456", True),
        ("https://www.amazon.com/dp/B07SH6HN2X", False),
        ("https://example.com", False),
    ],
)
def test_is_walmart_url(url: str, expected: bool):
    """Test Walmart URL detection"""
    assert is_walmart_url(url) == expected


@pytest.mark.parametrize(
    "url,expected_id,expected_slug",
    [
        (
            "https://www.walmart.com/ip/Orgain-Organic-Plant-Based-Protein-Powder-Sweet-Vanilla-Bean/553332207",
            "553332207",
            "Orgain-Organic-Plant-Based-Protein-Powder-Sweet-Vanilla-Bean",
        ),
        (
            "https://www.walmart.com/ip/123456",
            "123456",
            None,
        ),
        (
            "https://www.walmart.com/ip/Product-Name/123456?param=value",
            "123456",
            "Product-Name",
        ),
    ],
)
def test_extract_walmart_id_and_slug(url: str, expected_id: str, expected_slug: str | None):
    """Test extracting product ID and slug from Walmart URLs"""
    product_id, slug = extract_walmart_id_and_slug(url)
    assert product_id == expected_id
    assert slug == expected_slug


def test_extract_walmart_id_and_slug_invalid():
    """Test extracting product ID from invalid Walmart URL"""
    with pytest.raises(ValueError, match="Could not extract product ID from Walmart URL"):
        extract_walmart_id_and_slug("https://www.walmart.com/category/123")


@pytest.mark.asyncio
@patch("app.scraper.service.search_google")
@patch("app.scraper.service.fetch_amazon_product")
async def test_scrape_amazon_product(mock_fetch: Any, mock_search: Any) -> None:
    """Test scraping Amazon product"""
    # Load mock data
    mock_data = load_test_response("amazon/product_response_1.json")
    mock_fetch.return_value = OxyAmazonProductResponse(**mock_data)
    mock_search.return_value = GoogleSearchResponse(items=[])

    url = "https://www.amazon.com/Insta360-Standard-Bundle-Waterproof-Stabilization/dp/B0DBQBMQH2"
    response = await scrape_product(url)

    assert str(response.url) == url  # Convert HttpUrl to string for comparison
    assert response.product.source == ProductSource.AMAZON
    assert response.product.title
    assert response.product.price > 0
    assert response.product.currency
    assert isinstance(response.search_results, GoogleSearchResponse)

    # Verify mock was called correctly
    mock_fetch.assert_called_once()
    mock_search.assert_called_once()


@pytest.mark.asyncio
@patch("app.scraper.service.search_google")
@patch("app.scraper.service.fetch_walmart_product")
async def test_scrape_walmart_product(mock_fetch: Any, mock_search: Any) -> None:
    """Test scraping Walmart product"""
    # Load mock data
    mock_data = load_test_response("walmart/product_response_1.json")
    mock_fetch.return_value = OxyWalmartResponse(**mock_data)
    mock_search.return_value = GoogleSearchResponse(items=[])

    url = "https://www.walmart.com/ip/Orgain-Organic-Plant-Based-Protein-Powder-Sweet-Vanilla-Bean/553332207"
    response = await scrape_product(url)

    assert str(response.url) == url  # Convert HttpUrl to string for comparison
    assert response.product.source == ProductSource.WALMART
    assert response.product.title
    assert response.product.price > 0
    assert response.product.currency
    assert isinstance(response.search_results, GoogleSearchResponse)

    # Verify mock was called correctly
    mock_fetch.assert_called_once()
    mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_scrape_invalid_url() -> None:
    """Test scraping invalid URL"""
    with pytest.raises(ValueError, match="Only Amazon and Walmart URLs are supported"):
        await scrape_product("https://example.com/product/123")
