import os

import httpx
import requests
from fake_headers import Headers
from loguru import logger


def get_html_content(url: str) -> str | None:
    """Download HTML content from URL with proper error handling"""
    try:
        headers = Headers(browser="chrome", os="windows", headers=True).generate()

        # Using httpx with HTTP/2 support
        with httpx.Client(http2=True) as client:
            response = client.get(url, headers=headers, timeout=10.0, follow_redirects=True)
            response.raise_for_status()
            content = response.text
            return str(content) if content is not None else None
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch URL {url}: {str(e)}")
        return None


def get_html_content_spider(url: str) -> str | None:
    """Fetch HTML content using Spider API with proper error handling"""
    try:
        headers = {
            "Authorization": f'Bearer {os.getenv("SPIDER_API_KEY")}',
            "Content-Type": "application/json",
        }

        json_data = {"url": url}

        response = requests.post("https://api.spider.cloud/crawl", headers=headers, json=json_data)
        content = response.json()[0].get("content")
        return str(content) if content is not None else None
    except (requests.RequestException, IndexError, KeyError) as e:
        logger.error(f"Failed to fetch URL {url} using Spider API: {str(e)}")
        return None
