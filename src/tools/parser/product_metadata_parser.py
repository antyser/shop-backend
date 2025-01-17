import json

from bs4 import BeautifulSoup
from loguru import logger
from tools.parser.models.product_metadata import ProductMetadata


def extract_json_ld(soup: BeautifulSoup) -> ProductMetadata | None:
    """Extract product metadata from JSON-LD script tags"""
    script_tag = soup.find("script", {"type": "application/ld+json"})
    if not script_tag:
        return None

    try:
        data = json.loads(script_tag.string)
        if data.get("@type") != "Product":
            return None

        # Normalize image field
        if "image" in data:
            if isinstance(data["image"], str):
                data["image"] = [data["image"]]
            elif isinstance(data["image"], dict):
                data["image"] = [data["image"].get("url", "")]

        # Normalize offers field
        if "offers" in data:
            if isinstance(data["offers"], dict):
                if data["offers"].get("@type") == "AggregateOffer":
                    data["offers"] = data["offers"].get("offers", [])
                else:
                    data["offers"] = [data["offers"]]

        # Handle empty review string
        if "review" in data and data["review"] == "":
            data["review"] = []
        # Transform the review data if it exists and is not empty
        elif "review" in data:
            review_data = data["review"]
            if not isinstance(review_data, list):
                review_data = [review_data]

            # Transform each review's author from object to string
            for review in review_data:
                if isinstance(review.get("author"), dict):
                    review["author"] = review["author"].get("name")

            data["review"] = review_data

        metadata = ProductMetadata.model_validate(data)
        return metadata if isinstance(metadata, ProductMetadata) else None
    except Exception as e:
        logger.error(f"Error parsing JSON-LD: {str(e)}\nData: {json.dumps(data, indent=2)}")
        return None


def extract_rdfa(soup: BeautifulSoup) -> ProductMetadata | None:
    """Extract product metadata from RDFa markup"""
    product_div = soup.find(attrs={"typeof": "schema:Product"})
    if not product_div:
        return None

    try:
        # Find product name and description directly under product div
        name_div = product_div.find(attrs={"property": "schema:name"}, recursive=False)
        desc_div = product_div.find(attrs={"property": "schema:description"}, recursive=False)

        data = {
            "name": name_div["content"] if name_div else None,
            "description": desc_div["content"] if desc_div else None,
        }

        # Extract aggregate rating
        agg_rating_div = product_div.find(attrs={"typeof": "schema:AggregateRating"})
        if agg_rating_div:
            data["aggregateRating"] = {
                "ratingValue": float(agg_rating_div.find(attrs={"property": "schema:ratingValue"})["content"]),
                "reviewCount": int(agg_rating_div.find(attrs={"property": "schema:reviewCount"})["content"]),
            }

        # Extract review
        review_div = product_div.find(attrs={"typeof": "schema:Review"})
        if review_div:
            author_div = review_div.find(attrs={"typeof": "schema:Person"})
            author_name = author_div.find(attrs={"property": "schema:name"})["content"] if author_div else None

            rating_div = review_div.find(attrs={"typeof": "schema:Rating"})
            if rating_div:
                review_data = {
                    "author": author_name,
                    "reviewRating": {
                        "ratingValue": float(rating_div.find(attrs={"property": "schema:ratingValue"})["content"]),
                        "bestRating": float(rating_div.find(attrs={"property": "schema:bestRating"})["content"]),
                    },
                }
                data["review"] = [review_data]

        metadata = ProductMetadata.model_validate(data)
        return metadata if isinstance(metadata, ProductMetadata) else None
    except Exception as e:
        logger.error(f"Error parsing RDFa: {e}")
        return None


def extract_microdata(soup: BeautifulSoup) -> ProductMetadata | None:
    """Extract product metadata from Microdata markup"""
    product_div = soup.find(attrs={"itemtype": "https://schema.org/Product"})
    if not product_div:
        return None

    try:
        data = {
            "name": product_div.find(attrs={"itemprop": "name"})["content"],
            "description": product_div.find(attrs={"itemprop": "description"})["content"],
        }

        # Extract aggregate rating
        agg_rating_div = product_div.find(attrs={"itemtype": "https://schema.org/AggregateRating"})
        if agg_rating_div:
            data["aggregateRating"] = {
                "ratingValue": float(agg_rating_div.find(attrs={"itemprop": "ratingValue"})["content"]),
                "reviewCount": int(agg_rating_div.find(attrs={"itemprop": "reviewCount"})["content"]),
            }

        # Extract review
        review_div = product_div.find(attrs={"itemtype": "https://schema.org/Review"})
        if review_div:
            author_name = review_div.find(attrs={"itemtype": "https://schema.org/Person"}).find(attrs={"itemprop": "name"})["content"]
            rating_div = review_div.find(attrs={"itemtype": "https://schema.org/Rating"})

            review_data = {
                "author": author_name,  # Use the name string directly
                "reviewRating": {
                    "ratingValue": float(rating_div.find(attrs={"itemprop": "ratingValue"})["content"]),
                    "bestRating": float(rating_div.find(attrs={"itemprop": "bestRating"})["content"]),
                },
            }
            data["review"] = [review_data]

        metadata = ProductMetadata.model_validate(data)
        return metadata if isinstance(metadata, ProductMetadata) else None
    except Exception as e:
        logger.error(f"Error parsing Microdata: {e}")
        return None


def extract_product_metadata(html: str) -> ProductMetadata | None:
    """Extract product metadata from HTML using various formats"""
    soup = BeautifulSoup(html, "html.parser")

    # Try each format in order of preference
    metadata = extract_json_ld(soup) or extract_rdfa(soup) or extract_microdata(soup)
    return metadata
