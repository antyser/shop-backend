from datetime import datetime

from pydantic import BaseModel, HttpUrl


class Review(BaseModel):
    rating: float | None = None
    title: str
    text: str
    images: list[str] = []
    timestamp: datetime | None = None
    verified_purchase: bool = False

    marketplace: str
    product_id: str
    user_id: str | None = None
    review_id: str | None = None

    # Add other common optional fields as needed
    helpful_vote: int = 0
    review_url: HttpUrl | None = None  # URL of the review
    author_name: str | None = None

    # Marketplace-specific data as a dictionary
    marketplace_specific_data: dict | None = None
