#!/usr/bin/env python
"""
Research Manager CLI - Command-line interface for the research workflow

This script provides a convenient command-line interface to execute the research workflow
for a given query using the research manager. It generates a research plan,
executes searches concurrently, and synthesizes the findings into a comprehensive report.
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import logfire
from dotenv import load_dotenv
from loguru import logger

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from app.llm.agents.research_manager import execute_research_workflow


async def main():
    """
    Main function to run the research manager from the command line.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Research Manager CLI - Generate comprehensive research reports on any topic"
    )
    parser.add_argument(
        "query",
        type=str,
        help="The research query to investigate",
        nargs="?",
        default="",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path for the research report (default: save to research_reports directory)",
        default=None,
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug logging",
        default=False,
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv(override=True)
    
    # Configure logging
    logfire.configure()
    log_level = "DEBUG" if args.debug else "INFO"
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    
    # Disable OpenAI Agents tracing for cleaner logs
    os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    
    # Get research query from command line or prompt
    query = args.query
    if not query:
        query = input("Enter your research query: ")
        if not query:
            print("Error: No research query provided")
            return
    
    print(f"Starting comprehensive research workflow for: {query}")
    print("This may take some time as we gather and analyze information...")
    
    try:
        # Execute the full research workflow
        result = await execute_research_workflow(query)
        
        # Display the results
        print("\nRESEARCH REPORT:")
        print("=" * 80)
        print(result.report)
        
        # Save the report to a file
        if args.output:
            output_path = Path(args.output)
        else:
            output_dir = Path("research_reports")
            output_dir.mkdir(exist_ok=True)
            
            # Create a filename from the query
            filename = f"report_{query[:30].replace(' ', '_').replace('/', '_')}.txt"
            output_path = output_dir / filename
        
        with open(output_path, "w") as f:
            f.write(f"Research Query: {query}\n\n")
            f.write(result.report)
        
        print(f"\nReport saved to: {output_path}")
        
    except Exception as e:
        logger.exception(f"Error during research: {str(e)}")
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 