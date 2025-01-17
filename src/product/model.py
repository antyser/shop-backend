from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Identifiers(BaseModel):
    gtin: str | None = Field(default=None, description="Global Trade Item Number.")
    mpn: str | None = Field(default=None, description="Manufacturer Part Number")
    asin: str | None = Field(default=None, description="Amazon Standard Identification Number.")
    google_product_id: str | None = Field(default=None, description="Google Product ID.")
    sku: str | None = Field(default=None, description="Stock Keeping Unit")
    upc: str | None = Field(default=None, description="Universal Product Code")


class Ratings(BaseModel):
    one_star: int | None = Field(default=None, description="Number of 1-star ratings")
    two_stars: int | None = Field(default=None, description="Number of 2-star ratings")
    three_stars: int | None = Field(default=None, description="Number of 3-star ratings")
    four_stars: int | None = Field(default=None, description="Number of 4-star ratings")
    five_stars: int | None = Field(default=None, description="Number of 5-star ratings")
    average_rating: float | None = Field(default=None, description="Average rating")
    total_ratings: int | None = Field(default=None, description="Total number of ratings")


class Product(BaseModel):
    # Basic Product Information
    title: str | None = Field(default=None, description="The title or name of the product.")
    description: str | None = Field(default=None, description="A description of the product.")
    images: list[str] | None = Field(default=None, description="Array of URLs for product images.")
    feature_image: str | None = Field(default=None, format="url", description="URL of the product image")
    videos: list[str] | None = Field(default=None, format="url", description="URL of the product videos")
    video_count: int | None = Field(default=None, description="Number of product videos")
    identifiers: Identifiers | None = Field(default=None, description="Object of identifiers")
    brand: str | None = Field(default=None, description="The brand of the product")
    url: str | None = Field(default=None, format="url", description="URL of the product")
    features: list[str] | None = Field(default=None, description="Features of the product")
    date_first_available: str | None = Field(default=None, description="Date of first availability of the product")

    seller_name: str | None = Field(default=None, description="Name of the seller")
    seller_url: str | None = Field(default=None, format="url", description="URL of the seller")

    # Product Specifications
    size: str | None = Field(default=None, description="Size of the product")
    weight: str | None = Field(default=None, description="Weight of the product")
    color: str | None = Field(default=None, description="Color of the product")
    model_number: str | None = Field(default=None, description="Model number of the product")
    manufacturer: str | None = Field(default=None, description="Manufacturer of the product")
    country_of_origin: str | None = Field(default=None, description="Country of origin of the product")
    ingredients: str | None = Field(default=None, description="Ingredients of the product")
    additional_attributes: list[dict[str, str]] | None = Field(default=None, description="Additional attributes of the product")
    tags: list[str] | None = Field(default=None, description="Tags of the product")
    variants: list[dict[str, Any]] | None = Field(default=None, description="Variants of the product")

    # Category Information
    canonical_categories: list[str] | None = Field(default=None, description="Unified category path")
    original_categories: list[str] | None = Field(default=None, description="Original categories from each platform")

    # Price and Offers
    final_price: float | None = Field(default=None, description="Final price of the product")
    initial_price: float | None = Field(default=None, description="Initial price of the product")
    discount: float | None = Field(default=None, description="Discount on the product")
    currency: str | None = Field(default=None, description="Currency used for pricing")
    unit_price: str | None = Field(default=None, description="Unit price of the product")
    availability: str | None = Field(default=None, description="Availability of the product")

    # Policies
    shipping: str | None = Field(default=None, description="Shipping details for the product")
    tax: str | None = Field(default=None, description="Tax information")
    return_policy: str | None = Field(default=None, description="Details for return policy")

    ratings: Ratings | None = Field(default=None, description="Ratings of the product")
    reviews_count: int | None = Field(default=None, description="Number of reviews for the product")

    # Marketplace Specific - Google Shopping
    google_shopping_seller_name: str | None = Field(default=None, description="Name of the seller on Google shopping")
    google_shopping_delivery_price: str | None = Field(default=None, description="Price for delivery on Google shopping")
    google_shopping_item_price: str | None = Field(default=None, description="Price of item on Google shopping")
    google_shopping_total_price: str | None = Field(default=None, description="Total price of item on Google shopping")
    google_shopping_related_items: list[dict[str, str]] | None = Field(default=None, description="Related items of the product")

    # Marketplace Specific - Amazon
    amazon_parent_asin: str | None = Field(default=None, description="Parent ASIN for the product")
    amazon_number_of_sellers: int | None = Field(default=None, description="Number of sellers on Amazon")
    amazon_root_bs_rank: int | None = Field(default=None, description="Best sellers rank on Amazon")
    amazon_answered_questions: int | None = Field(default=None, description="Number of questions answered on Amazon")
    # amazon_domain: Optional[str] = Field(default=None, format="url", description="URL of product domain on Amazon")
    amazon_plus_content: bool | None = Field(default=None, description="Additional content indicator on Amazon")
    amazon_top_review: str | None = Field(default=None, description="Top review for product on Amazon")
    amazon_buybox_prices: dict[str, float] | None = Field(default=None, description="Amazon product price details")
    amazon_input_asin: str | None = Field(default=None, description="Input asin on Amazon")
    amazon_origin_url: str | None = Field(default=None, format="url", description="Origin url of product on Amazon")
    amazon_bought_past_month: int | None = Field(default=None, description="Product bought in last month on Amazon")
    amazon_is_available: bool | None = Field(default=None, description="Availability indicator of the product on Amazon")
    amazon_root_bs_category: str | None = Field(default=None, description="Best seller root category on Amazon")
    amazon_bs_category: str | None = Field(default=None, description="Best seller category on Amazon")
    amazon_bs_rank: int | None = Field(default=None, description="Best seller rank of product on Amazon")
    amazon_badge: str | None = Field(default=None, description="Badge for product on Amazon")
    amazon_subcategory_rank: list[dict[str, Any]] | None = Field(default=None, description="Rank of subcategory on Amazon")
    amazon_choice: bool | None = Field(default=None, description="Amazon choice indicator for product")
    amazon_product_details: list[dict[str, str]] | None = Field(default=None, description="Full product details on Amazon")
    amazon_prices_breakdown: dict[str, float] | None = Field(default=None, description="Price breakdown on Amazon")
    amazon_from_the_brand: list[str] | None = Field(default=None, description="Brand information on Amazon")
    amazon_product_description: list[dict[str, str]] | None = Field(default=None, description="Description of the product on Amazon")
    amazon_customer_says: str | None = Field(default=None, description="Customer review on Amazon")
    amazon_sustainability_features: list[dict[str, Any]] | None = Field(default=None, description="Sustainability features of the product on Amazon")
    amazon_climate_pledge_friendly: bool | None = Field(default=None, description="Climate pledge indicator on Amazon")
    amazon_videos: list[str] | None = Field(default=None, format="url", description="Videos of the product on Amazon")
    amazon_other_sellers_prices: list[dict[str, Any]] | None = Field(default=None, description="Other sellers prices on Amazon")
    amazon_downloadable_videos: list[str] | None = Field(default=None, format="url", description="Downloadable videos on Amazon")

    # Marketplace Specific - Walmart
    walmart_top_reviews: dict[str, Any] | None = Field(default=None, description="Top reviews of product on Walmart")
    walmart_related_pages: list[str] | None = Field(default=None, format="url", description="Related pages on Walmart")
    walmart_available_for_delivery: bool | None = Field(default=None, description="Product is available for delivery on Walmart")
    walmart_available_for_pickup: bool | None = Field(default=None, description="Product is available for pickup on Walmart")
    walmart_breadcrumbs: list[dict[str, str]] | None = Field(default=None, description="Breadcrumbs of product on Walmart")
    walmart_category_ids: str | None = Field(default=None, description="Category IDs on Walmart")
    walmart_review_count: int | None = Field(default=None, description="Number of reviews on Walmart")
    walmart_product_id: str | None = Field(default=None, description="Product ID on Walmart")
    walmart_product_name: str | None = Field(default=None, description="Product name on Walmart")
    walmart_review_tags: list[str] | None = Field(default=None, description="Tags of the review on Walmart")
    walmart_category_url: str | None = Field(default=None, format="url", description="URL of category on Walmart")
    walmart_category_name: str | None = Field(default=None, description="Name of the category on Walmart")
    walmart_root_category_url: str | None = Field(default=None, format="url", description="URL of the root category on Walmart")
    walmart_root_category_name: str | None = Field(default=None, description="Name of the root category on Walmart")
    walmart_rating: float | None = Field(default=None, description="Rating of the product on Walmart")
    walmart_aisle: str | None = Field(default=None, description="Aisle on Walmart")
    walmart_sizes: list[str] | None = Field(default=None, description="Sizes of the product on Walmart")
    walmart_colors: list[str] | None = Field(default=None, description="Colors of the product on Walmart")
    walmart_seller: str | None = Field(default=None, description="Seller of product on Walmart")
    walmart_other_attributes: list[dict[str, str]] | None = Field(default=None, description="Other attributes of product on Walmart")
    walmart_customer_reviews: list[dict[str, Any]] | None = Field(default=None, description="Customer review on Walmart")
    walmart_nutrition_information: list[dict[str, Any]] | None = Field(default=None, description="Nutrition information on Walmart")
    walmart_ingredients_full: list[dict[str, str]] | None = Field(default=None, description="Full list of ingredients of product on Walmart")

    created_at: datetime | None = Field(default=None, description="Timestamp of when the product data was crawled.")
    updated_at: datetime | None = Field(default=None, description="Timestamp of when the product data was last updated.")
