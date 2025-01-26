import pytest

from src.scraper.utils import extract_asin_and_slug, is_amazon_url


@pytest.mark.parametrize(
    "url,expected_asin,expected_slug",
    [
        (
            "https://www.amazon.com/Aquaphor-Advanced-Therapy-Ointment-Protectant/dp/B0107QP1VE",
            "B0107QP1VE",
            "Aquaphor Advanced Therapy Ointment Protectant",
        ),
        ("https://www.amazon.com/dp/B0107QP1VE", "B0107QP1VE", None),
        ("https://www.amazon.com/gp/product/B0107QP1VE", "B0107QP1VE", None),
    ],
)
def test_extract_asin_and_slug(url: str, expected_asin: str, expected_slug: str):
    """
    Test extracting ASIN and slug from various Amazon URL formats
    """
    asin, slug = extract_asin_and_slug(url)
    assert asin == expected_asin
    assert slug == expected_slug


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.amazon.com/Aquaphor-Advanced-Therapy-Ointment-Protectant/dp/B0107QP1VE", True),
        ("https://www.amazon.com/dp/B0107QP1VE", True),
        ("https://www.amazon.com/gp/product/B0107QP1VE", True),
        ("https://www.amazon.com/not-a-product", False),
        ("https://www.fake-amazon.com/dp/B0107QP1VE", False),
        ("not a url", False),
    ],
)
def test_is_amazon_url(url: str, expected: bool):
    """
    Test validation of Amazon product URLs
    """
    assert is_amazon_url(url) == expected


def test_extract_asin_and_slug_invalid_url():
    """
    Test that invalid URLs raise ValueError
    """
    with pytest.raises(ValueError, match="Could not extract ASIN from URL"):
        extract_asin_and_slug("https://www.amazon.com/not-a-product")
