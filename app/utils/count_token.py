"""Utility functions for counting tokens in text and Pydantic models"""

import tiktoken
from loguru import logger
from pydantic import BaseModel


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Count the number of tokens in a text string using the specified encoding

    Args:
        text: Text string to count tokens for
        encoding_name: Name of the tiktoken encoding to use

    Returns:
        Number of tokens in the text
    """
    try:
        enc = tiktoken.get_encoding(encoding_name)
        return len(enc.encode(text))
    except Exception as e:
        logger.error(f"Failed to count tokens: {str(e)}")
        return 0


def count_model_tokens(model: BaseModel, encoding_name: str = "cl100k_base") -> int:
    """
    Count the number of tokens in a Pydantic model using the specified encoding

    Args:
        model: Pydantic model to count tokens for
        encoding_name: Name of the tiktoken encoding to use

    Returns:
        Number of tokens in the model's JSON representation
    """
    try:
        # Convert model to JSON string
        json_str = model.model_dump_json()
        return count_tokens(json_str, encoding_name)
    except Exception as e:
        logger.error(f"Failed to count model tokens: {str(e)}")
        return 0
