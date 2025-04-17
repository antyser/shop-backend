"""
Streamlit UI for the Research Manager.

This script provides a web interface for interacting with the research workflow,
including planning, searching, and report generation.

Usage:
    streamlit run app/streamlit_research_ui.py

Example:
    streamlit run app/streamlit_research_ui.py
"""
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import logfire
import streamlit as st
from agents.run import RunConfig
from dotenv import load_dotenv
from loguru import logger

# Add the project root to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.agents.planner_agent import ResearchPlan, planner_agent
from app.llm.agents.research_manager import ResearchResult, execute_research_workflow
from app.llm.agents.search_agent import Runner, create_search_agent

# Configure page
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if "research_results" not in st.session_state:
    st.session_state.research_results = None
if "research_plan" not in st.session_state:
    st.session_state.research_plan = None
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "report" not in st.session_state:
    st.session_state.report = None
if "is_researching" not in st.session_state:
    st.session_state.is_researching = False
if "step" not in st.session_state:
    st.session_state.step = 0
if "progress" not in st.session_state:
    st.session_state.progress = 0
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "end_time" not in st.session_state:
    st.session_state.end_time = None


async def run_research_workflow(query: str) -> ResearchResult:
    """
    Run the complete research workflow with the given query.
    
    Args:
        query: The research query
        
    Returns:
        ResearchResult: Contains the research plan, search results and final report
    """
    # Disable OpenAI Agents tracing to prevent payload too large errors
    os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"
    
    # Step 1: Planning - Update UI
    st.session_state.step = 1
    st.session_state.progress = 0.1
    logfire.configure(scrubbing=False)
    logfire.instrument_openai_agents()
    # Execute the complete research workflow directly
    with st.spinner("Running the research workflow..."):
        try:
            # Call the execute_research_workflow function directly from research_manager
            result = await execute_research_workflow(query)
            
            # Update session state with results
            st.session_state.research_plan = result.plan
            st.session_state.search_results = result.search_results
            st.session_state.report = result.report
            st.session_state.step = 3
            st.session_state.progress = 1.0
            
            return result
        except Exception as e:
            logger.exception(f"Error in research workflow: {e}")
            raise e


def format_time(seconds):
    """Format seconds into a human-readable time string."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {int(seconds)}s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"


def research_callback():
    """Callback function for the research button."""
    query = st.session_state.research_query
    if query:
        st.session_state.is_researching = True
        st.session_state.research_results = None
        st.session_state.research_plan = None
        st.session_state.search_results = None
        st.session_state.report = None
        st.session_state.step = 0
        st.session_state.progress = 0
        st.session_state.start_time = time.time()
        st.session_state.end_time = None


def save_report_to_file(query: str, report: str) -> str:
    """
    Save the research report to a file.
    
    Args:
        query: The research query
        report: The report content
        
    Returns:
        str: The path to the saved file
    """
    # Create the output directory
    output_dir = Path("research_reports")
    output_dir.mkdir(exist_ok=True)
    
    # Create a sanitized filename from the query
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = "".join(c if c.isalnum() or c in " _-" else "_" for c in query)
    filename = f"report_{timestamp}_{safe_query[:30].replace(' ', '_')}.md"
    output_path = output_dir / filename
    
    # Write the report to the file
    with open(output_path, "w") as f:
        f.write(f"# Research Report: {query}\n\n")
        f.write(f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(report)
    
    return str(output_path)


def main():
    """Main function to run the Streamlit app."""
    # Load environment variables
    load_dotenv(override=True)
    
    # Configure logging
    logfire.configure(scrubbing=False)
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # App title and description
    st.title("📚 AI Research Assistant")
    st.markdown("""
    This tool uses an AI research workflow to plan, search, and synthesize information about a topic.
    Enter your research query below to get started.
    """)
    
    # Sidebar with API key configuration and instructions
    st.sidebar.title("Configuration")
    
    # Check if API keys are set
    searchapi_key = os.getenv("SEARCHAPI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Display API key status
    if not searchapi_key:
        st.sidebar.error("⚠️ SEARCHAPI_API_KEY is not set")
    else:
        st.sidebar.success("✅ SEARCHAPI_API_KEY is set")
    
    if not openai_key:
        st.sidebar.error("⚠️ OPENAI_API_KEY is not set")
    else:
        st.sidebar.success("✅ OPENAI_API_KEY is set")
    
    # Add instructions in the sidebar
    st.sidebar.title("How It Works")
    st.sidebar.markdown("""
    1. **Planning**: AI creates a research plan with specific search queries
    2. **Searching**: Executes searches concurrently to gather information
    3. **Synthesis**: Compiles findings into a comprehensive report
    """)
    
    # Example queries to help users get started
    st.sidebar.title("Example Queries")
    example_queries = [
        "murad retinol youth renewal serum analysis"
    ]
    
    for query in example_queries:
        if st.sidebar.button(f"📝 {query}"):
            st.session_state.research_query = query
            research_callback()
    
    # Research input
    st.text_area(
        "Enter your research query:",
        key="research_query",
        height=100,
        placeholder="e.g., Compare the benefits and drawbacks of different sustainable energy sources for residential use.",
    )
    
    # Research button
    col1, col2 = st.columns([5, 1])
    with col1:
        st.button(
            "🔍 Start Research",
            key="research_button",
            on_click=research_callback,
            disabled=not (searchapi_key and openai_key)
        )
    
    with col2:
        if st.button("Clear"):
            st.session_state.research_results = None
            st.session_state.research_plan = None
            st.session_state.search_results = None
            st.session_state.report = None
            st.session_state.is_researching = False
            st.session_state.step = 0
            st.session_state.progress = 0
            st.session_state.research_query = ""
            st.session_state.start_time = None
            st.session_state.end_time = None
            st.rerun()
    
    # Display progress bar when researching
    if st.session_state.is_researching or st.session_state.step > 0:
        # Show progress bar
        st.progress(st.session_state.progress)
        
        # Show current step
        if st.session_state.step == 0:
            st.info("Initializing research workflow...")
        elif st.session_state.step == 1:
            st.info("Step 1: Generating research plan...")
        elif st.session_state.step == 2:
            st.info("Step 2: Executing searches...")
        elif st.session_state.step == 3:
            st.info("Step 3: Synthesizing findings into report...")
    
    # Display a progress indicator while researching
    if st.session_state.is_researching:
        with st.spinner("Processing your research request..."):
            # Run the research asynchronously
            query = st.session_state.research_query
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                research_result = loop.run_until_complete(run_research_workflow(query))
                st.session_state.research_results = research_result
                st.session_state.end_time = time.time()
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                logger.exception(f"Research error: {str(e)}")
                st.session_state.step = -1  # Error state
            finally:
                loop.close()
                st.session_state.is_researching = False
                if st.session_state.end_time is None:
                    st.session_state.end_time = time.time()
            
            st.rerun()
    
    # Display research completion time if available
    if st.session_state.end_time and st.session_state.start_time:
        elapsed_time = st.session_state.end_time - st.session_state.start_time
        st.info(f"Research completed in {format_time(elapsed_time)}")
    
    # Display research plan if available
    if st.session_state.research_plan:
        st.markdown("## Research Plan")
        st.markdown(f"**Query:** {st.session_state.research_query}")
        
        # Display the research plan
        with st.expander("View Research Plan", expanded=True):
            for i, instruction in enumerate(st.session_state.research_plan, 1):
                st.markdown(f"**{i}.** {instruction}")
    
    # Display search results if available
    if st.session_state.search_results:
        st.markdown("## Search Results")
        
        # Display the search results
        for i, result in enumerate(st.session_state.search_results, 1):
            with st.expander(f"Search {i} Results", expanded=False):
                st.markdown(result)
    
    # Display the final report if available
    if st.session_state.report:
        st.markdown("## Research Report")
        
        # Add download button for the report
        report = st.session_state.report
        query = st.session_state.research_query
        report_path = save_report_to_file(query, report)
        
        cols = st.columns([3, 1])
        with cols[1]:
            with open(report_path, "r") as f:
                report_content = f.read()
                st.download_button(
                    label="📥 Download Report",
                    data=report_content,
                    file_name=os.path.basename(report_path),
                    mime="text/markdown",
                )
        
        # Display the report
        st.markdown(report)


if __name__ == "__main__":
    main() 