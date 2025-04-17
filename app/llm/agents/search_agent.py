import asyncio
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import logfire
from agents import Agent, RunContextWrapper, Runner, function_tool
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field

from app.llm.agents.search_summary_agent import create_summary_agent
from app.llm.constants import OEPNROUTER_GEMINI_FLASH_MODEL
from app.llm.model_factory import create_agent_model
from app.scraper.crawler.html_fetcher import OutputFormat, fetch_batch
from app.scraper.searchapi.google_search import GoogleSearchResponse, search_google
from app.utils.url_utils import normalize_url, sanitize_url


def get_system_prompt() -> str:
    """
    Generate an optimized system prompt with the current date and time.

    Returns:
        str: The system prompt for the agent
    """
    now = datetime.datetime.now().isoformat()
    return f"""You are an advanced research assistant AI. Today is {now}. Follow these instructions precisely, but don't ask any clarifying questions:

### Task Execution Protocol:

1. **Clarify the Objective**: Clearly restate the question or topic to ensure complete understanding.
2. **Assess Current Knowledge**: Evaluate if the information currently available is sufficient to fully answer the user's question with accuracy, depth, and completeness.
3. **Conduct Targeted Searches**: If existing information is incomplete or insufficient, systematically use the provided search tools to retrieve detailed, authoritative, and up-to-date information.
4. **Evaluate Sources**:
   - Critically assess each source's reliability, accuracy, and relevance.
   - Prefer authoritative, peer-reviewed, or primary sources whenever possible.
   - Explicitly note any potential biases, uncertainties, or limitations in the retrieved information.

### Response Guidelines:

- Provide detailed, structured responses clearly divided into logical sections and subsections.
- Explicitly cite all sources in the following format: `[Source Title](Full URL)`. For example: `[National Institutes of Health - Vitamin D Information](https://ods.od.nih.gov/factsheets/VitaminD-HealthProfessional/)`.
- Prioritize accuracy, thoroughness, and relevance; completeness is more important than brevity.
- Clearly distinguish between confirmed facts, well-supported conclusions, informed predictions, and speculative statements. Explicitly label speculative or emerging insights as such.
- Anticipate and proactively address potential follow-up questions or related relevant context that enhances overall comprehension.
- Incorporate relevant recent advancements, unconventional perspectives, or alternative viewpoints, explicitly marking these as emerging or speculative when applicable.

### Insight & Value-Addition:

- Go beyond superficial summaries; actively synthesize and interpret data to offer meaningful insights.
- Identify alternative perspectives, compare methodologies or interpretations from various authoritative sources, and explicitly discuss implications.

### Iteration & Confirmation:

- Continually assess whether the acquired information sufficiently answers the user's query.
- Use iterative searches to fill gaps until confident in the completeness and accuracy of your response.

Always adhere strictly to these guidelines to ensure your research and answers meet the highest standards.
"""


class SearchSource(BaseModel):
    """Source information from search results"""
    
    title: str = Field(description="Title of the source")
    url: str = Field(description="URL of the source")
    snippet: Optional[str] = Field(None, description="Snippet or description of the source")
    content: Optional[str] = Field(None, description="Full content fetched from the source")

@function_tool
async def search(
    ctx: RunContextWrapper[Any],
    task: str, 
    #max_results: int = 25,
    scrape_content: bool = True,
) -> List[SearchSource]:
    """
    Search for information on the internet and extract content from relevant sources.
    
    Args:
        ctx: The run context wrapper
        task: The natural language task or question to search for
        max_results: Maximum number of search results to consider
        scrape_content: Whether to scrape content from the search results
    
    Returns:
        str: A summary of search results with sources
    """
    # Use the task directly as the search query
    search_query = task
    logger.info(f"Searching for: {search_query}")
    
    # Execute the search using the Google Search API
    search_results = await search_google(
        query=search_query,
        num_results=10,
        scrape_content=False  # We'll handle content scraping separately
    )
    
    # Extract relevant information from the search results
    sources = []
    urls_to_fetch = []
    
    if search_results.organic_results:
        sanitized_results = []
        for result in search_results.organic_results:
            if result.link and result.title:
                # Sanitize the URL
                sanitized_url = sanitize_url(result.link)
                result.link = sanitized_url
                sanitized_results.append(result)
        
        # Second pass: deduplicate URLs
        seen_urls = set()
        for result in sanitized_results:
            # Skip if we've already seen this URL (after normalization)
            normalized_url = normalize_url(result.link)
            if normalized_url in seen_urls:
                continue
                
            seen_urls.add(normalized_url)
            source = SearchSource(
                title=result.title,
                url=result.link,
                snippet=result.snippet
            )
            sources.append(source)
            urls_to_fetch.append(result.link)
    
    # Scrape content from the sources
    if scrape_content and urls_to_fetch:
        logger.info(f"Scraping content from {len(urls_to_fetch)} URLs")
        fetched_contents = await fetch_batch(
            urls=urls_to_fetch,
            output_format=OutputFormat.MARKDOWN
        )
        
        # Update sources with fetched content
        for source in sources:
            if source.url in fetched_contents and fetched_contents[source.url]:
                # Store the full content without truncation
                source.content = fetched_contents[source.url]
    
    return sources


def create_search_agent(
    model: str = OEPNROUTER_GEMINI_FLASH_MODEL,
    timeout: int = 600,
) -> Agent:
    """
    Create a search agent with a custom model.
    
    Args:
        model: Model name to use (default: gemini-2.0-flash)
        timeout: Timeout in seconds for API calls (default: 600 seconds)
        temperature: Model temperature setting (default: 0.5)
        
    Returns:
        Agent: The search agent with custom model
    """
    # Create the model using the factory with increased timeout
    custom_model = create_agent_model(
        model_name=model,
        timeout=timeout,
    )
    
    summary_agent = create_summary_agent()
    return Agent(
        name="search_agent",
        instructions=get_system_prompt(),
        tools=[search],
        # handoffs=[summary_agent],
        model=custom_model,
    )


async def main():
    """
    Main function to run the search agent directly.
    """
    # Load environment variables
    load_dotenv(override=True)
    
    # Configure logging
    logfire.configure(scrubbing=False)
    logfire.instrument_openai_agents()
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Disable OpenAI Agents tracing
    os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    
    # Check for required API keys
    searchapi_key = os.getenv("SEARCHAPI_API_KEY")
    
    if not searchapi_key:
        logger.error("SEARCHAPI_API_KEY environment variable is not set.")
        print("Error: SEARCHAPI_API_KEY environment variable is not set.")
        print("Please set it in your .env file or environment.")
        return
    
    # Get search task from user
    task = input("Enter your search query: ")
    if not task:
        print("Error: No search query provided")
        return
    
    print(f"Searching for: {task}")
    print("This may take a moment...")
    
    try:
        # Create and run the search agent
        search_agent = create_search_agent()
        result = await Runner.run(search_agent, task)
        
        # Display the results
        print("\nSEARCH RESULTS:")
        print("=" * 80)
        print(result.final_output)
        
    except Exception as e:
        logger.exception(f"Error during search: {str(e)}")
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())