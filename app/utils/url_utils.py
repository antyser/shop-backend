"""
URL Utilities

This module provides functions for working with URLs, including sanitization
and deduplication.
"""

import re
from typing import List
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def sanitize_url(url: str) -> str:
    """
    Remove tracking parameters from a URL.
    
    Args:
        url: The URL to sanitize
        
    Returns:
        Sanitized URL with tracking parameters removed
    """
    if not url:
        return url
        
    # Parse the URL
    parsed_url = urlparse(url)
    
    # Get the query parameters
    query_params = parse_qs(parsed_url.query)
    
    # List of tracking parameters to remove
    tracking_params = [
        # Google Analytics and Ads
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'gclid', 'gclsrc', 'dclid', 'fbclid',
        
        # Amazon
        'tag', '_encoding', 'linkCode', 'linkId', 'camp', 'creative',
        
        # Other common tracking parameters
        'ref', 'ref_', 'referrer', 'srsltid', 'msclkid', 'zanpid', 'affid',
        '_hsenc', '_hsmi', 'mc_cid', 'mc_eid', 'yclid', 'igshid',
        
        # Social media
        'share', 'share_id', 'share_source', 'cmpid', 'twclid',
        
        # Other
        'trk', 'trkCampaign', 'sc_campaign', 'sc_channel', 'sc_content',
        'sc_medium', 'sc_outcome', 'sc_geo', 'sc_country'
    ]
    
    # Remove tracking parameters
    for param in tracking_params:
        if param in query_params:
            del query_params[param]
    
    # Rebuild the query string
    new_query = urlencode(query_params, doseq=True)
    
    # Rebuild the URL
    clean_url = urlunparse((
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        ''  # Remove fragment (anchor)
    ))
    
    # Remove trailing slash if present
    if clean_url.endswith('/'):
        clean_url = clean_url[:-1]
    
    return clean_url


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing www prefix, http/https, and trailing slashes.
    
    Args:
        url: The URL to normalize
        
    Returns:
        Normalized URL for comparison purposes
    """
    if not url:
        return ""
    
    # Remove protocol (http://, https://)
    url = re.sub(r'^https?://', '', url.lower())
    
    # Remove www prefix
    url = re.sub(r'^www\.', '', url)
    
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    
    return url


def deduplicate_urls(urls: List[str]) -> List[str]:
    """
    Remove duplicate URLs from a list, considering normalized versions.
    
    Args:
        urls: List of URLs to deduplicate
        
    Returns:
        List of unique URLs
    """
    seen = set()
    unique_urls = []
    
    for url in urls:
        sanitized = sanitize_url(url)
        normalized = normalize_url(sanitized)
        
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_urls.append(sanitized)
    
    return unique_urls 