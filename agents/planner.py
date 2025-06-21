# %% Import Libs
from pydantic import BaseModel
from pydantic_ai import Agent
import os, sys
from dotenv import load_dotenv

load_dotenv(override=True)

sys.path.append(p) if (p:=os.path.abspath('..')) not in sys.path else None
from models import agent_model, model_settings

# %% Planing Agent

HOW_MANY_SEARCHES = os.environ.get('HOW_MANY_SEARCHES', 5)
PLANNER_INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."

class WebSearchItem(BaseModel):
    reason: str
    query: str

class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem]

planner_agent = Agent(
    name="PlannerAgent",
    instructions=PLANNER_INSTRUCTIONS,
    model=agent_model,
    model_settings=model_settings,
    output_type=WebSearchPlan,
)

async def plan_searches(query: str):
    result = await planner_agent.run(f"Query: {query}")
    print(f"Will perform {len(result.output.searches)} searches")
    return result.output