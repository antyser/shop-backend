import datetime
import sys

from agents import Agent, Runner
from pydantic import BaseModel

from app.llm.constants import OEPNROUTER_GEMINI_FLASH_MODEL
from app.llm.model_factory import create_agent_model


def get_system_prompt() -> str:
    """
    Generate an enhanced system prompt with the current date and time for comprehensive product research.

    Returns:
        str: The improved system prompt for the agent
    """
    now = datetime.datetime.now().isoformat()
    return f"""
You are a strategic research planning agent tasked with constructing a detailed research plan specifically tailored to the user's product inquiry. Your goal is to guide search agents to gather relevant, comprehensive information that aligns closely with user priorities and interests. Follow these structured steps:
Idenify the key user concerns and think of the research plan. Create a list of instructions for the search agents.
"""



class ResearchPlan(BaseModel):
    instructions: list[str]
    """A list of web searches to perform to best answer the query."""


planner_agent = Agent(
    name="PlannerAgent",
    instructions=get_system_prompt(),
    model=create_agent_model(OEPNROUTER_GEMINI_FLASH_MODEL),
    output_type=ResearchPlan,
)

def run(query: str) -> ResearchPlan:
    """
    Run the planner agent with the given query and print the results.
    
    Args:
        query (str): The research query to plan searches for
        
    Returns:
        WebSearchPlan: The generated search plan
    """
    # Use the Runner class to run the agent
    result = Runner.run_sync(planner_agent, query)
    
    # Get the final output as WebSearchPlan
    plan = result.final_output_as(ResearchPlan)
    
    print(f"Research Plan for: {query}\n")
    for i, instruction in enumerate(plan.instructions, 1):
        print(f"Instruction {i}:")
        print(f"  Instruction: {instruction}")
        print()
    
    return plan

def main():
    """
    Main function to run the planner agent from the command line.
    Usage: python planner_agent.py "Your research query here"
    """
    if len(sys.argv) < 2:
        print("Usage: python planner_agent.py \"Your research query here\"")
        return
    
    # Join all arguments to handle queries with spaces
    query = " ".join(sys.argv[1:])
    run(query)

if __name__ == "__main__":
    main()

