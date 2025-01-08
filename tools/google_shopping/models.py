import os
from decimal import Decimal
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field


# Common Base Models
class SearchMetadata(BaseModel):
    id: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    request_time_taken: Optional[float] = None
    parsing_time_taken: Optional[float] = None
    total_time_taken: Optional[float] = None
    request_url: Optional[str] = None
    html_url: Optional[str] = None
    json_url: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class SearchParameters(BaseModel):
    engine: Optional[str] = None
    q: Optional[str] = None
    product_id: Optional[str] = None
    location: Optional[str] = None
    location_used: Optional[str] = None
    google_domain: Optional[str] = None
    hl: Optional[str] = None
    gl: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class SearchInformation(BaseModel):
    detected_location: Optional[str] = None
    total_results: Optional[int] = None
    time_taken_displayed: Optional[float] = None
    query_displayed: Optional[str] = None
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
    position: Optional[int] = None
    title: Optional[str] = None
    link: Optional[str] = None
    product_id: Optional[str] = None
    price: Optional[str] = None
    extracted_price: Optional[float] = None
    currency: Optional[str] = None
    merchant: Optional[Dict[str, str]] = None
    thumbnail: Optional[str] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    extensions: Optional[List[str]] = None
    tag: Optional[str] = None
    delivery: Optional[str] = None
    prds: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class BaseGoogleResponse(BaseModel):
    """Base class for all Google Shopping responses"""

    model_config = ConfigDict(
        extra="allow",  # Allow extra fields
        populate_by_name=True,  # Allow population by field name
        from_attributes=True,  # Allow ORM model parsing
        ser_json_timedelta="iso8601",  # Consistent datetime serialization
        validate_assignment=True,  # Validate during assignment
        reorder_fields=False,  # Preserve field order
    )


class GoogleShoppingResponse(BaseGoogleResponse):
    search_metadata: Optional[SearchMetadata] = None
    search_parameters: Optional[SearchParameters] = None
    search_information: Optional[SearchInformation] = None
    shopping_results: Optional[List[ShoppingResult]] = None
    pagination: Optional[Dict[str, str]] = None
    serpapi_pagination: Optional[Dict[str, Any]] = None
    filters: Optional[List[Dict[str, Any]]] = None


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
    name: Optional[str] = None
    badge: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class Offer(BaseModel):
    position: Optional[int] = None
    link: Optional[str] = None
    price: Optional[str] = None
    extracted_price: Optional[float] = None
    original_price: Optional[str] = None
    extracted_original_price: Optional[float] = None
    delivery_price: Optional[str] = None
    tax_price: Optional[str] = None
    extracted_tax_price: Optional[float] = None
    total_price: Optional[str] = None
    extracted_total_price: Optional[float] = None
    merchant: Optional[Merchant] = None
    promo_code: Optional[str] = None
    tag: Optional[str] = None
    extracted_delivery_price: Optional[float] = None
    model_config = ConfigDict(extra="allow")


class GoogleProductOffersResponse(BaseGoogleResponse):
    search_metadata: Optional[SearchMetadata] = None
    search_parameters: Optional[SearchParameters] = None
    search_information: Optional[SearchInformation] = None
    offers: Optional[List[Offer]] = None
    offers_link: Optional[str] = None
    error: Optional[str] = Field(
        None, description="Error message when no results are found"
    )


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
    username: Optional[str] = None
    source: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None
    rating: Optional[int] = None
    text: Optional[str] = None
    likes: Optional[int] = None
    helpful_votes: Optional[int] = None
    model_config = ConfigDict(extra="allow")


class ReviewFilter(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None
    description: Optional[str] = None
    reviews: Optional[int] = None
    positive_percentage: Optional[int] = None


class ReviewResults(BaseModel):
    reviews: Optional[List[Review]] = None
    reviews_link: Optional[str] = None
    filters: Optional[List[ReviewFilter]] = None
    next_page_token: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class GoogleProductReviewsResponse(BaseGoogleResponse):
    search_metadata: Optional[SearchMetadata] = None
    search_parameters: Optional[SearchParameters] = None
    search_information: Optional[SearchInformation] = None
    review_results: Optional[ReviewResults] = None
    pagination: Optional[Dict[str, Any]] = Field(
        None, description="Pagination information"
    )


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
    name: Optional[str] = None
    value: Optional[str] = None


class Specification(BaseModel):
    category: Optional[str] = None
    attributes: Optional[List[SpecificationAttribute]] = None


class GoogleProductSpecsResponse(BaseGoogleResponse):
    search_metadata: Optional[SearchMetadata] = None
    search_parameters: Optional[SearchParameters] = None
    search_information: Optional[SearchInformation] = None
    specifications: Optional[List[Specification]] = None
    specifications_link: Optional[str] = None
    product: Optional[Dict[str, Any]] = Field(None, description="Product information")

    model_config = ConfigDict(
        extra="allow",
        populate_by_name=True,
        from_attributes=True,
        reorder_fields=False,  # Preserve field order
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
    product_id: Optional[str] = None
    title: Optional[str] = None
    link: Optional[str] = None
    image: Optional[str] = None


class Variations(BaseModel):
    current: Optional[Dict[str, str]] = None
    options: Optional[List[ProductVariation]] = None


class TypicalPrices(BaseModel):
    low_price: Optional[str] = None
    extracted_low_price: Optional[float] = None
    high_price: Optional[str] = None
    extracted_high_price: Optional[float] = None
    popular_choice: Optional[str] = None
    popular_choice_link: Optional[str] = None
    popular_choice_price: Optional[str] = None
    extracted_popular_choice_price: Optional[float] = None
    model_config = ConfigDict(extra="allow")


class Product(BaseModel):
    product_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    reviews: Optional[int] = None
    rating: Optional[float] = None
    reviews_histogram: Optional[Dict[str, int]] = None
    highlights: Optional[List[str]] = None
    variations: Optional[Variations] = None
    extensions: Optional[List[str]] = None
    images: Optional[List[str]] = None
    model_config = ConfigDict(extra="allow")


class RelatedProduct(BaseModel):
    product_id: Optional[str] = None
    title: Optional[str] = None
    link: Optional[str] = None
    price: Optional[str] = None
    extracted_price: Optional[float] = None
    rating: Optional[float] = None
    reviews: Optional[int] = None
    thumbnail: Optional[str] = None
    prds: Optional[str] = None
    model_config = ConfigDict(extra="allow")


class GoogleProductResponse(BaseModel):
    search_metadata: Optional[SearchMetadata] = None
    search_parameters: Optional[SearchParameters] = None
    search_information: Optional[SearchInformation] = None
    product: Optional[Product] = None
    offers: Optional[List[Offer]] = None
    offers_link: Optional[str] = None
    typical_prices: Optional[TypicalPrices] = None
    review_results: Optional[ReviewResults] = None
    specifications: Optional[List[Specification]] = None
    specifications_link: Optional[str] = None
    related_products: Optional[List[RelatedProduct]] = None
