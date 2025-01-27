import json
from bs4 import BeautifulSoup
from typing import TypedDict, Optional, List

class AmazonProductContent(TypedDict):
    url: Optional[str]
    title: Optional[str]
    price: Optional[str]
    description: Optional[str]

def parse_amazon_product_page(json_content: str) -> List[AmazonProductContent]:
    try:
        data = json.loads(json_content)
        results = data.get('results', [])
        parsed_results = []
        for result in results:
            html_content = result.get('content')
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                title_element = soup.find('span', id='productTitle')
                title = title_element.text.strip() if title_element else None
                price_element = soup.find('span', class_='a-price-whole')
                price_fraction_element = soup.find('span', class_='a-price-fraction')
                price = (price_element.text.strip() + "." + price_fraction_element.text.strip()) if price_element and price_fraction_element else None
                description_element = soup.find('div', id='productDescription')
                description = description_element.text.strip() if description_element else None
                url = result.get('url')
                parsed_results.append(AmazonProductContent(url=url, title=title, price=price, description=description))
        return parsed_results
    except json.JSONDecodeError:
        return []