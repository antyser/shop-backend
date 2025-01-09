from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class ItemAvailability(str, Enum):
    BACK_ORDER = "https://schema.org/BackOrder"
    DISCONTINUED = "https://schema.org/Discontinued"
    IN_STOCK = "https://schema.org/InStock"
    IN_STORE_ONLY = "https://schema.org/InStoreOnly"
    LIMITED_AVAILABILITY = "https://schema.org/LimitedAvailability"
    ONLINE_ONLY = "https://schema.org/OnlineOnly"
    OUT_OF_STOCK = "https://schema.org/OutOfStock"
    PRE_ORDER = "https://schema.org/PreOrder"
    PRE_SALE = "https://schema.org/PreSale"
    SOLD_OUT = "https://schema.org/SoldOut"


class Rating(BaseModel):
    ratingValue: float
    bestRating: float | None = None
    worstRating: float | None = None


class Review(BaseModel):
    author: str | None = None
    datePublished: date | None = None
    reviewBody: str | None = None
    name: str | None = None
    reviewRating: Rating | None = None


class AggregateRating(BaseModel):
    ratingValue: float
    reviewCount: int | None = None
    ratingCount: int | None = None


class Offer(BaseModel):
    price: float
    priceCurrency: str
    availability: ItemAvailability | None = None
    priceValidUntil: date | None = None
    url: HttpUrl | None = None


class Brand(BaseModel):
    name: str


class ProductMetadata(BaseModel):
    name: str
    description: str | None = None
    brand: Brand | None = None
    image: list[HttpUrl] | None = Field(default_factory=list)
    offers: list[Offer] | None = Field(default_factory=list)
    review: list[Review] | None = Field(default_factory=list)
    aggregateRating: AggregateRating | None = None
    sku: str | None = None
    mpn: str | None = None
    gtin: str | None = None
