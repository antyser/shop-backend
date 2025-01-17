from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DeliveryDate(BaseModel):
    """Delivery date information"""

    by: str | None = None
    from_date: str | None = Field(None, alias="from")


class DeliveryDetail(BaseModel):
    """Delivery details"""

    date: DeliveryDate | None = None
    type: str | None = None


class BuyboxItem(BaseModel):
    """Buybox pricing information"""

    price: float | None = None
    stock: str | None = None
    condition: str | None = None
    delivery_details: list[DeliveryDetail] | None = None


class SalesRankLadder(BaseModel):
    """Sales rank category information"""

    url: str | None = None
    name: str | None = None


class SalesRank(BaseModel):
    """Sales rank information"""

    rank: int | None = None
    ladder: list[SalesRankLadder] | None = None


class BuyWithItem(BaseModel):
    """Related product information"""

    asin: str | None = None
    price: float | None = None
    title: str | None = None


class RatingDistribution(BaseModel):
    """Rating distribution information"""

    rating: int | None = None
    percentage: int | None = None


class ProductDetails(BaseModel):
    """Product details information"""

    upc: str | None = None
    asin: str | None = None
    manufacturer: str | None = None
    country_of_origin: str | None = None
    item_model_number: str | None = None
    product_dimensions: str | None = None
    is_discontinued_by_manufacturer: str | None = None


class AmazonProductContent(BaseModel):
    """Main product content information"""

    url: str | None = None
    asin: str  # Keep this required as it's the primary identifier
    page: int | None = None
    brand: str | None = None
    price: float | None = None
    stock: str | None = None
    title: str | None = None
    buybox: list[BuyboxItem] | None = None
    coupon: str | None = None
    images: list[str] | None = Field(default_factory=list)
    rating: float | None = None
    currency: str | None = None
    item_form: str | None = None
    description: str | None = None
    manufacturer: str | None = None
    max_quantity: int | None = None
    price_buybox: float | None = None
    sales_volume: str | None = None
    amazon_choice: bool | None = None
    bullet_points: str | None = None
    reviews_count: int | None = None
    product_details: ProductDetails | None = None
    sales_rank: list[SalesRank] | None = None
    buy_it_with: list[BuyWithItem] | None = None
    rating_stars_distribution: list[RatingDistribution] | None = None
    price_shipping: float | None = 0
    price_strikethrough: float | None = None
    sns_discounts: list[str] | None = None


class QueryContext(BaseModel):
    """Query context information"""

    key: str | None = None
    value: Any | None = None


class QueryLinks(BaseModel):
    """Query links information"""

    rel: str | None = None
    href: str | None = None
    href_list: list[str] | None = None
    method: str | None = None


class QueryJob(BaseModel):
    """Query job information"""

    callback_url: str | None = None
    client_id: int | None = None
    context: list[QueryContext] | None = None
    created_at: datetime | None = None
    domain: str | None = None
    geo_location: str | None = None
    id: str | None = None
    parse: bool | None = None
    query: str | None = None
    source: str | None = None
    status: str | None = None
    _links: list[QueryLinks] | None = None


class QueryResult(BaseModel):
    """Query result information"""

    content: AmazonProductContent
    created_at: datetime | None = None
    updated_at: datetime | None = None
    page: int | None = None
    url: str | None = None
    job_id: str | None = None
    status_code: int | None = None


class OxyAmazonProductResponse(BaseModel):
    """Complete Oxylabs Amazon product response"""

    results: list[QueryResult]
    job: QueryJob | None = None
