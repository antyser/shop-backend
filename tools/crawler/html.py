import asyncio
import os
from enum import Enum
from pathlib import Path

import httpx
from fake_headers import Headers
from loguru import logger
from markdownify import markdownify as md


class OutputFormat(str, Enum):
    """Output format options for HTML content"""

    HTML = "html"
    MARKDOWN = "markdown"


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


async def fetch_direct(url: str) -> str | None:
    """
    Fetch content directly using httpx with HTTP/2 support

    Args:
        url: Target URL to fetch

    Returns:
        HTML content if successful, None otherwise
    """
    try:
        headers = Headers(browser="chrome", os="windows", headers=True).generate()

        async with httpx.AsyncClient(http2=True, timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            logger.debug(f"Response headers: {response.headers}")
            logger.info(f"Response encoding: {response.encoding}")

            return str(response.text)

    except httpx.HTTPError as e:
        logger.error(f"Direct request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Direct request error: {e}", exc_info=True)
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
        headers = {
            "Authorization": f'Bearer {os.getenv("SPIDER_API_KEY")}',
            "Content-Type": "application/json",
        }

        json_data = {"url": url}

        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.spider.cloud/crawl", headers=headers, json=json_data, timeout=30.0)
            response.raise_for_status()

            result = response.json()
            if not result or not isinstance(result, list):
                logger.error("Invalid Spider API response format")
                return None

            content = result[0].get("content")
            if not content:
                logger.error("No content in Spider API response")
                return None

            return str(content)

    except httpx.HTTPError as e:
        logger.error(f"Spider API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Spider API error: {e}", exc_info=True)
        return None


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
        HTML or markdown content if successful, None otherwise
    """

    # TODO: spider api has batch mode and markdown parsing. Need benchmark against our own implementation.
    try:
        logger.info(f"Fetching content from {'Spider API' if use_external_crawler else 'direct request'}: " f"{url}")

        # Fetch content using appropriate method
        content = await fetch_with_spider(url) if use_external_crawler else await fetch_direct(url)

        if not content:
            logger.error("No content received")
            return None

        logger.info(f"Successfully decoded {len(content)} characters")

        if output_format == OutputFormat.MARKDOWN:
            markdown_content = html_to_markdown(content)
            if save_debug:
                save_debug_files(url, content, markdown_content)
            return markdown_content

        if save_debug:
            save_debug_files(url, content, None)
        return content

    except Exception as e:
        logger.error(f"Unexpected error while fetching {url}: {str(e)}", exc_info=True)
        return None


def html_to_markdown(html_content: str) -> str | None:
    """
    Convert HTML content to markdown format using markdownify

    Args:
        html_content: Raw HTML string to convert

    Returns:
        Markdown formatted string if successful, None otherwise

    Raises:
        ValueError: If html_content is empty or invalid
    """
    if not html_content:
        logger.error("Empty HTML content provided")
        return None

    try:
        logger.info("Starting HTML to markdown conversion")
        logger.debug(f"HTML content length: {len(html_content)}")

        # Convert HTML to markdown using markdownify
        markdown_content = md(
            html_content,
            heading_style="ATX",  # Use # style headings
            bullets="*",  # Use * for unordered lists
            strip=["img"],  # Remove img tags
            strong_em_symbol="*",  # Use * for bold/italic
            escape_asterisks=True,
            escape_underscores=True,
            code_language="",
            newline_style="SPACES",
        )

        logger.info(f"Conversion complete. Markdown length: {len(markdown_content)}")

        return markdown_content if markdown_content else None

    except Exception as e:
        logger.error(f"Failed to convert HTML to markdown: {str(e)}", exc_info=True)
        return None


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
        urls: List of target URLs to fetch
        output_format: Desired output format
        save_debug: Whether to save debug files
        use_external_crawler: Whether to use Spider API
        max_concurrent: Maximum concurrent requests

    Returns:
        Dictionary mapping URLs to their content
    """
    results: dict[str, str | None] = {}

    # Process URLs in batches to limit concurrency
    for i in range(0, len(urls), max_concurrent):
        batch = urls[i : i + max_concurrent]
        tasks = [fetch(url, output_format, save_debug, use_external_crawler) for url in batch]

        # Wait for batch completion
        batch_results = await asyncio.gather(*tasks)

        # Map results to URLs
        results.update(dict(zip(batch, batch_results, strict=False)))

        logger.info(f"Completed batch {i//max_concurrent + 1}, " f"processed {len(results)}/{len(urls)} URLs")

    return results
