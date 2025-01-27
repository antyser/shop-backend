import unittest
import json
from amazon_scraper import parse_amazon_product_page, AmazonProductContent

class TestAmazonScraper(unittest.TestCase):

    def test_parse_amazon_product_page(self):
        with open('amazon_product_data.json', 'r') as f:
            json_content = f.read()
        parsed_content = parse_amazon_product_page(json_content)
        self.assertEqual(len(parsed_content), 1)
        product = parsed_content[0]
        self.assertEqual(product['url'], 'https://www.amazon.com/Finebee-Unicorn-Stuffed-Birthday-Valentines/dp/B0CPP5PKR8')
        self.assertIsNotNone(product['title'])
        self.assertIsNotNone(product['price'])

    def test_parse_amazon_product_page_no_results(self):
        json_content = '{"results": []}'
        parsed_content = parse_amazon_product_page(json_content)
        self.assertEqual(len(parsed_content), 0)

    def test_parse_amazon_product_page_invalid_json(self):
        json_content = 'invalid json'
        parsed_content = parse_amazon_product_page(json_content)
        self.assertEqual(len(parsed_content), 0)

if __name__ == '__main__':
    unittest.main()