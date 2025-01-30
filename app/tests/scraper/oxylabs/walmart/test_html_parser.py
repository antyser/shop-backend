"""Tests for Walmart HTML parser"""

import pytest
from bs4 import BeautifulSoup

from app.scraper.oxylabs.walmart.html_parser import (
    extract_breadcrumbs,
    extract_fulfillment,
    extract_location,
    extract_price,
    extract_rating,
    extract_seller,
    extract_specifications,
    parse_walmart_html,
)
from app.scraper.oxylabs.walmart.models import (
    Breadcrumb,
    Fulfillment,
    Location,
    Price,
    Rating,
    Seller,
    Specification,
    WalmartProductContent,
)


@pytest.fixture
def sample_html() -> str:
    """Load sample HTML from test data"""
    from pathlib import Path

    html_path = Path("tests/data/walmart/product.html")
    return html_path.read_text(encoding="utf-8")


@pytest.fixture
def soup(sample_html: str) -> BeautifulSoup:
    """Create BeautifulSoup object from sample HTML"""
    return BeautifulSoup(sample_html, "html.parser")


def test_extract_price(soup: BeautifulSoup) -> None:
    """Test extracting price information"""
    price = extract_price(soup)
    assert isinstance(price, Price)
    assert price.price is not None
    assert price.currency == "USD"


def test_extract_rating(soup: BeautifulSoup) -> None:
    """Test extracting rating information"""
    rating = extract_rating(soup)
    assert isinstance(rating, Rating)
    assert rating.rating is not None
    assert rating.count is not None


def test_extract_seller(soup: BeautifulSoup) -> None:
    """Test extracting seller information"""
    seller = extract_seller(soup)
    assert isinstance(seller, Seller)
    assert seller.name is not None
    assert seller.id is not None


def test_extract_location(soup: BeautifulSoup) -> None:
    """Test extracting location information"""
    location = extract_location(soup)
    assert isinstance(location, Location)
    assert location.city is not None
    assert location.state is not None
    assert location.store_id is not None
    assert location.zip_code is not None


def test_extract_breadcrumbs(soup: BeautifulSoup) -> None:
    """Test extracting breadcrumb information"""
    breadcrumbs = extract_breadcrumbs(soup)
    assert isinstance(breadcrumbs, list)
    assert len(breadcrumbs) > 0
    for breadcrumb in breadcrumbs:
        assert isinstance(breadcrumb, Breadcrumb)
        assert breadcrumb.url is not None
        assert breadcrumb.category_name is not None


def test_extract_fulfillment(soup: BeautifulSoup) -> None:
    """Test extracting fulfillment information"""
    fulfillment = extract_fulfillment(soup)
    assert isinstance(fulfillment, Fulfillment)
    assert fulfillment.pickup is not None
    assert fulfillment.delivery is not None
    assert fulfillment.shipping is not None
    assert fulfillment.out_of_stock is not None


def test_extract_specifications(soup: BeautifulSoup) -> None:
    """Test extracting product specifications"""
    specs = extract_specifications(soup)
    assert isinstance(specs, list)
    assert len(specs) > 0
    for spec in specs:
        assert isinstance(spec, Specification)
        assert spec.key is not None
        assert spec.value is not None


def test_parse_walmart_html(sample_html: str) -> None:
    """Test parsing complete Walmart product HTML"""
    product = parse_walmart_html(sample_html)
    assert isinstance(product, WalmartProductContent)
    assert product.price is not None
    assert product.rating is not None
    assert product.seller is not None
    assert product.location is not None
    assert product.breadcrumbs is not None
    assert product.fulfillment is not None
    assert product.specifications is not None
