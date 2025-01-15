from typing import Any

import logfire
from datasets import load_dataset
from pydantic import BaseModel

# Configure logfire
logfire.configure()


class AmazonReview(BaseModel):
    """Schema for Amazon review data"""

    rating: float
    title: str
    text: str
    images: list
    asin: str
    parent_asin: str
    user_id: str
    timestamp: int
    helpful_vote: int
    verified_purchase: bool


class AmazonMetadata(BaseModel):
    """Schema for Amazon product metadata"""

    main_category: str
    title: str
    average_rating: float
    rating_number: int
    features: list
    description: list
    price: str | None
    images: dict[str, list]
    videos: dict[str, list]
    store: str | None
    categories: list
    details: str
    parent_asin: str
    bought_together: Any | None
    subtitle: str | None
    author: str | None


def load_amazon_reviews(category: str, split: str = "full", trust_remote_code: bool = True) -> list[AmazonReview]:
    """
    Load Amazon review data for a specific category

    Args:
        category: Product category (e.g., 'All_Beauty')
        split: Dataset split to load
        trust_remote_code: Whether to trust remote code

    Returns:
        List of AmazonReview objects
    """
    try:
        dataset_name = f"raw_review_{category}"
        dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", dataset_name, split=split, trust_remote_code=trust_remote_code)

        reviews = [AmazonReview(**review) for review in dataset]

        logfire.info("Reviews loaded successfully", category=category, count=len(reviews))
        return reviews

    except Exception as e:
        logfire.exception("Failed to load reviews", category=category, error=str(e))
        raise


def load_amazon_metadata(category: str, split: str = "full", trust_remote_code: bool = True) -> list[AmazonMetadata]:
    """
    Load Amazon product metadata for a specific category

    Args:
        category: Product category (e.g., 'All_Beauty')
        split: Dataset split to load
        trust_remote_code: Whether to trust remote code

    Returns:
        List of AmazonMetadata objects
    """
    try:
        dataset_name = f"raw_meta_{category}"
        dataset = load_dataset("McAuley-Lab/Amazon-Reviews-2023", dataset_name, split=split, trust_remote_code=trust_remote_code)

        metadata = [AmazonMetadata(**meta) for meta in dataset]

        logfire.info("Metadata loaded successfully", category=category, count=len(metadata))
        return metadata

    except Exception as e:
        logfire.exception("Failed to load metadata", category=category, error=str(e))
        raise


if __name__ == "__main__":
    # Example usage
    category = "All_Beauty"

    # Load metadata
    metadata = load_amazon_metadata(category)
    logfire.info("Metadata sample", category=category, sample=metadata[0].model_dump())
