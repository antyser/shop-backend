import re
from urllib.parse import unquote, urlparse, urlunparse


def is_amazon_url(url: str) -> bool:
    """
    Check if URL is from Amazon product page

    Args:
        url: URL string to check

    Returns:
        bool: True if URL is from Amazon product page
    """
    try:
        # Parse the URL
        parsed = urlparse(url)

        # Check domain is amazon
        if not re.match(r"^(?:www\.)?amazon\.(?:com|co\.uk|ca|de|fr|co\.jp|in|it|es|nl)$", parsed.netloc.lower()):
            return False

        # Check path patterns for product pages
        path = parsed.path.rstrip("/")
        valid_patterns = [
            r"/dp/[A-Za-z0-9]{10}",  # Standard product URL
            r"/gp/product/[A-Za-z0-9]{10}",  # Alternative product URL
            r"/gp/aw/d/[A-Za-z0-9]{10}",  # Mobile URLs
            r"/[^/]+/dp/[A-Za-z0-9]{10}",  # Category URLs
        ]

        return any(re.search(pattern, path, re.IGNORECASE) for pattern in valid_patterns)

    except Exception:
        return False


def is_walmart_url(url: str) -> bool:
    """
    Check if URL is a valid Walmart product URL

    Args:
        url: URL to check

    Returns:
        bool: True if valid Walmart product URL
    """
    try:
        parsed = urlparse(url)
        # Check domain
        if not re.match(r"^(?:www\.)?walmart\.com$", parsed.netloc):
            return False
        # Check path pattern for product URLs
        return bool(re.search(r"/ip/(?:[^/]+/)?(?:\d+)(?:/|\?|$)", parsed.path))
    except Exception:
        return False


def extract_asin_and_slug(url: str) -> tuple[str, str | None]:
    """
    Extract ASIN and product name slug from Amazon URL

    Args:
        url: Amazon product URL

    Returns:
        Tuple of (asin, slug)

    Raises:
        ValueError: If ASIN cannot be extracted
    """
    # Clean and parse URL
    cleaned_url = unquote(url).strip()
    path = urlparse(cleaned_url).path

    # Extract ASIN from URL patterns like:
    # /dp/ASIN
    # /gp/product/ASIN
    # /*/ASIN/
    asin_match = re.search(r"/(?:dp|gp/product|[^/]+)/([A-Z0-9]{10})(?:/|\?|$)", path)
    if not asin_match:
        raise ValueError("Could not extract ASIN from URL")

    # Try to extract product name/slug from URL
    # Look for text before /dp/ or /gp/product/
    if "/dp/" in path:
        parts = path.split("/dp/")[0].split("/")
        if len(parts) > 1:
            slug = parts[-1]
            return asin_match.group(1), slug
    elif "/gp/product/" in path:
        parts = path.split("/gp/product/")[0].split("/")
        if len(parts) > 1:
            slug = parts[-1]
            return asin_match.group(1), slug

    return asin_match.group(1), None


def extract_walmart_id_and_slug(url: str) -> tuple[str, str | None]:
    """
    Extract product ID and slug from Walmart URL

    Args:
        url: Walmart product URL

    Returns:
        Tuple of (product_id, slug)

    Raises:
        ValueError: If product ID cannot be extracted
    """
    # Extract product ID from URL patterns like:
    # /ip/SLUG/PRODUCT_ID
    # /ip/PRODUCT_ID
    product_id_match = re.search(r"/ip/(?:[^/]+/)?(\d+)(?:/|\?|$)", url)
    if not product_id_match:
        raise ValueError("Could not extract product ID from Walmart URL")

    # Try to extract product name/slug from URL
    slug_match = re.search(r"/ip/([^/]+)/\d+(?:/|\?|$)", url)
    slug = slug_match.group(1) if slug_match else None

    return product_id_match.group(1), slug


def normalize_url(url: str) -> str:
    """
    Normalize URL by removing query parameters and fragments.

    Args:
        url: URL string to normalize

    Returns:
        Normalized URL string without query parameters and fragments
    """
    if not url:
        return ""

    parsed = urlparse(url)
    # Reconstruct URL without query parameters and fragments
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))  # params  # query  # fragment

    # Remove trailing slash if present
    return clean_url.rstrip("/")
