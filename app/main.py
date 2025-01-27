"""
Main application module for the Shop Backend API
"""

import logfire
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.scraper.router import router as scraper_router

settings = get_settings()

if settings.ENVIRONMENT == "prod":
    sentry_sdk.init(
        dsn="https://595562752640a86693f4bb4dfa9ecf98@o4508708809277440.ingest.us.sentry.io/4508708810915840",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        _experiments={
            # Set continuous_profiling_auto_start to True
            # to automatically start the profiler on when
            # possible.
            "continuous_profiling_auto_start": True,
        },
    )


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    description="API for shopping",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scraper_router, prefix=settings.API_V0_STR, tags=["scraper"])

logfire.configure(send_to_logfire="if-token-present", environment=settings.ENVIRONMENT)
logfire.instrument_pydantic()
logfire.instrument_httpx()
logfire.instrument_fastapi(app)
logfire.instrument_system_metrics()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
