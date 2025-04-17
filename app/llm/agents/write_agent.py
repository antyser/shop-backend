"""
Write agent module for generating research reports based on search results.

This module provides functionality for the write agent that synthesizes research
information from search results into comprehensive reports.
"""

import datetime
import os
from typing import Any

from agents import Agent, OpenAIChatCompletionsModel, RunContextWrapper
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from loguru import logger
from openai import AsyncOpenAI

from app.llm.constants import OEPNROUTER_GEMINI_FLASH_MODEL
from app.llm.model_factory import create_agent_model


def get_write_system_prompt() -> str:
    """
    Generate the system prompt for the write agent.
    
    Returns:
        str: The system prompt for the write agent
    """
    now = datetime.datetime.now().isoformat()
    return prompt_with_handoff_instructions(f"""

You are a product review writer. You should write a review for a product based on the search results.
You should think from a user perspective. i.e. a wide bread toaster slot -> it can fit in a bagel.
Be concise and focus on the most important features and benefits of the product.
Use bullet points and short sentences. Each section should not be over 5 sentences.

""")


# Create the write agent
write_agent = Agent(
    name="write_agent",
    instructions=get_write_system_prompt(),
)


def create_write_agent_with_model(model: str = OEPNROUTER_GEMINI_FLASH_MODEL) -> Agent:
    """
    Create a write agent with a custom model.
    
    Args:
        model: Model to use (default: OEPNROUTER_GEMINI_FLASH_MODEL)
        
    Returns:
        Agent: The write agent with custom model
    """
    # Create the model using the factory
    custom_model = create_agent_model(
        model_name=model,
    )
    
    return Agent(
        name=write_agent.name,
        instructions=write_agent.instructions,
        model=custom_model,
    )