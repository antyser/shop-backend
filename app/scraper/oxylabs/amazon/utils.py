"""Utility functions for Amazon product data"""

from app.scraper.models import ProductSource, UnifiedProductContent
from app.scraper.oxylabs.amazon.models import AmazonProductContent


def convert_to_unified_product(product: AmazonProductContent) -> UnifiedProductContent:
    """
    Convert Amazon product data to unified format

    Args:
        product: Amazon product content from Oxylabs API

    Returns:
        UnifiedProductContent: Product data in unified format
    """
    return UnifiedProductContent(
        title=product.title,
        price=product.price,
        currency=product.currency,
        rating=product.rating,
        reviews_count=product.reviews_count,
        description=product.description,
        brand=product.brand,
        seller=product.seller,
        in_stock=product.stock == "in_stock" if product.stock else True,
        shipping_available=True,  # Amazon always has shipping
        source=ProductSource.AMAZON,
        raw_data=product,
    )
