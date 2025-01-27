import pytest
from .models import AmazonProductContent, parse_amazon_product_page
import requests

def test_parse_amazon_product_page_aquaphor():
    url = "https://www.amazon.com/Aquaphor-Advanced-Therapy-Ointment-Protectant/dp/B0107QP1VE"
    response = requests.get(url)
    response.raise_for_status()
    html = response.text
    product = parse_amazon_product_page(html)
    assert product.title is not None
    assert "Aquaphor" in product.title
    assert product.price == 11.02
    assert product.description is not None
    assert product.images is not None
    assert product.brand == "Visit the Aquaphor Store"

def test_parse_amazon_product_page_stanley():
    url = "https://www.amazon.com/Quencher-FlowState-Stainless-Insulated-Smoothie/dp/B0CRMWHW47/"
    response = requests.get(url)
    response.raise_for_status()
    html = response.text
    product = parse_amazon_product_page(html)
    assert product.title is not None
    assert "Stanley" in product.title
    assert product.price == 26.82
    assert product.description is not None
    assert product.images is not None
    assert product.brand == "Visit the STANLEY Store"

def test_parse_amazon_product_page_empty_fields():
    html = "<html><body></body></html>"
    product = parse_amazon_product_page(html)
    assert product.title is None
    assert product.price is None
    assert product.description is None
    assert product.images is None
    assert product.brand is None
    assert product.asin is None