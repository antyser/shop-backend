import asyncio
import json
import os
import re
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from xml.etree.ElementTree import Element

import chardet
import html5lib
import httpx
import logfire
from loguru import logger

from app.config import get_settings
from app.scraper.crawler.fetch_utils import fetch_direct, fetch_with_jina, fetch_with_playwright
from app.scraper.oxylabs.universal.scraper import fetch_universal
from app.scraper.reddit.json_parser import convert_reddit_json_to_markdown
from app.scraper.youtube.transcript import aget_transcript
from app.utils.counter import crawler_counter


class OutputFormat(Enum):
    """Enum for different output formats"""
    RAW = "raw"
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
    url: str,
    output_format: OutputFormat = OutputFormat.MARKDOWN,
    save_debug: bool = True,
) -> str | None:
    """
    Fetch content from a URL, handling special cases based on URL type.
    
    Args:
        url: URL to fetch
        output_format: Desired output format
        save_debug: Whether to save debug files
        
    Returns:
        Processed content or None if fetching failed
    """
    try:
        # Handle YouTube URLs
        youtube_id = extract_youtube_id(url)
        if youtube_id:
            return await aget_transcript(youtube_id)
        
        # Handle Reddit URLs
        if "reddit.com" in url:
            json_url = convert_reddit_url_to_json(url)
            logger.info(f"Converting Reddit URL to JSON API: {url} -> {json_url}")
            content = await fetch_with_playwright(json_url)
            
            if isinstance(content, str):
                markdown = convert_reddit_json_to_markdown(content)
                return sanitize_markdown_links(markdown)
        
        content = await fetch_direct(url)
        
        if content is None:
            return None
            
        if output_format == OutputFormat.RAW:
            return content
        else:  # MARKDOWN
            result = html_to_markdown(content)
        
        # Save debug files if requested
        if save_debug:
            markdown_content = result if output_format == OutputFormat.MARKDOWN else None
            save_debug_files(url, content, markdown_content)
            
        return result
    
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
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
    max_concurrent: int = 20,
) -> dict[str, str | None]:
    """
    Download content from multiple URLs concurrently
    
    Args:
        urls: List of URLs to fetch
        output_format: Desired output format
        save_debug: Whether to save debug files
        max_concurrent: Maximum number of concurrent requests
        
    Returns:
        Dictionary mapping URLs to their content
    """
    results: dict[str, str | None] = {}
    
    # Process URLs in batches to limit concurrency
    for i in range(0, len(urls), max_concurrent):
        batch = urls[i : i + max_concurrent]
        
        # Create tasks for each URL in the batch
        tasks = [
            fetch(url, output_format, save_debug)
            for url in batch
        ]
        
        # Wait for batch completion
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to URLs
        for url, result in zip(batch, batch_results, strict=False):
            if isinstance(result, Exception):
                logger.error(f"Failed to fetch {url}: {str(result)}")
                results[url] = None
            else:
                results[url] = result
                
    return results


if __name__ == "__main__":
    import asyncio

    logfire.configure()

    # Test Reddit URL
    reddit_url = "https://www.reddit.com/r/buildapc/comments/18rqtmb/simple_whats_the_best_allround_gaming_mouse"
    result = asyncio.run(fetch(reddit_url))

    print(result)
