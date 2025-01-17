from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Price(BaseModel):
    """Price information"""

    price: float | None = None
    currency: str | None = None
    price_strikethrough: float | None = None


class Rating(BaseModel):
    """Rating information"""

    count: int | None = None
    rating: float | None = None


class Seller(BaseModel):
    """Seller information"""

    id: str | None = None
    name: str | None = None
    official_name: str | None = None


class Location(BaseModel):
    """Store location information"""

    city: str | None = None
    state: str | None = None
    store_id: str | None = None
    zip_code: str | None = None


class Breadcrumb(BaseModel):
    """Breadcrumb navigation information"""

    url: str | None = None
    category_name: str | None = None


class Fulfillment(BaseModel):
    """Fulfillment information"""

    pickup: bool | None = None
    delivery: bool | None = None
    shipping: bool | None = None
    out_of_stock: bool | None = None
    free_shipping: bool | None = None
    pickup_information: str | None = None
    delivery_information: str | None = None
    shipping_information: str | None = None


class Specification(BaseModel):
    """Product specification"""

    key: str | None = None
    value: str | None = None


class WalmartProductContent(BaseModel):
    """Main product content information"""

    price: Price | None = None
    rating: Rating | None = None
    seller: Seller | None = None
    location: Location | None = None
    breadcrumbs: list[Breadcrumb] | None = None
    fulfillment: Fulfillment | None = None
    specifications: list[Specification] | None = None
    parse_status_code: int | None = None


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
    limit: int | None = None
    parse: bool | None = None
    parser_type: str | None = None
    query: str | None = None
    source: str | None = None
    status: str | None = None
    url: str | None = None
    _links: list[QueryLinks] | None = None


class QueryResult(BaseModel):
    """Query result information"""

    content: WalmartProductContent
    created_at: datetime | None = None
    updated_at: datetime | None = None
    page: int | None = None
    url: str | None = None
    job_id: str | None = None
    status_code: int | None = None
    parser_type: str | None = None


class OxyWalmartResponse(BaseModel):
    """Complete Oxylabs Walmart product response"""

    results: list[QueryResult]
    job: QueryJob | None = None


def parse_walmart_response(response_data: dict[str, Any]) -> OxyWalmartResponse:
    """
    Parse Oxylabs Walmart API response into structured data

    Args:
        response_data: Raw API response dictionary

    Returns:
        OxyWalmartResponse: Structured response data

    Raises:
        ValidationError: If response data is invalid
    """
    return OxyWalmartResponse(**response_data)
