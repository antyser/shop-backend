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

    title: str | None = None  # Derived from URL or specifications
    description: str | None = None
    brand: str | None = None
    price: Price | None = None
    rating: Rating | None = None
    seller: Seller | None = None
    location: Location | None = None
    breadcrumbs: list[Breadcrumb] | None = None
    fulfillment: Fulfillment | None = None
    specifications: list[Specification] | None = None
    parse_status_code: int | None = None

    def get_title(self) -> str:
        """Get product title from specifications or URL"""
        if self.title:
            return self.title
        if self.specifications:
            for spec in self.specifications:
                if spec.key and spec.key.lower() == "title" and spec.value:
                    return spec.value
        return "Unknown Product"


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
    # Extract content from results
    if not response_data.get("results"):
        raise ValueError("No results in response")

    result = response_data["results"][0]
    content = result.get("content", {})
    general = content.get("general", {})

    # Combine general and other fields
    product_content = {
        "url": general.get("url"),
        "title": general.get("title"),
        "description": general.get("description"),
        "brand": general.get("brand"),
        "price": content.get("price"),
        "rating": content.get("rating"),
        "seller": content.get("seller"),
        "location": content.get("location"),
        "breadcrumbs": content.get("breadcrumbs"),
        "fulfillment": content.get("fulfillment"),
        "specifications": content.get("specifications"),
        "parse_status_code": content.get("parse_status_code"),
    }

    # Create QueryResult with the combined content
    query_result = QueryResult(
        content=WalmartProductContent(**product_content),
        created_at=result.get("created_at"),
        updated_at=result.get("updated_at"),
        page=result.get("page"),
        url=result.get("url"),
        job_id=result.get("job_id"),
        status_code=result.get("status_code"),
        parser_type=result.get("parser_type"),
    )

    return OxyWalmartResponse(results=[query_result], job=response_data.get("job"))
