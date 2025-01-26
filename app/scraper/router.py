from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.scraper.models import (
    ScrapeProductRequest,
    ScrapeProductResponse,
    ScrapeRequest,
    ScrapeResponse,
    ScrapeSearchRequest,
    ScrapeSearchResponse,
)
from app.scraper.service import scrape_links, scrape_product, scrape_search

router = APIRouter(tags=["scraper"])


@router.post("/scrape-links", response_model=ScrapeResponse)
async def scrape_links_post(request: ScrapeRequest) -> ScrapeResponse:
    """
    Scrape and parse content from a list of URLs

    Args:
        request: ScrapeRequest containing list of URLs to scrape

    Returns:
        ScrapeResponse containing mapping of URLs to their scraped content
    """
    try:
        return await scrape_links([str(url) for url in request.urls])
    except Exception as e:
        logger.error(f"Error scraping URLs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/scrape-product", response_model=ScrapeProductResponse)
async def scrape_product_get(url: str = Query(..., description="Product URL to scrape")) -> ScrapeProductResponse:
    """
    Scrape product information and related reviews (GET method)

    Args:
        url: Product URL to scrape

    Returns:
        ScrapeProductResponse containing product information and search results
    """
    try:
        return await scrape_product(url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/scrape-product", response_model=ScrapeProductResponse)
async def scrape_product_post(request: ScrapeProductRequest) -> ScrapeProductResponse:
    """
    Scrape product information and related reviews (POST method)

    Args:
        request: ScrapeProductRequest containing product URL

    Returns:
        ScrapeProductResponse containing product information and search results
    """
    try:
        return await scrape_product(str(request.url))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scraping product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/scrape-search", response_model=ScrapeSearchResponse)
async def scrape_search_post(request: ScrapeSearchRequest) -> ScrapeSearchResponse:
    """
    Scrape Google search results for a query

    Args:
        request: ScrapeSearchRequest containing search query

    Returns:
        ScrapeSearchResponse containing search results
    """
    try:
        return await scrape_search(request.query)
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
