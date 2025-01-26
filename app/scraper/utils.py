import re
from urllib.parse import unquote, urlparse


def is_amazon_url(url: str) -> bool:
    """
    Check if URL is a valid Amazon product URL

    Args:
        url: URL to check

    Returns:
        bool: True if valid Amazon product URL
    """
    try:
        # Parse URL
        parsed = urlparse(url)

        # Check domain - make sure it's exactly amazon.com
        if parsed.netloc != "www.amazon.com":
            return False

        # Check path pattern for product URLs
        path = parsed.path
        is_dp = bool(re.search(r"/dp/[A-Z0-9]{10}", path))
        is_gp = bool(re.search(r"/gp/product/[A-Z0-9]{10}", path))

        return is_dp or is_gp

    except Exception:
        return False


def extract_asin_and_slug(url: str) -> tuple[str, str | None]:
    """
    Extract ASIN and product name slug from Amazon URL

    Args:
        url: Amazon product URL

    Returns:
        Tuple of (asin, slug)
    """
    # Clean and parse URL
    cleaned_url = unquote(url).strip()
    path = urlparse(cleaned_url).path

    # Extract ASIN using regex
    asin_match = re.search(r"/dp/([A-Z0-9]{10})", path)
    if not asin_match:
        asin_match = re.search(r"/gp/product/([A-Z0-9]{10})", path)

    if not asin_match:
        raise ValueError("Could not extract ASIN from URL")

    asin = asin_match.group(1)

    slug = None
    if "/dp/" in path:
        parts = path.split("/dp/")[0]
        if parts and parts != "/":
            slug = parts.lstrip("/").replace("-", " ").strip().title()

    return asin, slug
