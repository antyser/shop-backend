"""Factory for creating appropriate model instances."""

from typing import Union

from loguru import logger
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel

from app.config import get_settings


def create_model(model_name: str) -> Union[OpenAIModel, GeminiModel]:
    """
    Create appropriate model instance based on model name.

    Args:
        model_name: Name of the model to use

    Returns:
        Model instance appropriate for the given model name
    """
    settings = get_settings()

    if model_name.startswith("google/") or model_name.startswith("gemini-"):
        # Strip prefix if present
        gemini_name = model_name.replace("google/", "")
        logger.info(f"Creating Gemini model instance for {gemini_name}")
        return GeminiModel(
            model_name=gemini_name,
            api_key=settings.GEMINI_API_KEY,
        )
    else:
        # Default to OpenAI/OpenRouter for other models
        logger.info(f"Creating OpenAI model instance for {model_name}")
        return OpenAIModel(
            model_name=model_name,
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        )
