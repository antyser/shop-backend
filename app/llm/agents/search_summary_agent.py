import os
import sys
from typing import List

import logfire
from agents import Agent, Runner
from dotenv import load_dotenv
from loguru import logger

from app.llm.constants import GEMINI_FLASH_MODEL, OEPNROUTER_GEMINI_FLASH_MODEL
from app.llm.model_factory import create_agent_model


def get_system_prompt() -> str:
    """
    Generate the system prompt for the summarization agent.
    
    Returns:
        str: The system prompt for the agent
    """
    return """You are an expert research summarizer that synthesizes information follow the original instructions.
    # Response Guidelines:
- Provide detailed, structured responses clearly divided into logical sections and subsections.
- Explicitly cite all sources, including the title and direct URL.
- Prioritize accuracy, thoroughness, and relevance; completeness is more important than brevity.
- Clearly distinguish between confirmed facts, well-supported conclusions, informed predictions, and speculative statements. Explicitly label speculative or emerging insights as such.
- Anticipate and proactively address potential follow-up questions or related relevant context that enhances overall comprehension.
- Incorporate relevant recent advancements, unconventional perspectives, or alternative viewpoints, explicitly marking these as emerging or speculative when applicable."""


def create_summary_agent(
    model: str = OEPNROUTER_GEMINI_FLASH_MODEL,
    timeout: int = 300,  # 5 minutes for summarization
) -> Agent:
    """
    Create an agent specifically for summarizing search results.
    
    Args:
        model: Model name to use (default: gemini-2.0-flash)
        timeout: Timeout in seconds for API calls (default: 300 seconds)
        
    Returns:
        Agent: The summarization agent
    """
    # Create the model using the factory
    custom_model = create_agent_model(
        model_name=model,
        timeout=timeout,
    )
    
    # Create the summarization agent
    return Agent(
        name="summary_agent",
        instructions=get_system_prompt(),
        model=custom_model,
    )


if __name__ == "__main__":
    import asyncio