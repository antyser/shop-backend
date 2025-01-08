import json
from pathlib import Path

import pytest

from tools.google_shopping.models import (
    GoogleProductOffersResponse,
    GoogleProductResponse,
    GoogleProductReviewsResponse,
    GoogleProductSpecsResponse,
    GoogleShoppingResponse,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def shopping_response_data():
    with open(FIXTURES_DIR / "shopping_response.json") as f:
        return json.load(f)


@pytest.fixture
def product_offers_data():
    with open(FIXTURES_DIR / "product_offers.json") as f:
        return json.load(f)


@pytest.fixture
def product_reviews_data():
    with open(FIXTURES_DIR / "product_reviews.json") as f:
        return json.load(f)


@pytest.fixture
def product_specs_data():
    with open(FIXTURES_DIR / "product_specs.json") as f:
        return json.load(f)


@pytest.fixture
def product_details_data():
    with open(FIXTURES_DIR / "product_details.json") as f:
        return json.load(f)


def test_shopping_response_serialization(shopping_response_data):
    model = GoogleShoppingResponse(**shopping_response_data)
    model_dict = model.model_dump(exclude_none=True)
    assert model_dict == shopping_response_data


def test_product_offers_serialization(product_offers_data):
    model = GoogleProductOffersResponse(**product_offers_data)
    model_dict = model.model_dump(exclude_none=True)
    assert model_dict == product_offers_data


def test_product_reviews_serialization(product_reviews_data):
    model = GoogleProductReviewsResponse(**product_reviews_data)
    model_dict = model.model_dump(exclude_none=True)
    assert model_dict == product_reviews_data


def test_product_specs_serialization(product_specs_data):
    model = GoogleProductSpecsResponse(**product_specs_data)
    model_dict = model.model_dump(exclude_none=True)
    assert model_dict == product_specs_data


def test_product_details_serialization(product_details_data):
    model = GoogleProductResponse(**product_details_data)
    model_dict = model.model_dump(exclude_none=True)
    assert model_dict == product_details_data


def test_shopping_response_validation():
    invalid_data = {
        "search_metadata": {
            "id": 123,  # Should be string
            "request_time_taken": "invalid",  # Should be float
        }
    }

    with pytest.raises(ValueError):
        GoogleShoppingResponse(**invalid_data)


def test_optional_fields():
    minimal_data = {"search_metadata": {"id": "123"}}

    model = GoogleShoppingResponse(**minimal_data)
    assert model.search_metadata.id == "123"
    assert model.shopping_results is None


def test_nested_model_validation():
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
