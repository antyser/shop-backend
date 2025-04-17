"""
Utility functions for fetching content from various sources.
"""
import asyncio
import json
import os
import re
from typing import Optional

import httpx
from dotenv import load_dotenv
from loguru import logger
from fake_headers import Headers
from playwright.async_api import async_playwright

# API constants
JINA_API_URL = "https://r.jina.ai/"
JINA_API_KEY_ENV = "JINA_API_KEY"
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/scrape"
FIRECRAWL_API_KEY_ENV = "FIRECRAWL_API_KEY"
SPIDER_API_URL = "https://api.scrapingspider.com/spider"
SPIDER_API_KEY_ENV = "SPIDER_API_KEY"

# Playwright constants
PLAYWRIGHT_TIMEOUT = 30000  # 30 seconds in milliseconds
PLAYWRIGHT_WAIT_UNTIL = "networkidle"  # Wait until network is idle

def strip_html_tags(html_content: str) -> str:
    """
    Strip HTML tags from content and return only the text.
    
    Args:
        html_content: HTML content to strip
        
    Returns:
        Text content without HTML tags
    """
    # Check if the content is wrapped in HTML tags
    if html_content.startswith('<html') and html_content.endswith('</html>'):
        # Find the content inside <pre> tags which usually contains the JSON
        pre_match = re.search(r'<pre>(.*?)</pre>', html_content, re.DOTALL)
        if pre_match:
            return pre_match.group(1)
    
    # If no pre tags or not HTML, try to remove all HTML tags
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    return clean_text

async def fetch_with_playwright(url: str) -> Optional[str]:
    """
    Fetch content from a URL using Playwright browser automation.
    
    Args:
        url: URL to fetch
        
    Returns:
        HTML content or None if fetching failed
    """
    try:
        logger.info(f"Fetching {url} with Playwright")
        
        async with async_playwright() as p:
            # Launch a headless browser
            browser = await p.chromium.launch(headless=True)
            
            try:
                # Create a new page
                page = await browser.new_page()
                
                # Set user agent to avoid bot detection
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                })
                
                await page.goto(
                    url, 
                    timeout=PLAYWRIGHT_TIMEOUT,
                    wait_until=PLAYWRIGHT_WAIT_UNTIL
                )
            
                content = await page.content()
                
                if url.lower().endswith('.json'):
                    return strip_html_tags(content)
                
                return content
                
            finally:
                # Always close the browser
                await browser.close()
                
    except Exception as e:
        logger.error(f"Error fetching {url} with Playwright: {str(e)}")
        return None

async def fetch_with_spider(url: str) -> Optional[str]:
    """
    Fetch content from a URL using Spider API.
    
    Args:
        url: URL to fetch
        
    Returns:
        HTML content or None if fetching failed
    """
    # Load environment variables
    load_dotenv(override=True)
    
    # Get Spider API key from environment
    spider_api_key = os.getenv(SPIDER_API_KEY_ENV)
    if not spider_api_key:
        logger.error(f"{SPIDER_API_KEY_ENV} environment variable is not set")
        return None
    
    try:
        # Prepare the request URL and headers
        request_url = f"{SPIDER_API_URL}?api_key={spider_api_key}&url={url}"
        
        # Make the request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(request_url, timeout=60.0)
            
            if response.status_code != 200:
                logger.error(f"Spider API returned status code {response.status_code} for {url}")
                return None
            
            return response.text
    
    except httpx.RequestError as e:
        logger.error(f"HTTP request error fetching {url} with Spider: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url} with Spider: {str(e)}")
        return None

async def fetch_with_jina(url: str) -> Optional[str]:
    """
    Fetch content from a URL using Jina API with httpx.
    
    Args:
        url: URL to fetch
        
    Returns:
        Markdown content or None if fetching failed
    """
    # Load environment variables
    load_dotenv(override=True)
    
    # Get Jina API key from environment
    jina_api_key = os.getenv(JINA_API_KEY_ENV)
    if not jina_api_key:
        logger.error(f"{JINA_API_KEY_ENV} environment variable is not set")
        return None
    
    try:
        # Prepare the request URL and headers
        request_url = f"{JINA_API_URL}{url}"
        headers = {
            "Authorization": f"Bearer {jina_api_key}"
        }
        
        # Make the request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(request_url, headers=headers, timeout=30.0)
            
            if response.status_code != 200:
                logger.error(f"Jina API returned status code {response.status_code} for {url}")
                return None
            
            # Parse the response
            text = response.text
            
            # Extract markdown content
            markdown_marker = "Markdown Content:"
            if markdown_marker in text:
                # Get everything after the markdown marker
                markdown_content = text.split(markdown_marker, 1)[1].strip()
                return markdown_content
            else:
                logger.warning(f"No markdown content found in Jina response for {url}")
                return text  # Return the full response if no markdown marker
    
    except httpx.RequestError as e:
        logger.error(f"HTTP request error fetching {url} with Jina: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url} with Jina: {str(e)}")
        return None

async def fetch_with_firecrawl(url: str) -> Optional[str]:
    """
    Fetch content from a URL using Firecrawl API.
    
    Args:
        url: URL to fetch
        
    Returns:
        Markdown content or None if fetching failed
    """
    # Load environment variables
    load_dotenv(override=True)
    
    # Get Firecrawl API key from environment
    firecrawl_api_key = os.getenv(FIRECRAWL_API_KEY_ENV)
    if not firecrawl_api_key:
        logger.error(f"{FIRECRAWL_API_KEY_ENV} environment variable is not set")
        return None
    
    try:
        # Prepare the request headers and payload
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {firecrawl_api_key}"
        }
        
        payload = {
            "url": url,
            "formats": ["markdown"]
        }
        
        # Make the request using httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                FIRECRAWL_API_URL, 
                headers=headers, 
                json=payload, 
                timeout=60.0
            )
            
            if response.status_code != 200:
                logger.error(f"Firecrawl API returned status code {response.status_code} for {url}")
                return None
            
            # Parse the JSON response
            response_data = response.json()
            
            # Extract markdown content from the response
            if "data" in response_data and "markdown" in response_data["data"]:
                return response_data["data"]["markdown"]
            else:
                logger.warning(f"No markdown content found in Firecrawl response for {url}")
                return json.dumps(response_data)  # Return the full response as JSON string
    
    except httpx.RequestError as e:
        logger.error(f"HTTP request error fetching {url} with Firecrawl: {str(e)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in Firecrawl response for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error fetching {url} with Firecrawl: {str(e)}")
        return None 
    

async def fetch_direct(url: str) -> str | None:
    """
    Fetch content directly using httpx with HTTP/2 support
    and automatic encoding detection

    Args:
        url: Target URL to fetch

    Returns:
        HTML content if successful, None otherwise
    """
    try:
        headers = Headers(browser="chrome", os="windows", headers=True).generate()
        headers["Accept-Encoding"] = "br"

        async with httpx.AsyncClient(
            http2=True,
            timeout=10.0,
            follow_redirects=True,
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            content = str(response.text)
            return content

    except httpx.HTTPStatusError as e:
        # HTTPStatusError always has a response
        logger.error(f"Direct request failed with status {e.response.status_code}: {e}")
        return None
    except httpx.HTTPError as e:
        # Other HTTP errors may not have a response
        logger.error(f"Direct request failed: {e} {url}")
        return None
    except Exception as e:
        logger.error(f"Direct request error: {e} {url}")
        return None
