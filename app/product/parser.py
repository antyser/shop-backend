import asyncio
from datetime import datetime
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from product.model import Identifiers, Product, Ratings
from pydantic import BaseModel

from app.scraper.bright_data.amazon import Product as AmazonProduct
from app.scraper.bright_data.amazon import scrape_amazon_product


class ProductDetail(BaseModel):
    """Product detail model"""

    type: str
    value: str


def extract_product_attribute(product_details: list[dict[str, Any]], attribute_type: str) -> str | None:
    """
    Extract specific attribute from product details

    Args:
        product_details: List of product detail dictionaries
        attribute_type: Type of attribute to extract

    Returns:
        Optional[str]: Extracted attribute value or None
    """
    if not product_details:
        return None

    matches = [detail["value"] for detail in product_details if detail["type"] == attribute_type]
    return matches[0] if matches else None


def parse_amazon_product(amazon_product: AmazonProduct) -> Product:
    """
    Parse AmazonProduct data into Product model"""

    # Create identifiers
    identifiers = Identifiers(
        asin=amazon_product.asin,
        upc=amazon_product.upc,
    )

    # Create ratings if available
    ratings = None
    if amazon_product.rating:
        ratings = Ratings(
            average_rating=amazon_product.rating,
            total_ratings=amazon_product.reviews_count,
        )

    # Convert variations to dictionaries
    variants = None
    if amazon_product.variations:
        variants = [variation.model_dump() for variation in amazon_product.variations]

    return Product(
        # Basic Product Information
        title=amazon_product.title,
        description=amazon_product.description,
        brand=amazon_product.brand,
        images=amazon_product.images or [],
        feature_image=amazon_product.image_url,
        videos=amazon_product.videos or [],
        video_count=amazon_product.video_count,
        identifiers=identifiers,
        url=amazon_product.url,
        features=amazon_product.features or [],
        date_first_available=amazon_product.date_first_available,
        # Seller Information
        seller_name=amazon_product.seller_name,
        seller_url=amazon_product.seller_url,
        # Product Specifications
        weight=amazon_product.item_weight,
        model_number=amazon_product.model_number,
        manufacturer=amazon_product.manufacturer,
        country_of_origin=amazon_product.country_of_origin,
        ingredients=amazon_product.ingredients,
        # Category Information
        original_categories=amazon_product.categories,
        canonical_categories=amazon_product.categories,
        # Price and Offers
        final_price=amazon_product.final_price,
        initial_price=amazon_product.initial_price,
        discount=amazon_product.discount,
        currency=amazon_product.currency,
        availability=amazon_product.availability,
        variants=variants,
        # Ratings and Reviews
        ratings=ratings,
        reviews_count=amazon_product.reviews_count,
        # Amazon Specific Fields
        amazon_parent_asin=amazon_product.parent_asin,
        amazon_number_of_sellers=amazon_product.number_of_sellers,
        amazon_root_bs_rank=amazon_product.root_bs_rank,
        amazon_answered_questions=amazon_product.answered_questions,
        amazon_plus_content=amazon_product.plus_content,
        amazon_top_review=amazon_product.top_review,
        amazon_input_asin=amazon_product.input_asin,
        amazon_origin_url=amazon_product.origin_url,
        amazon_bought_past_month=amazon_product.bought_past_month,
        amazon_is_available=amazon_product.is_available,
        amazon_root_bs_category=amazon_product.root_bs_category,
        amazon_bs_category=amazon_product.bs_category,
        amazon_bs_rank=amazon_product.bs_rank,
        amazon_badge=amazon_product.badge,
        amazon_subcategory_rank=(
            [{"subcategory_name": rank.subcategory_name, "subcategory_rank": rank.subcategory_rank} for rank in amazon_product.subcategory_rank]
            if amazon_product.subcategory_rank
            else None
        ),
        amazon_choice=amazon_product.amazon_choice,
        amazon_customer_says=amazon_product.customer_says,
        amazon_sustainability_features=amazon_product.sustainability_features,
        amazon_climate_pledge_friendly=amazon_product.climate_pledge_friendly,
        amazon_videos=amazon_product.videos,
        amazon_other_sellers_prices=amazon_product.other_sellers_prices,
        # Timestamps
        created_at=amazon_product.timestamp or datetime.now(),
        updated_at=amazon_product.timestamp or datetime.now(),
    )


async def main(urls: list[str]) -> None:
    """
    Main function to scrape and parse Amazon products

    Args:
        urls: List of Amazon product URLs to process
    """
    try:
        # Scrape products
        product_response = await scrape_amazon_product(urls)

        if not product_response or not product_response.products:
            logger.error("No products found")
            return

        # Parse each product
        for raw_product in product_response.products:
            try:
                # Create AmazonProduct instance

                # Parse to our Product model
                product = parse_amazon_product(raw_product)

                # Print product details
                logger.info(
                    f"\nParsed Product Details:"
                    f"\nTitle: {product.title}"
                    f"\nBrand: {product.brand}"
                    f"\nPrice: {product.final_price} {product.currency}"
                    f"\nASIN: {product.identifiers.asin if product.identifiers else 'N/A'}"
                    f"\nURL: {product.url}"
                )

                # Optional: Print full product details
                logger.debug(f"Full product details:\n" f"{product.model_dump_json(indent=2)}")

            except Exception as e:
                logger.error(f"Error parsing product: {str(e)}", exc_info=True)
                continue

    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)


if __name__ == "__main__":
    # Example URLs
    load_dotenv()
    urls = [
        # "https://www.amazon.com/dp/B07N2BC377",
        # "https://www.amazon.com/dp/B089M1BH1K",
        # "https://www.amazon.com/Sengled-Alexa-Light-Bulb-S1/dp/B08DJBDG5L?th=1&psc=1&language=en_US&currency=USD",
        # "https://www.amazon.com/Notakia-Electroplating-Balloon-Dog-Decorations/dp/B0C66K596L?th=1&psc=1&language=en_US&currency=USD",
        # "https://www.amazon.com/Turtle-Stealth-Wireless-Headset-Licensed-Bluetooth/dp/B0CYWLSCFW?th=1&psc=1&language=en_US&currency=USD",
        "https://www.amazon.com/Greenland-Home-Antique-Quilted-Patchwork/dp/B0045SKUS0?th=1&psc=1&language=en_US&currency=USD",
        "https://www.amazon.com/MIAYBPH-Chandelier-Geometric-Industrial-Farmhouse/dp/B0CNCKLSKN?th=1&psc=1&language=en_US&currency=USD",
        "https://www.amazon.com/Sailstar-Dimmable-Candelabra-Equivalent-Chandelier/dp/B07V42LQG1?th=1&psc=1&language=en_US&currency=USD",
        "https://www.amazon.com/Premium-Alternator-Compatible-Silverado-Suburban/dp/B0B3RLRW29?th=1&psc=1&language=en_US&currency=USD",
        "https://www.amazon.com/Engraver-10W-Engraving-Machine-Engravers/dp/B0CZ8ZF56Y?th=1&psc=1&language=en_US&currency=USD",
    ]

    # Run async main
    asyncio.run(main(urls))
