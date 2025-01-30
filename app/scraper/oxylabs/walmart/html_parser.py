"""Walmart HTML parser module."""

import json
from typing import Any

from bs4 import BeautifulSoup
from loguru import logger

from app.scraper.oxylabs.walmart.models import (
    Breadcrumb,
    Fulfillment,
    Location,
    Price,
    Rating,
    Seller,
    Specification,
    WalmartProductContent,
)


def extract_json_ld(soup: BeautifulSoup) -> dict[str, Any] | None:
    """Extract product data from JSON-LD script."""
    script = soup.find("script", {"type": "application/ld+json", "data-seo-id": "schema-org-product"})
    if not script:
        logger.warning("No JSON-LD script found")
        return None

    try:
        data = json.loads(script.string)
        if isinstance(data, list):
            data = data[0]
        if not isinstance(data, dict):
            logger.warning("Invalid JSON-LD data type")
            return None
        return data
    except (json.JSONDecodeError, AttributeError) as e:
        logger.error(f"Failed to parse JSON-LD: {e}")
        return None


def extract_price(soup: BeautifulSoup) -> Price:
    """Extract price information."""
    price_elem = soup.find("span", {"data-fs-element": "price"})
    if not price_elem:
        logger.warning("No price element found")
        return Price(price=0.0, currency="USD")

    try:
        # Extract price from text like "Now $129.99"
        price_text = price_elem.get_text(strip=True)
        price = float(price_text.split("$")[-1])
        return Price(price=price, currency="USD")
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse price: {e}")
        return Price(price=0.0, currency="USD")


def extract_rating(soup: BeautifulSoup, json_ld: dict[str, Any] | None = None) -> Rating:
    """Extract rating information."""
    if json_ld and "aggregateRating" in json_ld:
        try:
            rating_data = json_ld["aggregateRating"]
            return Rating(rating=float(rating_data.get("ratingValue", 0.0)), count=int(rating_data.get("reviewCount", 0)))
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse rating from JSON-LD: {e}")

    # Fallback to HTML
    try:
        rating_elem = soup.find("div", {"data-testid": "rating-stars"})
        count_elem = soup.find("div", {"data-testid": "review-count"})

        rating = float(rating_elem.get("aria-label", "0.0").split()[0]) if rating_elem else 0.0
        count = int(count_elem.get_text(strip=True).split()[0]) if count_elem else 0

        return Rating(rating=rating, count=count)
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse rating from HTML: {e}")
        return Rating(rating=0.0, count=0)


def extract_seller(soup: BeautifulSoup, json_ld: dict[str, Any] | None = None) -> Seller:
    """Extract seller information."""
    seller_elem = soup.find("div", {"data-testid": "seller-info"})
    if seller_elem:
        try:
            name = seller_elem.get_text(strip=True)
            return Seller(name=name)
        except AttributeError as e:
            logger.error(f"Failed to parse seller from HTML: {e}")

    # Fallback to default
    return Seller(name="Walmart")


def extract_location(soup: BeautifulSoup) -> Location:
    """Extract location information."""
    location_elem = soup.find("div", {"data-testid": "store-info"})
    if location_elem:
        try:
            # Parse location text (format may vary)
            return Location(city="", state="", store_id="", zip_code="")
        except Exception as e:
            logger.error(f"Failed to parse location: {e}")

    # Always return a Location object
    return Location(city="", state="", store_id="", zip_code="")


def extract_fulfillment(soup: BeautifulSoup) -> Fulfillment:
    """Extract fulfillment information."""
    fulfillment_elem = soup.find("div", {"data-test-id": "ilc-container"})
    if not fulfillment_elem:
        return Fulfillment(
            pickup=False,
            delivery=False,
            shipping=False,
            out_of_stock=True,
            free_shipping=False,
            pickup_information="Not available",
            delivery_information="Not available",
            shipping_information="Not available",
        )

    try:
        text = fulfillment_elem.get_text(strip=True)

        # Parse fulfillment options
        shipping = "Shipping" in text
        pickup = "Pickup" in text and "Not available" not in text
        delivery = "Delivery" in text and "Not available" not in text

        # Extract shipping information
        shipping_info = ""
        if shipping:
            shipping_parts = text.split("Shipping")[-1].split("Pickup")[0].strip()
            shipping_info = f"Shipping, {shipping_parts}"

        return Fulfillment(
            pickup=pickup,
            delivery=delivery,
            shipping=shipping,
            out_of_stock=not (pickup or delivery or shipping),
            free_shipping=False,  # Need to check if shipping is free
            pickup_information="Pickup, Not available" if not pickup else "",
            delivery_information="Delivery, Not available" if not delivery else "",
            shipping_information=shipping_info,
        )
    except Exception as e:
        logger.error(f"Failed to parse fulfillment: {e}")
        return Fulfillment(
            pickup=False,
            delivery=False,
            shipping=False,
            out_of_stock=True,
            free_shipping=False,
            pickup_information="Not available",
            delivery_information="Not available",
            shipping_information="Not available",
        )


def extract_breadcrumbs(soup: BeautifulSoup, json_ld: dict[str, Any] | None = None) -> list[Breadcrumb]:
    """Extract breadcrumb information."""
    breadcrumbs = []

    # Try JSON-LD first
    if json_ld and "breadcrumb" in json_ld:
        try:
            items = json_ld["breadcrumb"].get("itemListElement", [])
            for item in items:
                breadcrumbs.append(Breadcrumb(url=item.get("item", {}).get("@id", ""), category_name=item.get("name", "")))
            return breadcrumbs
        except (KeyError, AttributeError) as e:
            logger.error(f"Failed to parse breadcrumbs from JSON-LD: {e}")

    # Fallback to HTML
    nav = soup.find("nav", {"aria-label": "breadcrumb"})
    if nav:
        try:
            links = nav.find_all("a")
            for link in links:
                breadcrumbs.append(Breadcrumb(url=link.get("href", ""), category_name=link.get_text(strip=True)))
        except AttributeError as e:
            logger.error(f"Failed to parse breadcrumbs from HTML: {e}")

    return breadcrumbs


def extract_specifications(soup: BeautifulSoup, json_ld: dict[str, Any] | None = None) -> list[Specification]:
    """Extract product specifications."""
    specs = []

    # Try JSON-LD first
    if json_ld and "additionalProperty" in json_ld:
        try:
            for prop in json_ld["additionalProperty"]:
                specs.append(Specification(key=prop.get("name", ""), value=prop.get("value", "")))
            return specs
        except (KeyError, AttributeError) as e:
            logger.error(f"Failed to parse specifications from JSON-LD: {e}")

    # Fallback to HTML
    specs_div = soup.find("div", {"data-testid": "product-specs"})
    if specs_div:
        try:
            rows = specs_div.find_all("div", recursive=False)
            for row in rows:
                key = row.find("div", {"class": "key"})
                value = row.find("div", {"class": "value"})
                if key and value:
                    specs.append(Specification(key=key.get_text(strip=True), value=value.get_text(strip=True)))
        except AttributeError as e:
            logger.error(f"Failed to parse specifications from HTML: {e}")

    return specs


def parse_walmart_html(html_content: str) -> WalmartProductContent:
    """Parse Walmart product HTML and extract structured data."""
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract JSON-LD data first
    json_ld = extract_json_ld(soup)

    # Extract basic product information
    title_elem = soup.find("h1", {"data-fs-element": "name"})
    title = title_elem.get_text(strip=True) if title_elem else ""

    description_elem = soup.find("div", {"data-testid": "product-description"})
    description = description_elem.get_text(strip=True) if description_elem else ""

    brand_elem = soup.find("div", {"data-testid": "brand-info"})
    brand = brand_elem.get_text(strip=True) if brand_elem else ""

    # Extract structured data
    price = extract_price(soup)
    rating = extract_rating(soup, json_ld)
    seller = extract_seller(soup, json_ld)
    location = extract_location(soup)
    fulfillment = extract_fulfillment(soup)
    breadcrumbs = extract_breadcrumbs(soup, json_ld)
    specifications = extract_specifications(soup, json_ld)

    # Use JSON-LD data as fallback
    if json_ld:
        if not title and "name" in json_ld:
            title = json_ld["name"]
        if not description and "description" in json_ld:
            description = json_ld["description"]
        if not brand and "brand" in json_ld:
            brand = json_ld["brand"].get("name", "")

    return WalmartProductContent(
        title=title,
        description=description,
        brand=brand,
        price=price,
        rating=rating,
        seller=seller,
        location=location,
        fulfillment=fulfillment,
        breadcrumbs=breadcrumbs,
        specifications=specifications,
    )
