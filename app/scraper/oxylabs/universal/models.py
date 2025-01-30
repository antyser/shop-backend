"""Models for Oxylabs universal scraper"""

from typing import Any

from pydantic import BaseModel


class UniversalContent(BaseModel):
    """Content from universal scraping"""

    url: str
    content: str | None = None  # Content might be empty
    status_code: int
    html: str  # Raw HTML content
    headers: dict[str, str] | None = None


class UniversalResult(BaseModel):
    """Single result from universal scraping"""

    content: str  # Raw HTML content as string
    created_at: str
    updated_at: str
    page: int = 1  # Default to page 1
    url: str
    job_id: str
    status_code: int


class JobContext(BaseModel):
    """Job context information"""

    key: str
    value: Any


class JobInfo(BaseModel):
    """Job information"""

    callback_url: str | None = None
    client_id: int
    context: list[JobContext]
    created_at: str
    domain: str
    geo_location: str | None = None
    id: str
    limit: int
    pages: int
    parse: bool
    source: str
    status: str
    url: str
    content_encoding: str
    updated_at: str
    user_agent_type: str


class OxyUniversalResponse(BaseModel):
    """Complete response from Oxylabs universal scraping"""

    results: list[UniversalResult]
    job: JobInfo
    url: str | None = None  # URL field is optional
