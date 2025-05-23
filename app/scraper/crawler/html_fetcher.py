import asyncio
import re
from enum import Enum
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

import chardet
import html5lib
import httpx
import logfire
from fake_headers import Headers
from loguru import logger

from app.config import get_settings
from app.llm.func.summarizer import generate_summary
from app.scraper.oxylabs.universal.scraper import fetch_universal
from app.scraper.reddit.json_parser import convert_reddit_json_to_markdown
from app.scraper.youtube.transcript import aget_transcript
from app.utils.counter import crawler_counter


class OutputFormat(str, Enum):
    """Output format options for HTML content"""

    HTML = "html"
    MARKDOWN = "markdown"
    SUMMARY = "summary"


def save_debug_files(url: str, html: str, markdown: str | None) -> None:
    """
    Save HTML and markdown content to debug files

    Args:
        url: Source URL for naming
        html: HTML content
        markdown: Markdown content
    """
    # Create debug directory if not exists
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)

    # Create safe filename from URL
    safe_name = "".join(c if c.isalnum() else "_" for c in url.split("//")[-1])[:100]

    # Save HTML content
    html_path = debug_dir / f"{safe_name}.html"
    html_path.write_text(html, encoding="utf-8")

    # Save markdown content if available
    if markdown:
        md_path = debug_dir / f"{safe_name}.md"
        md_path.write_text(markdown, encoding="utf-8")

    logger.info(f"Debug files saved for {url}")


def autodetect(content: bytes) -> str:
    """
    Detect character encoding of content using chardet

    Args:
        content: Bytes to analyze

    Returns:
        Detected encoding or 'utf-8' as fallback
    """
    result = chardet.detect(content)
    return result.get("encoding") or "utf-8"


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
            default_encoding=autodetect,
        ) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            content = str(response.text)
            crawler_counter.add(1, {"type": "direct", "status": "success", "status_code": response.status_code})
            return content

    except httpx.HTTPStatusError as e:
        # HTTPStatusError always has a response
        logger.error(f"Direct request failed with status {e.response.status_code}: {e}")
        crawler_counter.add(1, {"type": "direct", "status": "error", "error": "http", "status_code": e.response.status_code})
        return None
    except httpx.HTTPError as e:
        # Other HTTP errors may not have a response
        logger.error(f"Direct request failed: {e}")
        crawler_counter.add(1, {"type": "direct", "status": "error", "error": "http"})
        return None
    except Exception as e:
        logger.error(f"Direct request error: {e}", exc_info=True)
        crawler_counter.add(1, {"type": "direct", "status": "error", "error": "unknown"})
        return None


async def fetch_with_spider(url: str) -> str | None:
    """
    Fetch content using Spider API

    Args:
        url: Target URL to fetch

    Returns:
        HTML content if successful, None otherwise
    """
    try:
        settings = get_settings()
        spider_api_key = settings.SPIDER_API_KEY
        if not spider_api_key:
            raise ValueError("SPIDER_API_KEY not found in settings")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {spider_api_key}",
        }

        json_data = {"url": url}

        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.spider.cloud/crawl", headers=headers, json=json_data, timeout=30.0)
            response.raise_for_status()

            result = response.json()
            if not result or not isinstance(result, list):
                logger.error("Invalid Spider API response format")
                crawler_counter.add(1, {"type": "spider", "status": "error", "error": "format"})
                return None

            content = result[0].get("content")
            if not content:
                logger.error("No content in Spider API response")
                crawler_counter.add(1, {"type": "spider", "status": "error", "error": "empty"})
                return None

            crawler_counter.add(1, {"type": "spider", "status": "success"})
            return str(content)

    except httpx.HTTPError as e:
        logger.error(f"Spider API request failed: {e}")
        crawler_counter.add(1, {"type": "spider", "status": "error", "error": "http"})
        return None
    except Exception as e:
        logger.error(f"Spider API error: {e}", exc_info=True)
        crawler_counter.add(1, {"type": "spider", "status": "error", "error": "unknown"})
        return None


def sanitize_markdown_links(markdown: str) -> str:
    """
    Remove external links from markdown content while preserving text

    Args:
        markdown: Markdown content with links

    Returns:
        Markdown content with links removed
    """
    if markdown is None:
        return None

    # Replace markdown links with just the text
    link_pattern = r"\[([^\]]+)\]\([^)]+\)"
    sanitized = re.sub(link_pattern, r"\1", markdown)

    # Replace bare URLs with empty string
    url_pattern = r"https?://\S+"
    sanitized = re.sub(url_pattern, "", sanitized)

    return sanitized


async def fetch(
    url: str, output_format: OutputFormat = OutputFormat.MARKDOWN, save_debug: bool = False, use_external_crawler: bool = False
) -> str | None:
    """
    Download HTML content from URL with proper error handling

    Args:
        url: Target URL to fetch
        output_format: Desired output format
        save_debug: Whether to save debug files
        use_external_crawler: Whether to use Spider API

    Returns:
        HTML, markdown, or summary content if successful, None otherwise
    """
    try:
        logger.info(f"Fetching content from {'Spider API' if use_external_crawler else 'direct request'}: {url}")

        # Fetch content using appropriate method
        content = await fetch_with_spider(url) if use_external_crawler else await fetch_direct(url)

        if not content:
            # If direct fetch failed, try to get status code for better debugging
            if not use_external_crawler:
                try:
                    async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                        response = await client.get(url)
                        logger.error(f"Failed to fetch content from {url} (HTTP Status: {response.status_code})")
                except Exception as e:
                    logger.error(f"Failed to fetch content from {url} (Error: {str(e)})")
            else:
                logger.error(f"Failed to fetch content from {url} using Spider API")
            return None

        # Convert to markdown first if needed
        if output_format in (OutputFormat.MARKDOWN, OutputFormat.SUMMARY):
            markdown_content = html_to_markdown(content)
            if not markdown_content:
                logger.error("Failed to convert HTML to markdown")
                return None

            if save_debug:
                save_debug_files(url, content, markdown_content)

            # Generate summary if requested
            if output_format == OutputFormat.SUMMARY:
                return await generate_summary(markdown_content)  # type: ignore

            return markdown_content

        if save_debug:
            save_debug_files(url, content, None)
        return content

    except Exception as e:
        logger.error(f"Unexpected error while fetching {url}: {str(e)}", exc_info=True)
        return None


def html_to_markdown(html_content: str) -> str | None:
    """
    Convert HTML content to markdown format, preserving important content and structure
    while removing unnecessary elements.

    Args:
        html_content: Raw HTML string to convert

    Returns:
        Markdown formatted string or None if conversion fails
    """
    if not html_content:
        return None

    try:
        document = html5lib.parse(html_content)
        result = []
        seen_texts = set()  # To avoid duplicates

        def should_skip_element(elem: Element) -> bool:
            """Check if the element should be skipped."""
            tag_str = str(elem.tag)
            # Skip common non-content elements
            skip_tags = {
                "{http://www.w3.org/1999/xhtml}script",
                "{http://www.w3.org/1999/xhtml}style",
                "{http://www.w3.org/1999/xhtml}nav",
                "{http://www.w3.org/1999/xhtml}footer",
                "{http://www.w3.org/1999/xhtml}header",
                "{http://www.w3.org/1999/xhtml}aside",
            }
            if tag_str in skip_tags:
                return True

            if not any(text.strip() for text in elem.itertext()):
                return True

            return False

        def get_heading_level(tag: str) -> int:
            """Get markdown heading level from HTML heading tag."""
            tag_str = str(tag)
            if (
                not tag_str.endswith("}h1")
                and not tag_str.endswith("}h2")
                and not tag_str.endswith("}h3")
                and not tag_str.endswith("}h4")
                and not tag_str.endswith("}h5")
                and not tag_str.endswith("}h6")
            ):
                return 0
            return int(tag_str[-1])

        def process_element(elem: Any, depth: int = 0) -> None:
            """Process an element and its children recursively."""
            if should_skip_element(elem):
                return

            # Handle text content
            if hasattr(elem, "text") and elem.text:
                text = elem.text.strip()
                if text and text not in seen_texts:
                    prefix = ""
                    tag_str = str(elem.tag)

                    # Handle headings
                    heading_level = get_heading_level(tag_str)
                    if heading_level > 0:
                        prefix = "#" * heading_level + " "

                    # Handle lists
                    elif tag_str.endswith("}li"):
                        prefix = "* "

                    # Handle links
                    if tag_str == "{http://www.w3.org/1999/xhtml}a":
                        href = None
                        for attr, value in elem.attrib.items():
                            if str(attr).endswith("href"):
                                href = value
                                break
                        if href and not str(href).startswith(("#", "javascript:", "mailto:")):
                            result.append("  " * depth + prefix + f"[{text}]({href})")
                            seen_texts.add(text)
                            return

                    # Handle emphasis
                    elif tag_str.endswith("}strong") or tag_str.endswith("}b"):
                        text = f"**{text}**"
                    elif tag_str.endswith("}em") or tag_str.endswith("}i"):
                        text = f"*{text}*"

                    # Add text with appropriate prefix
                    result.append("  " * depth + prefix + text)
                    seen_texts.add(text)

            # Process children
            for child in elem:
                process_element(child, depth + 1)

            # Handle tail text
            if hasattr(elem, "tail") and elem.tail:
                tail = elem.tail.strip()
                if tail and tail not in seen_texts:
                    result.append("  " * depth + tail)
                    seen_texts.add(tail)

        # Find main content area if possible
        main_content = (
            document.find(".//{http://www.w3.org/1999/xhtml}main")
            or document.find(".//{http://www.w3.org/1999/xhtml}article")
            or document.find(".//{http://www.w3.org/1999/xhtml}body")
        )

        if main_content is not None:
            process_element(main_content)
        else:
            # Fallback to processing the entire document
            process_element(document)

        # Filter out unwanted content
        filtered_result = []
        for line in result:
            # Skip lines that are likely to be noise
            skip_patterns = {
                "var ",
                "function()",
                ".js",
                ".css",
                "google-analytics",
                "disqus",
                "{",
                "}",
                "undefined",
                "null",
                "NaN",
                "cookie",
                "privacy policy",
                "terms of service",
                "all rights reserved",
                "copyright ©",
            }
            if not any(pattern in str(line).lower() for pattern in skip_patterns):
                filtered_result.append(line)

        # Clean up the result
        markdown = "\n".join(filtered_result)

        # Remove excessive newlines
        markdown = "\n".join(line for line in markdown.splitlines() if line.strip())

        # Ensure proper spacing between sections
        markdown = markdown.replace("\n\n\n", "\n\n")

        return markdown

    except Exception as e:
        logger.error(f"Error converting HTML to markdown: {str(e)}")
        return None


def extract_youtube_id(url: str) -> str | None:
    """
    Extracts the YouTube video ID from a given URL.

    Args:
        url: The YouTube URL.

    Returns:
        The video ID if found, otherwise None.
    """
    if "youtube.com/watch?v=" in url:
        return url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("/")[-1]
    return None


def convert_reddit_url_to_json(url: str) -> str:
    """Convert a Reddit URL to its JSON API equivalent.

    Args:
        url: Reddit URL

    Returns:
        JSON API URL
    """
    # Remove trailing slash if present
    if url.endswith("/"):
        url = url[:-1]

    # Add .json extension if not already present
    if not url.endswith(".json"):
        url = f"{url}.json"

    return url


async def fetch_batch(
    urls: list[str],
    output_format: OutputFormat = OutputFormat.MARKDOWN,
    save_debug: bool = True,
    use_external_crawler: bool = False,
    max_concurrent: int = 20,
) -> dict[str, str | None]:
    """
    Download HTML content from multiple URLs concurrently

    Args:
        urls: List of URLs to fetch
        output_format: Desired output format
        save_debug: Whether to save debug files
        use_external_crawler: Whether to use Spider API
        max_concurrent: Maximum number of concurrent requests

    Returns:
        Dictionary mapping URLs to their content
    """
    results: dict[str, str | None] = {}

    # Process URLs in batches to limit concurrency
    for i in range(0, len(urls), max_concurrent):
        batch = urls[i : i + max_concurrent]
        tasks = []

        for url in batch:
            youtube_id = extract_youtube_id(url)
            if youtube_id:
                # Call transcript function for YouTube links
                tasks.append(aget_transcript(youtube_id))
            elif "reddit.com" in url:
                # Convert Reddit URL to JSON API URL and fetch with universal fetcher
                json_url = convert_reddit_url_to_json(url)
                logger.info(f"Converting Reddit URL to JSON API: {url} -> {json_url}")
                tasks.append(fetch_universal(json_url))
            else:
                # Fetch HTML content for non-YouTube links
                tasks.append(fetch(url, output_format, save_debug, use_external_crawler))

        # Wait for batch completion
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results to URLs
        for url, result in zip(batch, batch_results, strict=False):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {url}: {str(result)}")
                results[url] = None
            elif "reddit.com" in url and isinstance(result, str):
                # Process Reddit JSON content
                try:
                    markdown = convert_reddit_json_to_markdown(result)
                    # Remove links from Reddit markdown
                    markdown = sanitize_markdown_links(markdown)
                    results[url] = markdown
                except Exception as e:
                    logger.error(f"Failed to convert Reddit JSON to markdown: {e}")
                    results[url] = None
            else:
                # Remove links from regular markdown content
                if isinstance(result, str) and output_format == OutputFormat.MARKDOWN:
                    result = sanitize_markdown_links(result)
                results[url] = result

    return results


if __name__ == "__main__":
    import asyncio

    logfire.configure()

    # Test Reddit URL
    reddit_url = "https://www.travelandleisure.com/best-samsonite-luggage-6835399"
    results = asyncio.run(fetch_batch(urls=[reddit_url], output_format=OutputFormat.MARKDOWN, save_debug=True))

    # Print results
    for url, content in results.items():
        if content:
            logger.info(f"Successfully fetched {url}")
            logger.info(f"Content :\n{content}")
        else:
            logger.error(f"Failed to fetch {url}")
