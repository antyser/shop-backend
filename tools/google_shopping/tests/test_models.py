import pytest

from tools.google_shopping.models import (
    GoogleProductOffersResponse,
    GoogleProductResponse,
    GoogleProductReviewsResponse,
    GoogleProductSpecsResponse,
    GoogleShoppingResponse,
)


@pytest.fixture
def shopping_response_data():
    return {
        "search_metadata": {
            "id": "123",
            "status": "Success",
            "created_at": "2024-03-20",
            "request_time_taken": 1.2,
            "parsing_time_taken": 0.3,
            "total_time_taken": 1.5,
            "request_url": "https://example.com",
            "html_url": "https://example.com/html",
            "json_url": "https://example.com/json",
        },
        "search_parameters": {
            "engine": "google_shopping",
            "q": "laptop",
            "location": "United States",
            "location_used": "United States",
            "google_domain": "google.com",
            "hl": "en",
            "gl": "us",
        },
        "shopping_results": [
            {
                "position": 1,
                "title": "Test Laptop",
                "link": "https://example.com/product",
                "product_id": "12345",
                "price": "$999.99",
                "extracted_price": 999.99,
                "currency": "USD",
                "merchant": {"name": "Test Store", "link": "https://example.com"},
                "thumbnail": "https://example.com/thumb.jpg",
                "rating": 4.5,
                "reviews": 100,
                "extensions": ["Free shipping"],
                "tag": "Sponsored",
            }
        ],
    }


@pytest.fixture
def product_offers_data():
    return {
        "search_metadata": {"id": "123", "status": "Success"},
        "offers": [
            {
                "position": 1,
                "link": "https://example.com/offer",
                "price": "$999.99",
                "extracted_price": 999.99,
                "merchant": {"name": "Test Store", "badge": "Verified"},
            }
        ],
    }


@pytest.fixture
def product_reviews_data():
    return {
        "search_metadata": {"id": "123", "status": "Success"},
        "review_results": {
            "reviews": [
                {
                    "username": "TestUser",
                    "source": "Verified Purchase",
                    "title": "Great product",
                    "date": "2024-03-20",
                    "rating": 5,
                    "text": "Amazing product!",
                    "likes": 10,
                    "helpful_votes": 8,
                }
            ]
        },
    }


def test_shopping_response_serialization(shopping_response_data):
    # Convert dict to model
    model = GoogleShoppingResponse(**shopping_response_data)

    # Convert model back to dict
    model_dict = model.model_dump(exclude_none=True)

    # Compare original and resulting dictionaries
    assert model_dict == shopping_response_data


def test_product_offers_serialization(product_offers_data):
    # Convert dict to model
    model = GoogleProductOffersResponse(**product_offers_data)

    # Convert model back to dict
    model_dict = model.model_dump(exclude_none=True)

    # Compare original and resulting dictionaries
    assert model_dict == product_offers_data


def test_product_reviews_serialization(product_reviews_data):
    # Convert dict to model
    model = GoogleProductReviewsResponse(**product_reviews_data)

    # Convert model back to dict
    model_dict = model.model_dump(exclude_none=True)

    # Compare original and resulting dictionaries
    assert model_dict == product_reviews_data


def test_shopping_response_validation():
    # Test with invalid data
    invalid_data = {
        "search_metadata": {
            "id": 123,  # Should be string
            "request_time_taken": "invalid",  # Should be float
        }
    }

    with pytest.raises(ValueError):
        GoogleShoppingResponse(**invalid_data)


def test_optional_fields():
    # Test with minimal data
    minimal_data = {"search_metadata": {"id": "123"}}

    # Should not raise any exceptions
    model = GoogleShoppingResponse(**minimal_data)
    assert model.search_metadata.id == "123"
    assert model.shopping_results is None


def test_nested_model_validation():
    # Test nested model validation
    data = {
        "search_metadata": {"id": "123"},
        "shopping_results": [
            {
                "position": 1,
                "extracted_price": 999.99,
                "rating": "invalid",  # Should be float
            }
        ],
    }

    with pytest.raises(ValueError):
        GoogleShoppingResponse(**data)
