import asyncio
import sys

from loguru import logger
from openai import AsyncOpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from app.llm.constants import GPT_4_MINI_MODEL
from app.config import get_settings
from app.utils.count_token import count_tokens


@retry(retry=retry_if_exception_type(Exception), stop=stop_after_attempt(3))
async def generate_summary(content: str) -> str:
    """Generate a comprehensive summary of the content

    Args:
        content: Text content to analyze

    Returns:
        str: Formatted summary of the content
    """
    # Count initial tokens
    initial_token_count = count_tokens(content)
    logger.info(f"Input content contains {initial_token_count} tokens")

    settings = get_settings()
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
    )

    try:
        response = await client.chat.completions.create(
            model=GPT_4_MINI_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": f"Please summarize this content: {content}",
                },
            ],
        )

        if not response.choices or not response.choices[0].message.content:
            raise ValueError("Empty response received from the model")

        summary: str = response.choices[0].message.content
        if not isinstance(summary, str):
            raise ValueError("Invalid response type from model")

        summary_token_count = count_tokens(summary)
        logger.info(f"Generated summary contains {summary_token_count} tokens (reduced by {initial_token_count - summary_token_count} tokens)")

        return summary

    except Exception as e:
        logger.error(f"Failed to generate summary: {str(e)}")
        if hasattr(e, "__cause__") and e.__cause__ is not None:
            logger.error(f"Caused by: {str(e.__cause__)}")
        raise


if __name__ == "__main__":
    # Configure logging
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="INFO",
    )

    # Load content from debug file
    debug_file = "debug/9to5mac_com_2024_10_19_iphone_16_pro_review_one_month_later_.md"
    try:
        with open(debug_file, encoding="utf-8") as f:
            content = f.read()
            logger.info(f"Loaded content from {debug_file}")

        # Generate summary
        summary = asyncio.run(generate_summary(content))
        print(summary)

    except FileNotFoundError:
        logger.error(f"Debug file not found: {debug_file}")
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
