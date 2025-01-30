import asyncio
import csv
import json
import sys
from typing import Any

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from app.config import get_settings
from app.scraper.cache import scrape_cache
from app.scraper.service import scrape_product


class BaselineReview(BaseModel):
    """Schema for baseline review using only product title"""

    review: str = Field(description="A general review based only on the product title")


class FullReview(BaseModel):
    """Schema for full review using all product data"""

    review: str = Field(description="A comprehensive review including features, pros/cons, target audience, and value assessment")


GEMINI_MODEL = "google/gemini-2.0-flash-thinking-exp:free"
DEEPSEEK_R1_FREE_MODEL = "deepseek/deepseek-r1:free"
DEEPSEEK_R1_MODEL = "deepseek/deepseek-r1"
GPT_4_MODEL = "openai/chatgpt-4o-latest"
CLAUDE_3_5_SONNET_MODEL = "anthropic/claude-3.5-sonnet"

settings = get_settings()

# Configure OpenAI client for OpenRouter
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)


async def generate_baseline_review(title: str) -> BaselineReview:
    """Generate a baseline review using only the product title

    Args:
        title: Product title

    Returns:
        BaselineReview containing the review
    """
    try:
        logger.info(f"Generating baseline review for: {title}")
        response = await client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a product research expert. Based only on the product title, "
                        "provide a general review of what you would expect from this type of product."
                    ),
                },
                {"role": "user", "content": f"Product title: {title}"},
            ],
        )

        if hasattr(response, "error"):
            raise ValueError(f"API Error: {response.error}")

        if not response.choices:
            raise ValueError(f"No response received from the model: {response}")

        review = response.choices[0].message.content
        if not review:
            raise ValueError(f"Empty review received from the model: {response}")

        logger.success("Successfully generated baseline review")
        return BaselineReview(review=review)

    except Exception as e:
        print(f"Error details: {str(e)}", file=sys.stderr)
        if hasattr(e, "__cause__") and e.__cause__ is not None:
            print(f"Caused by: {str(e.__cause__)}", file=sys.stderr)
        logger.error(f"Failed to generate baseline review: {str(e)}")
        raise


async def generate_full_review(context: dict) -> FullReview:
    """Generate a comprehensive review using full product data

    Args:
        context: Complete product data including features and reviews

    Returns:
        FullReview containing the comprehensive review
    """
    try:
        logger.info("Generating full product review")
        system_prompt = (
            "You are a product research expert. "
            "Analyze product features and reviews to provide balanced feedback. "
            "First say how to select this type of product and then provide a review given this "
            "product's features and reviews."
        )

        response = await client.chat.completions.create(
            model=GEMINI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Here is the product data and related reviews to analyze:\n"
                        f"{json.dumps(context, indent=2)}\n\n"
                        f"Please provide a comprehensive review."
                    ),
                },
            ],
        )

        if hasattr(response, "error"):
            raise ValueError(f"API Error: {response.error}")

        if not response.choices:
            raise ValueError(f"No response received from the model: {response}")

        review = response.choices[0].message.content
        if not review:
            raise ValueError(f"Empty review received from the model: {response}")

        logger.success("Successfully generated full review")
        return FullReview(review=review)

    except Exception as e:
        print(f"Error details: {str(e)}", file=sys.stderr)
        if hasattr(e, "__cause__") and e.__cause__ is not None:
            print(f"Caused by: {str(e.__cause__)}", file=sys.stderr)
        logger.error(f"Failed to generate full review: {str(e)}")
        raise


@retry(
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((ValueError, Exception)),
    before_sleep=lambda retry_state: logger.warning(f"Retrying due to error (attempt {retry_state.attempt_number}/3)..."),
)
async def analyze_product(url: str) -> tuple[BaselineReview, FullReview]:
    """Analyze product and generate both baseline and full reviews with retry logic

    Args:
        url: Product URL (Amazon or Walmart)

    Returns:
        Tuple of (BaselineReview, FullReview)

    Raises:
        Exception: If all retry attempts fail
    """
    try:
        # Check cache first
        cached_data = scrape_cache.get(url)
        product_context: dict[str, Any] | None = None

        if cached_data:
            logger.info(f"Using cached data for {url}")
            # Validate cached data has required fields
            if "product" not in cached_data or not isinstance(cached_data["product"], dict):
                logger.warning(f"Missing product data in cache for {url}, fetching fresh data")
            elif "title" not in cached_data["product"]:
                logger.warning(f"Missing title in cached product data for {url}, fetching fresh data")
            else:
                product_context = cached_data

        if not product_context:
            # Fetch and cache product data
            try:
                logger.info(f"Fetching product data from {url}")
                product_data = await scrape_product(url)
                product_context = product_data.model_dump()
                scrape_cache.set(url, product_context)  # type: ignore
                logger.success(f"Successfully fetched and cached data for {url}")
            except Exception as e:
                print(f"Error details: {str(e)}", file=sys.stderr)
                if hasattr(e, "__cause__") and e.__cause__ is not None:
                    print(f"Caused by: {str(e.__cause__)}", file=sys.stderr)
                logger.error(f"Failed to fetch product data: {str(e)}")
                raise

        # Validate context has required fields
        if not isinstance(product_context, dict):
            raise ValueError(f"Invalid data format for {url}")

        if "product" not in product_context or not isinstance(product_context["product"], dict):
            raise ValueError(f"Missing product data for {url}")

        product_data = product_context["product"]  # type: ignore
        if "title" not in product_data:
            raise ValueError(f"Missing title in product data for {url}")

        # Generate both reviews using product title
        baseline_review = await generate_baseline_review(product_data["title"])
        full_review = await generate_full_review(product_context)

        return baseline_review, full_review

    except Exception as e:
        print(f"Error details: {str(e)}", file=sys.stderr)
        if hasattr(e, "__cause__") and e.__cause__ is not None:
            print(f"Caused by: {str(e.__cause__)}", file=sys.stderr)
        logger.error(f"Failed to analyze product: {str(e)}")
        raise


async def process_urls(urls: list[str]) -> dict[str, tuple[str, str]]:
    """Process multiple URLs and generate reviews

    Args:
        urls: List of product URLs to analyze

    Returns:
        Dictionary mapping URLs to (full_review, baseline_review) tuples
    """
    results = {}
    for url in urls:
        try:
            logger.info(f"Processing URL: {url}")
            baseline_review, full_review = await analyze_product(url)
            results[url] = (full_review.review, baseline_review.review)
            logger.success(f"Successfully processed {url}")
        except Exception as e:
            logger.error(f"Failed to process {url}: {str(e)}")
            results[url] = (f"Error: {str(e)}", f"Error: {str(e)}")
    return results


def save_results_to_csv(results: dict[str, tuple[str, str]], filename: str = "product_reviews.csv") -> None:
    """Save results to CSV file

    Args:
        results: Dictionary mapping URLs to (full_review, baseline_review) tuples
        filename: Output CSV filename
    """
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Full Review", "Baseline Review"])
            for url, (full_review, baseline_review) in results.items():
                writer.writerow([url, full_review, baseline_review])
        logger.success(f"Results saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save results: {str(e)}")
        raise


if __name__ == "__main__":
    # Configure loguru with a more detailed format
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="INFO",
    )

    # List of URLs to process
    urls: list[str] = [
        "https://www.amazon.com/gp/aw/d/B08FWXPRFP/?_encoding=UTF8&pd_rd_plhdr=t",
        "https://www.amazon.com/dp/B0009YWKUA/?_encoding=UTF8",
        "https://www.amazon.com/FIFINE-Microphone-Voice-Over-Windscreen-Amplitank-K688/dp/B0B8SNVK5K",
        "https://www.walmart.com/ip/360-Oscillating-Toothbrush-Black-Black/5726850536",
        "https://www.walmart.com/ip/Coach-Women-s-Kristy-Shoulder-Bag/2100858768",
        "https://www.walmart.com/ip/Evenflo-Advanced-Double-Electric-Breast-Pump/795240370",
    ]

    try:
        logger.info("Starting batch product analysis")
        results = asyncio.run(process_urls(urls))
        save_results_to_csv(results)
        logger.success("Batch processing completed successfully")
    except Exception as e:
        print(f"Error details: {str(e)}", file=sys.stderr)
        if hasattr(e, "__cause__") and e.__cause__ is not None:
            print(f"Caused by: {str(e.__cause__)}", file=sys.stderr)
        logger.error("Batch processing failed")
        sys.exit(1)
