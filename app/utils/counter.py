"""
Utility module for metric counters used across the application
"""

import logfire

# Crawler metrics
crawler_counter = logfire.metric_counter("crawler_fetch_count", unit="1", description="Number of fetch attempts by type and status")
