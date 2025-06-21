# %% Import Libs
from pydantic import BaseModel
from pydantic_ai import Agent
import os, sys

sys.path.append(p) if (p:=os.path.abspath('..')) not in sys.path else None

from models import agent_model, model_settings
from .planner import WebSearchPlan, WebSearchItem

from utils import search_duck_duck_go, search_searxng
import os

# %% Searcher Agent

SEARCH_INSTRUCTIONS = (
    "You are a research assistant. Given a search term, you search the web for that term and "
    "words. Capture the main points. Write succintly, no need to have complete sentences or good "
    "produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 "
    "grammar. This will be consumed by someone synthesizing a report, so it's vital you capture the "
    "essence and ignore any fluff. Do not include any additional commentary other than the summary itself."
)

class SearchResult(BaseModel):
    url: str
    title: str
    content: str

search_agent = Agent(
    name="SearchAgent",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[search_duck_duck_go if os.environ.get('SEARCH_ENGINE', 'DuckDuckGo') == 'DuckDuckGo'  else search_searxng],
    model=agent_model,
    model_settings=model_settings,
    output_type=SearchResult
)

async def perform_searches(plan: WebSearchPlan, callback=None):
    # Process sequential
    results = []
    for i, item in enumerate(plan.searches):
        if callback:
            await callback(i, {'status':'start', 'data': None})
        result = await search(item)
        results.append(result)
        if callback:
            await callback(i, {'status': 'end', 'data': result})
    return results

async def search(item: WebSearchItem):
    input_text = f"Search term: {item.query}\nReason for searching: {item.reason}"
    result = await search_agent.run(input_text)
    return result.output
