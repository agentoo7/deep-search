from nicegui import ui
import asyncio, os, tempfile
from dotenv import load_dotenv
from weasyprint import HTML
import logfire, markdown, requests
from duckpy import Client

from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

load_dotenv(override=True)


# Point at your vLLM server:
provider = OpenAIProvider(
    base_url=os.environ["LOCAL_CHAT_MODEL_BASE_URL"],
    api_key=os.environ["LOCAL_CHAT_MODEL_API_KEY"],
)

# Tell PydanticAI which exact model name vLLM is serving:

agent_model = os.environ.get("MODEL_NAME", 'gpt-4o-mini')
# agent_model = OpenAIModel(os.environ["LOCAL_CHAT_MODEL_NAME"], provider=provider)


model_settings = ModelSettings(
    max_tokens=8000,
    temperature=0.0,
    stream=True
)

logfire.configure()
logfire.instrument_pydantic_ai()

HOW_MANY_SEARCHES = 5
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

def search_searxng(query: str, max_results: int = 5):
    params = {"q": query, "format": "json"}
    try:
        host = os.environ['searxng_url']
        resp = requests.get(host, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])[:max_results]
        return results
    except Exception as err:
        print(f"Error fetching SearXNG results: {err}")
        return []
    
def search_duck_duck_go(query: str, max_results: int = 5):
    try:
        print('search_duck_duck_go')
        client = Client()
        results = client.search(query)
        results = results[:max_results]
        return results
    except Exception as err:
        print(f"Error fetching DuckDuckGo results: {err}")
        return []
    
def export_pdf(md_text: str):
    html = markdown.markdown(md_text) # markdown to html
    pdf_bytes = HTML(string=html).write_pdf()
    fd, path = tempfile.mkstemp(suffix='.pdf')
    with os.fdopen(fd, 'wb') as f:
        f.write(pdf_bytes)
    ui.download(path)

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

with ui.element('div').classes("m-4 gap-4 grid sm:grid-cols-12 self-stretch"):
    with ui.element('div').classes("col-span-5 min-h-[100px] flex flex-col gap-4"):
        input_box = ui.textarea(
            label='Enter query: ',
            placeholder='What are the most popular and successful AI Coder Tool in May 2025',
            value="What are the most popular and successful AI Coder Tool in May 2025"
                                ).classes('p-2')
        send_btn = ui.button('Send')
        with ui.card().tight().classes('p-2') as main_output:
            ui.markdown('#### Output:')
            with ui.card_section():
                ui.label('intermediate: Lorem ipsum dolor sit amet, consectetur adipiscing elit, ...')

    with ui.card().classes("p-2 col-span-7 min-h-[600px] rounded-lg bg-white-500"):
        with ui.expansion('Buil the search plan', caption='Build the list of search items').classes('w-full') as build_plan_step:
            build_plan_step.open()
        with ui.expansion('Do searching', caption='Loop search for each item').classes('w-full') as search_step:
            ui.label('inside the expansion')
        with ui.expansion('Create report', caption='Create summay from search rerult').classes('w-full') as report_step:
            ui.label('inside the expansion')

    send_btn.on('click', lambda _: asyncio.create_task(handle_click()))

async def handle_click():
    searching = {
        'checkboxes': {},
        'progresses': {},
        'contents': {},
    }

    async def search_call_back(i, data):
        if data['status'] == 'start':
            # checkboxes[f'{i}'].text = f'Step: {i+1} is processing...'
            searching['progresses'][i].classes.clear()
            searching['progresses'][i].classes('block')
        else:
            searching['checkboxes'][i].value = True
            searching['progresses'][i].classes('hidden')
            searching['contents'][i].content = f'''
[{data['data'].title}]({data['data'].url}) \n
{data['data'].content}
''' 
    
    ## Build Search Plan

    build_plan_step.clear()
    with build_plan_step:
        ui.spinner('dots', size='lg', color='red')
        plan = await plan_searches(input_box.value)
        build_plan_step.clear()
        build_plan_step.open()
        for i, p in enumerate(plan.searches):
            ui.markdown (''
f'''**Search**: {i+1}<br>   
    - **Reason**: {p.reason}<br>
    - **Query**: {p.query}<br>
''') 
        with search_step:
            search_step.clear()
            search_step.open()
            for i, p in enumerate(plan.searches):
                searching['checkboxes'][i] = ui.checkbox(f'Search-{i+1}: {p.query}') 
                searching['progresses'][i] = ui.spinner('dots', size='lg', color='red')
                searching['progresses'][i].classes('hidden')
                searching['contents'][i] = ui.markdown()

    build_plan_step.close()

    search_results = await perform_searches(plan, search_call_back)

    report_step.open()
    report_step.clear()
    search_step.close()

    with report_step:
        ui.spinner('dots', size='lg', color='red')

    report = await write_report(input_box.value, search_results)
    report_step.clear()
    with report_step:
        ui.markdown(report.markdown_report)
        ui.button('Export PDF', on_click=lambda: export_pdf(report.markdown_report))
    
ui.run(title='Deep Search Agent', port=int(os.environ.get('APP_PORT', 9000)), reload=True) 
