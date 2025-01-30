"""Tests for scraper utilities"""

import pytest

from app.scraper.utils import (
    extract_asin_and_slug,
    extract_walmart_id_and_slug,
    is_amazon_url,
    is_walmart_url,
    normalize_url,
)


@pytest.mark.parametrize(
    "url,expected_asin,expected_slug",
    [
        (
            "https://www.amazon.com/Aquaphor-Advanced-Therapy-Ointment-Protectant/dp/B0107QP1VE",
            "B0107QP1VE",
            "Aquaphor-Advanced-Therapy-Ointment-Protectant",
        ),
        ("https://www.amazon.com/dp/B0107QP1VE", "B0107QP1VE", None),
        ("https://www.amazon.com/gp/product/B0107QP1VE", "B0107QP1VE", None),
        (
            "https://amazon.co.uk/Some-Product-Name/dp/B0107QP1VE",
            "B0107QP1VE",
            "Some-Product-Name",
        ),
    ],
)
def test_extract_asin_and_slug(url: str, expected_asin: str, expected_slug: str | None) -> None:
    """Test extracting ASIN and slug from various Amazon URL formats"""
    asin, slug = extract_asin_and_slug(url)
    assert asin == expected_asin
    assert slug == expected_slug


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.amazon.com/Aquaphor-Advanced-Therapy-Ointment-Protectant/dp/B0107QP1VE", True),
        ("https://www.amazon.com/dp/B0107QP1VE", True),
        ("https://www.amazon.com/gp/product/B0107QP1VE", True),
        ("https://amazon.co.uk/dp/B0107QP1VE", True),
        ("https://www.amazon.com/not-a-product", False),
        ("https://www.fake-amazon.com/dp/B0107QP1VE", False),
        (
            "https://www.amazon.com/gp/aw/d/B08FWXPRFP/?_encoding=UTF8&pd_rd_plhdr=t&aaxitk=d2985da0d2bf385a04fe04d96f96bf5b&hsa_cr_id=0&qid=1737901978&sr=1-1-9e67e56a-6f64-441f-a281-df67fc737124&ref_=sbx_be_s_sparkle_lsi4d_asin_0_img&pd_rd_w=NKQgY&content-id=amzn1.sym.8591358d-1345-4efd-9d50-5bd4e69cd942%3Aamzn1.sym.8591358d-1345-4efd-9d50-5bd4e69cd942&pf_rd_p=8591358d-1345-4efd-9d50-5bd4e69cd942&pf_rd_r=T5K2MPMEN5D7RWH0GDQM&pd_rd_wg=yQjdN&pd_rd_r=91b2a848-21f8-4afa-bedb-3093bfba4a19&th=1:",
            True,
        ),
        ("not a url", False),
    ],
)
def test_is_amazon_url(url: str, expected: bool) -> None:
    """Test validation of Amazon product URLs"""
    assert is_amazon_url(url) == expected


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
        (
            "https://walmart.com/ip/Product-Name/123456",
            "123456",
            "Product-Name",
        ),
    ],
)
def test_extract_walmart_id_and_slug(url: str, expected_id: str, expected_slug: str | None) -> None:
    """Test extracting product ID and slug from Walmart URLs"""
    product_id, slug = extract_walmart_id_and_slug(url)
    assert product_id == expected_id
    assert slug == expected_slug


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.walmart.com/ip/123456", True),
        ("https://walmart.com/ip/123456", True),
        ("https://www.walmart.com/ip/Product-Name/123456", True),
        ("https://www.walmart.com/not-a-product", False),
        ("https://www.fake-walmart.com/ip/123456", False),
        ("not a url", False),
    ],
)
def test_is_walmart_url(url: str, expected: bool) -> None:
    """Test validation of Walmart product URLs"""
    assert is_walmart_url(url) == expected


def test_extract_asin_and_slug_invalid_url() -> None:
    """Test that invalid Amazon URLs raise ValueError"""
    with pytest.raises(ValueError, match="Could not extract ASIN from URL"):
        extract_asin_and_slug("https://www.amazon.com/not-a-product")


def test_extract_walmart_id_and_slug_invalid() -> None:
    """Test that invalid Walmart URLs raise ValueError"""
    with pytest.raises(ValueError, match="Could not extract product ID from Walmart URL"):
        extract_walmart_id_and_slug("https://www.walmart.com/category/123")


@pytest.mark.parametrize(
    "input_url,expected",
    [
        # Basic URLs
        ("https://example.com", "https://example.com"),
        ("https://example.com/", "https://example.com"),
        # URLs with paths
        ("https://example.com/path", "https://example.com/path"),
        ("https://example.com/path/", "https://example.com/path"),
        # URLs with query parameters
        ("https://example.com?param=value", "https://example.com"),
        ("https://example.com/?param=value", "https://example.com"),
        ("https://example.com/path?param=value", "https://example.com/path"),
        # URLs with fragments
        ("https://example.com#section", "https://example.com"),
        ("https://example.com/#section", "https://example.com"),
        # Complex URLs
        ("https://example.com/path?param=value#section", "https://example.com/path"),
        ("https://sub.example.com/path/?param=value&p2=v2#section", "https://sub.example.com/path"),
        # Edge cases
        ("", ""),
        ("https://example.com/path///", "https://example.com/path"),
    ],
)
def test_normalize_url(input_url: str, expected: str) -> None:
    """
    Test URL normalization with various input cases.

    Args:
        input_url: Test input URL
        expected: Expected normalized output
    """
    assert normalize_url(input_url) == expected
