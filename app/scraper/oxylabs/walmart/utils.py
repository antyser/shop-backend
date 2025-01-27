"""Utility functions for Walmart product data"""

from app.scraper.models import ProductSource, UnifiedProductContent
from app.scraper.oxylabs.walmart.models import WalmartProductContent


def get_brand_from_specs(product: WalmartProductContent) -> str | None:
    """Extract brand from specifications"""
    if product.specifications:
        for spec in product.specifications:
            if spec.key == "Brand":
                return spec.value
    return None


def convert_to_unified_product(product: WalmartProductContent) -> UnifiedProductContent:
    """
    Convert Walmart product content to unified format

    Args:
        product: Walmart product content

    Returns:
        UnifiedProductContent with standardized fields
    """
    # Get title with fallback to "Unknown Product"
    title = product.get_title()  # This now always returns a string

    return UnifiedProductContent(
        title=title,
        price=product.price.price if product.price else 0.0,
        currency=product.price.currency if product.price else "USD",
        rating=product.rating.rating if product.rating else 0.0,
        reviews_count=product.rating.count if product.rating else 0,
        description=product.description or "",
        brand=product.brand or "Unknown Brand",
        seller=product.seller.name if product.seller else "Walmart",
        in_stock=product.fulfillment.shipping if product.fulfillment and product.fulfillment.shipping else False,
        shipping_available=True,  # Walmart always has shipping available
        source=ProductSource.WALMART,
        raw_data=product.model_dump(),
    )
