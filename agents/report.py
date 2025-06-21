# %% Report Agent
# REPORT AGENT

# %% Import Libs

from pydantic import BaseModel
from pydantic_ai import Agent
import os, sys

sys.path.append(p) if (p:=os.path.abspath('..')) not in sys.path else None

from models import agent_model, model_settings

# %% Report Aggent

REPORT_INSTRUCTIONS = (
    "You are a senior researcher tasked with writing a cohesive report for a research query. "
    "You will be provided with the original query, and some initial research done by a research assistant.\n"
    "You should first come up with an outline for the report that describes the structure and "
    "flow of the report. Then, generate the report and return that as your final output.\n"
    "The final output should be in markdown format, and it should be lengthy and detailed. Aim "
    "for 5-10 pages of content, at least 1000 words."
)

class ReportData(BaseModel):
    short_summary: str
    markdown_report: str
    follow_up_questions: list[str]

writer_agent = Agent(
    name="WriterAgent",
    instructions=REPORT_INSTRUCTIONS,
    model=agent_model,
    model_settings=model_settings,
    output_type=ReportData,
)

async def write_report(query: str, search_results: list[str]):
    print("Thinking about report...")
    input_text = f"Original query: {query}\nSummarized search results: {search_results}"
    result = await writer_agent.run(input_text)
    print("Finished writing report")
    return result.output
# %%
