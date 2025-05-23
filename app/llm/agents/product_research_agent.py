import asyncio
from dataclasses import dataclass
from urllib.parse import urlparse

import logfire
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from app.product.model import Product
from app.product.service import get_product
from app.scraper.bright_data.google_search import google_search
from app.scraper.searchapi.google_shopping import (
    GoogleProductResponse,
    search_product_details,
)


@dataclass
class ProductResearchDeps:
    """Dependencies for product research agent"""

    query: str  # Can be URL or product name
    product_metadata: dict | None = None


class ProductReviewAnalysis(BaseModel):
    """Schema for product review analysis results"""

    evaluation_criteria: list[str] = Field(description="Key criteria for evaluating this type of product")
    features: list[str] = Field(description=("Key features and specifications of the product " "mentioned in reviews and product descriptions"))
    pros: list[str] = Field(description="Positive aspects of the product")
    cons: list[str] = Field(description="Negative aspects of the product")
    overall_rating: int = Field(description="Rating from 1-10", ge=1, le=10)
    summary: str = Field(
        description=(
            "A concise 2-3 paragraph summary analyzing the product. "
            "Include target audience, value proposition, and key differentiators. "
            "Compare with competitors if relevant."
        )
    )
    best_for: list[str] = Field(description="List of use cases or user types this product is best suited for")
    alternatives: list[str] = Field(description="Top competing products to consider")
    price_value_ratio: str = Field(description="Assessment of price to value ratio (Excellent/Good/Fair/Poor)")


research_agent = Agent(
    model="google-gla:gemini-2.0-flash-exp",
    deps_type=ProductResearchDeps,
    result_type=ProductReviewAnalysis,
    system_prompt=(
        "You are a product research expert. "
        "Analyze product features and reviews to provide balanced feedback. "
        "Consider both technical specifications and user experiences."
    ),
)


def sanitize_amazon_url(url: str) -> str:
    """
    Sanitize Amazon URL by removing query parameters and fragments

    Args:
        url: Raw Amazon URL

    Returns:
        Cleaned Amazon URL with only the product path
    """
    parsed = urlparse(url)
    # Keep only the path up to the product ID
    path_parts = parsed.path.split("/")
    product_path = "/".join(p for p in path_parts if p and p.strip())

    # Reconstruct URL with just domain and product path
    return f"https://{parsed.netloc}/{product_path}"


@research_agent.tool
async def fetch_product_metadata(ctx: RunContext[ProductResearchDeps]) -> Product | None:
    """Fetch product metadata from Amazon URL

    Returns:
        Dict with product metadata or None if not an Amazon URL
    """
    try:
        parsed = urlparse(ctx.deps.query)
        if "amazon" not in parsed.netloc.lower():
            return None

        clean_url = sanitize_amazon_url(ctx.deps.query)
        return await get_product(clean_url)
    except Exception as e:
        logfire.error(f"Failed to fetch product metadata: {str(e)}")
        return None


@research_agent.tool
async def search_product_reviews(ctx: RunContext[ProductResearchDeps]) -> dict | None:
    """Search for product reviews using Google search and product details

    Returns:
        Dict containing review content and product details or None if search fails
    """
    search_term = ctx.deps.product_metadata["name"] if ctx.deps.product_metadata else ctx.deps.query

    try:
        # Run both searches in parallel
        search_tasks = await asyncio.gather(
            google_search(query=f"{search_term} reviews", scrape_content=True), search_product_details(search_term), return_exceptions=True
        )

        # Extract results, handling any exceptions
        google_result, product_details = search_tasks

        # Initialize response dict
        response: dict[str, list[str] | GoogleProductResponse | None] = {"google_reviews": [], "product_details": None}

        # Handle Google search results
        if isinstance(google_result, Exception) or not hasattr(google_result, "organic"):
            logfire.error(f"Google search failed: {str(google_result)}")
        else:
            response["google_reviews"] = [content.content for content in google_result.organic if content.content]  # type: ignore

        # Handle product details
        if isinstance(product_details, Exception):
            logfire.error(f"Product details search failed: {str(product_details)}")
        else:
            response["product_details"] = product_details  # type: ignore

        return response

    except Exception as e:
        logfire.error(f"Failed to search reviews: {str(e)}")
        return None


async def analyze_product(query: str) -> ProductReviewAnalysis:
    """Analyze product reviews and generate insights

    Args:
        query: Product name or Amazon URL

    Returns:
        ProductReviewAnalysis containing evaluation criteria and insights
    """
    deps = ProductResearchDeps(query=query)

    # Run the agent with appropriate prompt
    prompt = f"Analyze reviews and features for {query}"
    result = await research_agent.run(prompt, deps=deps)
    return result.data  # type: ignore


if __name__ == "__main__":
    import asyncio

    logfire.configure()

    # Test with Amazon URL
    url = "https://www.amazon.com/Insta360-Standard-Bundle-Waterproof-Stabilization/dp/B0DBQBMQH2"
    result = asyncio.run(analyze_product(url))
    print("Amazon URL Test:")
    print(result)
    # Test with product name
    # name = "iPhone 15 Pro"
    # result = asyncio.run(analyze_product(name))
# print("\nProduct Name Test:")
# print(result)
