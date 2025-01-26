"""
Main application module for the Shop Backend API
"""

import logfire
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.scraper.router import router as scraper_router

settings = get_settings()


# logger.configure(handlers=[logfire.loguru_handler()])

load_dotenv(override=True)
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

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic()
logfire.instrument_httpx()
logfire.instrument_fastapi(app)
