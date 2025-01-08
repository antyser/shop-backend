from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# Common Base Models
class SearchMetadata(BaseModel):
    id: str | None = None
    status: str | None = None
    created_at: str | None = None
    request_time_taken: float | None = None
    parsing_time_taken: float | None = None
    total_time_taken: float | None = None
    request_url: str | None = None
    html_url: str | None = None
    json_url: str | None = None
    model_config = ConfigDict(extra="allow")


class SearchParameters(BaseModel):
    engine: str | None = None
    q: str | None = None
    product_id: str | None = None
    location: str | None = None
    location_used: str | None = None
    google_domain: str | None = None
    hl: str | None = None
    gl: str | None = None
    model_config = ConfigDict(extra="allow")


class SearchInformation(BaseModel):
    detected_location: str | None = None
    total_results: int | None = None
    time_taken_displayed: float | None = None
    query_displayed: str | None = None
    model_config = ConfigDict(extra="allow")


# Shopping Search Models
class ShoppingSearchParameters(BaseModel):
    engine: str
    q: str
    location: str
    location_used: str
    google_domain: str
    hl: str
    gl: str


class ShoppingResult(BaseModel):
    position: int | None = None
    title: str | None = None
    link: str | None = None
    product_id: str | None = None
    price: str | None = None
    extracted_price: float | None = None
    currency: str | None = None
    merchant: dict[str, str] | None = None
    thumbnail: str | None = None
    rating: float | None = None
    reviews: int | None = None
    extensions: list[str] | None = None
    tag: str | None = None
    delivery: str | None = None
    prds: str | None = None
    model_config = ConfigDict(extra="allow")


class BaseGoogleResponse(BaseModel):
    """Base class for all Google Shopping responses"""

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields
        populate_by_name=True,  # Allow population by field name
        from_attributes=True,  # Allow ORM model parsing
        ser_json_timedelta="iso8601",  # Consistent datetime serialization
        validate_assignment=True,  # Validate during assignment
    )


class GoogleShoppingResponse(BaseGoogleResponse):
    search_metadata: SearchMetadata | None = None
    search_parameters: SearchParameters | None = None
    search_information: SearchInformation | None = None
    shopping_results: list[ShoppingResult] | None = None
    pagination: dict[str, str] | None = None
    serpapi_pagination: dict[str, Any] | None = None
    filters: list[dict[str, Any]] | None = None


# Product Offers Models
class OfferSearchParameters(BaseModel):
    engine: str
    product_id: str
    location: str
    location_used: str
    google_domain: str
    hl: str
    gl: str


class Merchant(BaseModel):
    name: str | None = None
    badge: str | None = None
    model_config = ConfigDict(extra="allow")


class Offer(BaseModel):
    position: int | None = None
    link: str | None = None
    price: str | None = None
    extracted_price: float | None = None
    original_price: str | None = None
    extracted_original_price: float | None = None
    delivery_price: str | None = None
    tax_price: str | None = None
    extracted_tax_price: float | None = None
    total_price: str | None = None
    extracted_total_price: float | None = None
    merchant: Merchant | None = None
    promo_code: str | None = None
    tag: str | None = None
    extracted_delivery_price: float | None = None
    model_config = ConfigDict(extra="allow")


class GoogleProductOffersResponse(BaseGoogleResponse):
    search_metadata: SearchMetadata | None = None
    search_parameters: SearchParameters | None = None
    search_information: SearchInformation | None = None
    offers: list[Offer] | None = None
    offers_link: str | None = None
    error: str | None = Field(None, description="Error message when no results are found")


# Product Reviews Models
class ReviewSearchParameters(BaseModel):
    engine: str
    product_id: str
    location: str
    location_used: str
    google_domain: str
    hl: str
    gl: str
    num: int


class Review(BaseModel):
    username: str | None = None
    source: str | None = None
    title: str | None = None
    date: str | None = None
    rating: int | None = None
    text: str | None = None
    likes: int | None = None
    helpful_votes: int | None = None
    model_config = ConfigDict(extra="allow")


class ReviewFilter(BaseModel):
    title: str | None = None
    link: str | None = None
    description: str | None = None
    reviews: int | None = None
    positive_percentage: int | None = None


class ReviewResults(BaseModel):
    reviews: list[Review] | None = None
    reviews_link: str | None = None
    filters: list[ReviewFilter] | None = None
    next_page_token: str | None = None
    model_config = ConfigDict(extra="allow")


class GoogleProductReviewsResponse(BaseGoogleResponse):
    search_metadata: SearchMetadata | None = None
    search_parameters: SearchParameters | None = None
    search_information: SearchInformation | None = None
    review_results: ReviewResults | None = None
    pagination: dict[str, Any] | None = Field(None, description="Pagination information")


# Product Specifications Models
class SpecSearchParameters(BaseModel):
    engine: str
    product_id: str
    location: str
    location_used: str
    google_domain: str
    hl: str
    gl: str


class SpecificationAttribute(BaseModel):
    name: str | None = None
    value: str | None = None


class Specification(BaseModel):
    category: str | None = None
    attributes: list[SpecificationAttribute] | None = None


class GoogleProductSpecsResponse(BaseGoogleResponse):
    search_metadata: SearchMetadata | None = None
    search_parameters: SearchParameters | None = None
    search_information: SearchInformation | None = None
    specifications: list[Specification] | None = None
    specifications_link: str | None = None
    product: dict[str, Any] | None = Field(None, description="Product information")

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        from_attributes=True,
    )


# Complete Product Details Models
class ProductSearchParameters(BaseModel):
    engine: str
    product_id: str
    location: str
    location_used: str
    google_domain: str
    hl: str
    gl: str


class ProductVariation(BaseModel):
    product_id: str | None = None
    title: str | None = None
    link: str | None = None
    image: str | None = None


class Variations(BaseModel):
    current: dict[str, str] | None = None
    options: list[ProductVariation] | None = None


class TypicalPrices(BaseModel):
    low_price: str | None = None
    extracted_low_price: float | None = None
    high_price: str | None = None
    extracted_high_price: float | None = None
    popular_choice: str | None = None
    popular_choice_link: str | None = None
    popular_choice_price: str | None = None
    extracted_popular_choice_price: float | None = None
    model_config = ConfigDict(extra="allow")


class Product(BaseModel):
    product_id: str | None = None
    title: str | None = None
    description: str | None = None
    reviews: int | None = None
    rating: float | None = None
    reviews_histogram: dict[str, int] | None = None
    highlights: list[str] | None = None
    variations: Variations | None = None
    extensions: list[str] | None = None
    images: list[str] | None = None
    model_config = ConfigDict(extra="allow")


class RelatedProduct(BaseModel):
    product_id: str | None = None
    title: str | None = None
    link: str | None = None
    price: str | None = None
    extracted_price: float | None = None
    rating: float | None = None
    reviews: int | None = None
    thumbnail: str | None = None
    prds: str | None = None
    model_config = ConfigDict(extra="allow")


class GoogleProductResponse(BaseModel):
    search_metadata: SearchMetadata | None = None
    search_parameters: SearchParameters | None = None
    search_information: SearchInformation | None = None
    product: Product | None = None
    offers: list[Offer] | None = None
    offers_link: str | None = None
    typical_prices: TypicalPrices | None = None
    review_results: ReviewResults | None = None
    specifications: list[Specification] | None = None
    specifications_link: str | None = None
    related_products: list[RelatedProduct] | None = None
