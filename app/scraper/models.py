"""
Pydantic models for the scraper module
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, HttpUrl

from app.scraper.oxylabs.amazon.models import AmazonProductContent
from app.scraper.oxylabs.walmart.models import WalmartProductContent
from app.scraper.searchapi.google_search import GoogleSearchResponse


class ProductSource(str, Enum):
    """Supported product sources"""

    AMAZON = "amazon"
    WALMART = "walmart"


class ScrapeRequest(BaseModel):
    """Request model for scraping URLs"""

    urls: list[HttpUrl]


class ScrapeResponse(BaseModel):
    """Response model for scraped content"""

    results: dict[str, str]


class SearchResult(BaseModel):
    """Model for individual search result"""

    title: str | None = None
    link: HttpUrl | None = None
    snippet: str | None = None
    date: str | None = None
    source: str | None = None
    content: str | None = None


class ScrapeProductRequest(BaseModel):
    """Request model for scraping product information"""

    url: HttpUrl


class UnifiedProductContent(BaseModel):
    """Unified product content model that works for both Amazon and Walmart"""

    title: str
    price: float
    currency: str
    rating: float | None = None
    reviews_count: int | None = None
    description: str | None = None
    brand: str | None = None
    seller: str | None = None
    in_stock: bool = True
    shipping_available: bool = True
    source: ProductSource
    raw_data: AmazonProductContent | WalmartProductContent


class ScrapeProductResponse(BaseModel):
    """Response model for product information and reviews"""

    product: UnifiedProductContent
    url: HttpUrl
    search_results: GoogleSearchResponse


class ScrapeSearchRequest(BaseModel):
    """Request model for scraping search results"""

    query: str


class ScrapeSearchResponse(BaseModel):
    """Response model for search results"""

    results: GoogleSearchResponse


# Additional models for specific product types
class ProductReview(BaseModel):
    """Model for product review"""

    rating: float | None = None
    title: str | None = None
    content: str
    author: str | None = None
    date: datetime | None = None
    verified_purchase: bool = False
    helpful_votes: int | None = None


class ProductVariant(BaseModel):
    """Model for product variant"""

    name: str
    value: str
    price: float | None = None
    available: bool = True
    url: HttpUrl | None = None


class ProductPrice(BaseModel):
    """Model for product price information"""

    current_price: float
    original_price: float | None = None
    currency: str
    savings_amount: float | None = None
    savings_percent: float | None = None
    price_per_unit: str | None = None
