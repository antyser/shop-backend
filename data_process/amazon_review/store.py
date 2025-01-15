import os
import random
from typing import TypeVar

import logfire
from dotenv import load_dotenv
from supabase.client import Client, create_client

from data_process.amazon_review.load import (
    AmazonMetadata,
    AmazonReview,
    load_amazon_metadata,
)

T = TypeVar("T")


def get_supabase_client() -> Client:
    """Initialize Supabase client with environment variables"""
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env")

    return create_client(url, key)


def store_reviews(client: Client, reviews: list[AmazonReview], category: str, batch_size: int = 1000) -> None:
    """
    Store Amazon reviews in Supabase

    Args:
        client: Supabase client instance
        reviews: List of review objects
        category: Product category
        batch_size: Number of records per batch
    """
    try:
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i : i + batch_size]
            data = [{**review.model_dump(), "category": category} for review in batch]

            client.table("amazon_reviews").insert(data).execute()

            logfire.info("Stored review batch", category=category, batch_size=len(batch), start_index=i)

    except Exception as e:
        logfire.exception("Failed to store reviews", category=category, error=str(e))
        raise


def store_metadata(client: Client, metadata: list[AmazonMetadata], category: str, batch_size: int = 1000) -> None:
    """
    Store Amazon metadata in Supabase

    Args:
        client: Supabase client instance
        metadata: List of metadata objects
        category: Product category
        batch_size: Number of records per batch
    """
    try:
        for i in range(0, len(metadata), batch_size):
            batch = metadata[i : i + batch_size]
            data = [{**meta.model_dump(), "category": category} for meta in batch]

            client.table("amazon_metadata").insert(data).execute()

            logfire.info("Stored metadata batch", category=category, batch_size=len(batch), start_index=i)

    except Exception as e:
        logfire.exception("Failed to store metadata", category=category, error=str(e))
        raise


def random_sample(items: list[T], sample_size: int) -> list[T]:
    """
    Randomly sample items from a list

    Args:
        items: List of items to sample from
        sample_size: Number of items to sample

    Returns:
        Random sample of items
    """
    return random.sample(items, min(sample_size, len(items)))


def main() -> None:
    """Main execution function"""
    logfire.configure()

    # Initialize Supabase client using environment variables
    client = get_supabase_client()

    # Example category
    category = "All_Beauty"
    sample_size = 1000

    # Load and store metadata (sample)
    metadata = load_amazon_metadata(category)[:sample_size]
    logfire.info("Sampled metadata", total_records=len(metadata), sample_size=sample_size)
    store_metadata(client, metadata, category)


if __name__ == "__main__":
    main()
