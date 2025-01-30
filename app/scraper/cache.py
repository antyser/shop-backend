"""Cache module for storing scrape results"""

import json
import time
from pathlib import Path
from typing import Any

import logfire
from pydantic import BaseModel

from app.config import get_settings


class CacheEntry(BaseModel):
    """Cache entry with timestamp"""

    data: dict[str, Any]
    timestamp: float


class ScrapeCache:
    """Local cache for scrape results"""

    def __init__(self, cache_file: str = "scrape_cache.json"):
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / cache_file
        self.settings = get_settings()
        self.cache: dict[str, CacheEntry] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from file"""
        try:
            if self.cache_file.exists():
                data = json.loads(self.cache_file.read_text())
                self.cache = {k: CacheEntry(**v) for k, v in data.items()}
                logfire.info(f"Loaded {len(self.cache)} entries from cache")
        except Exception as e:
            logfire.error(f"Failed to load cache: {str(e)}")
            self.cache = {}

    def _save_cache(self) -> None:
        """Save cache to file"""
        try:
            cache_data = {k: v.model_dump() for k, v in self.cache.items()}
            self.cache_file.write_text(json.dumps(cache_data, indent=2))
            logfire.info(f"Saved {len(self.cache)} entries to cache")
        except Exception as e:
            logfire.error(f"Failed to save cache: {str(e)}")

    def get(self, url: str) -> dict[str, Any] | None:
        """Get cached data for URL if not expired"""
        if not self.settings.ENABLE_CACHE:
            return None

        entry = self.cache.get(url)
        if not entry:
            return None

        # Check if cache entry has expired
        age = time.time() - entry.timestamp
        if age > self.settings.CACHE_TTL:
            logfire.info(f"Cache expired for {url}")
            del self.cache[url]
            self._save_cache()
            return None

        logfire.info(f"Cache hit for {url}")
        return entry.data

    def set(self, url: str, data: dict[str, Any]) -> None:
        """Set cache data for URL"""
        if not self.settings.ENABLE_CACHE:
            return

        self.cache[url] = CacheEntry(data=data, timestamp=time.time())
        self._save_cache()
        logfire.info(f"Cached data for {url}")


# Global cache instance
scrape_cache = ScrapeCache()
