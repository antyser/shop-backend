"""
Research Manager module for orchestrating the entire research workflow.

This module provides functionality to manage the research process by:
1. Using a planner agent to generate a research plan
2. Using search agents to execute the searches concurrently
3. Using a write agent to synthesize the findings into a comprehensive report
"""

import asyncio
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import logfire
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field

from app.llm.agents.planner_agent import ResearchPlan, planner_agent
from app.llm.agents.search_agent import create_search_agent
from app.llm.agents.write_agent import create_write_agent_with_model
from app.llm.constants import GEMINI_FLASH_MODEL, OEPNROUTER_GEMINI_FLASH_MODEL


class ResearchResult(BaseModel):
    """Research result containing all gathered information and the final report"""
    
    original_query: str = Field(description="The original research query")
    plan: List[str] = Field(description="The research plan that was followed")
    search_results: List[str] = Field(description="Results of all searches performed as text summaries")
    report: str = Field(description="The final synthesized research report")


async def execute_research_workflow(query: str) -> ResearchResult:
    """
    Execute the complete research workflow for a given query.
    
    Args:
        query: The research query to investigate
        
    Returns:
        ResearchResult: The complete research result including plan, search results, and final report
    """
    # Disable OpenAI Agents tracing to prevent payload too large errors
    os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    
    logger.info(f"Starting research workflow for query: {query}")
    
    # Step 1: Generate research plan using planner agent
    logger.info("Step 1: Generating research plan...")
    research_plan = await Runner.run(planner_agent, query)
    plan = research_plan.final_output_as(ResearchPlan)
    
    # Log the generated plan
    logger.info(f"Generated research plan with {len(plan.instructions)} instructions")
    for i, instruction in enumerate(plan.instructions, 1):
        logger.info(f"Research item {i}: {instruction}")
    
    # Step 2: Execute searches concurrently
    logger.info("Step 2: Executing searches concurrently...")
    search_agent = create_search_agent()
    
    # Create a list of coroutines for concurrent execution
    search_tasks = []
    for instruction in plan.instructions:
        search_tasks.append(Runner.run(search_agent, instruction))
    
    # Execute all searches concurrently with proper error handling
    logger.info(f"Executing {len(search_tasks)} search tasks concurrently...")
    completed_tasks = await asyncio.gather(*search_tasks, return_exceptions=True)
    
    # Extract search results and handle any errors
    all_search_results = []
    for i, result in enumerate(completed_tasks):
        search_instruction = plan.instructions[i]
        if isinstance(result, Exception):
            # Log the error and include a placeholder for failed searches
            logger.warning(f"Search {i+1} failed: {str(result)}")
            error_message = f"Unable to complete search for: {search_instruction}\nError: {str(result)}"
            all_search_results.append(error_message)
        else:
            logger.info(f"Completed search {i+1}/{len(completed_tasks)}")
            # Store the final output directly, as it's already a summary
            all_search_results.append(result.final_output)
    
    # Step 3: Synthesize findings using write agent
    logger.info("Step 3: Synthesizing findings into report...")
    write_agent = create_write_agent_with_model()
    
    # Prepare context for the write agent
    write_context = f"""
    Research Query: {query}
    
    Research Plan:
    {', '.join([f"{i+1}. {instruction}" for i, instruction in enumerate(plan.instructions)])}
    
    Search Results:
    """
    
    # Add search results to context in a structured format
    for i, result in enumerate(all_search_results):
        write_context += f"\n--- Search {i+1} Results ---\n{result}\n"
    
    # Generate the final report
    write_result = await Runner.run(write_agent, write_context)
    final_report = write_result.final_output
    
    # Compile the complete research result
    return ResearchResult(
        original_query=query,
        plan=plan.instructions,
        search_results=all_search_results,
        report=final_report
    )


async def main():
    """
    Main function to run the research manager directly.
    """
    # Load environment variables
    load_dotenv(override=True)
    
    # Configure logging
    logfire.configure(scrubbing=False)
    logfire.instrument_openai_agents()
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # Disable OpenAI Agents tracing for cleaner logs
    os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    
    # Get research query from command line or input
    query = ""
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    
    if not query:
        query = input("Enter your research query: ")
        if not query:
            print("Error: No research query provided")
            return
    
    print(f"Starting comprehensive research workflow for: {query}")
    print("This may take some time as we gather and analyze information...")
    
    try:
        # Execute the full research workflow
        print("Starting research workflow...")
        print("Step 1: Generating research plan...")
        result = await execute_research_workflow(query)
        
        # Display the results
        print("\nRESEARCH REPORT:")
        print("=" * 80)
        print(result.report)
        
        # Save the report to a file
        output_dir = Path("research_reports")
        output_dir.mkdir(exist_ok=True)
        
        # Create a sanitized filename from the query
        filename = f"report_{query[:30].replace(' ', '_').replace('/', '_')}.txt"
        output_path = output_dir / filename
        
        with open(output_path, "w") as f:
            f.write(f"Research Query: {query}\n\n")
            f.write(result.report)
        
        print(f"\nReport saved to: {output_path}")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error during research: {str(e)}")
        print(f"An error occurred: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check that all required API keys are set in your .env file")
        print("2. Verify your internet connection")
        print("3. Try a simpler query or fewer search instructions")
        print("4. Check the logs for detailed error information")


if __name__ == "__main__":
    asyncio.run(main())