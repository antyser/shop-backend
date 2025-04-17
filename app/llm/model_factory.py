"""
Model factory module for creating agent models with different vendors.

This module provides functionality to create models for agents with different
LLM providers like OpenAI, Gemini, Anthropic, and OpenRouter.
"""

import os
from typing import Optional

from agents import ModelSettings, OpenAIChatCompletionsModel
from loguru import logger
from openai import AsyncOpenAI

OPENAI_API_ENDPOINT = None
ANTHROPIC_API_ENDPOINT = "https://api.anthropic.com/v1/messages"
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
OPENROUTER_API_ENDPOINT = "https://openrouter.ai/api/v1"

# Default timeout in seconds (5 minutes)
DEFAULT_TIMEOUT = 300


def determine_provider_config(model_name: str) -> tuple[Optional[str], str]:
    """
    Determine the API endpoint and API key environment variable for a given model.
    
    Args:
        model_name: The model name
        
    Returns:
        tuple[Optional[str], str]: API endpoint and API key env var name
    """
    # Handle models with explicit provider prefix
    if model_name.startswith("/"):
        # Models starting with / use OpenRouter
        return OPENROUTER_API_ENDPOINT, "OPENROUTER_API_KEY"
    
    if "/" in model_name:
        provider = model_name.split("/", 1)[0].lower()
        if provider == "openai":
            return OPENAI_API_ENDPOINT, "OPENAI_API_KEY"
        elif provider == "anthropic":
            return ANTHROPIC_API_ENDPOINT, "ANTHROPIC_API_KEY"
        elif provider == "gemini":
            return GEMINI_API_ENDPOINT, "GEMINI_API_KEY"
        else:
            # Other providers use OpenRouter
            return OPENROUTER_API_ENDPOINT, "OPENROUTER_API_KEY"
    
    # Handle models without provider prefix based on naming conventions
    if model_name.startswith("gpt-") or model_name.startswith("o3-"):
        return OPENAI_API_ENDPOINT, "OPENAI_API_KEY"
    elif model_name.startswith("gemini-"):
        return GEMINI_API_ENDPOINT, "GEMINI_API_KEY"
    elif model_name.startswith("claude-"):
        return ANTHROPIC_API_ENDPOINT, "ANTHROPIC_API_KEY"
    
    # Default to OpenAI for unknown models
    logger.warning(f"Unknown model: {model_name}, defaulting to OpenAI")
    return OPENAI_API_ENDPOINT, "OPENAI_API_KEY"


def create_agent_model(
    model_name: str,
    api_key: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> OpenAIChatCompletionsModel:
    """
    Create an agent model based on the model name.
    
    Args:
        model_name: Name of the model to use
        api_key: Optional API key to use (if not provided, will use environment variables)
        timeout: Timeout in seconds for API calls (default: 300 seconds)
        
    Returns:
        OpenAIChatCompletionsModel: The model to use with the agent
    """
    # Determine the API endpoint and API key environment variable
    api_endpoint, api_key_env = determine_provider_config(model_name)
    
    # Get the API key
    model_api_key = api_key or os.getenv(api_key_env)
    if not model_api_key:
        raise ValueError(f"{api_key_env} environment variable is not set")
    
    # Create the client with the appropriate configuration
    client_kwargs = {
        "api_key": model_api_key,
        "timeout": timeout,  # Set timeout for API calls
    }
    
    if api_endpoint:
        client_kwargs["base_url"] = api_endpoint
    
    # Create the client
    client = AsyncOpenAI(**client_kwargs)
    
    # Create and return the model - use the model name as is
    return OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=client
    )
