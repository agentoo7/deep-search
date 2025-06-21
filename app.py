# %% Import Libs

from nicegui import ui
import asyncio, os, sys

from agents.planner import plan_searches
from agents.searcher import perform_searches
from agents.report import write_report
from utils import export_pdf

# %% Main

with ui.header().style('justify-content: space-between; align-items: center;'):
    ui.label('Simple Deep Search').classes('text-xl font-semibold')
    new_search_btn = ui.button('Create New SEARCH')
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
            with ui.card_section() as main_card_section:
                pass

    with ui.card().classes("p-2 col-span-7 min-h-[600px] rounded-lg bg-white-500"):
        with ui.expansion('Buil the search plan', caption='Build the list of search items').classes('w-full') as build_plan_step:
            build_plan_step.open()
        with ui.expansion('Do searching', caption='Loop search for each item').classes('w-full') as search_step:
            ui.label('inside the expansion')
        with ui.expansion('Create report', caption='Create summay from search rerult').classes('w-full') as report_step:
            ui.label('inside the expansion')

    send_btn.on('click', lambda _: asyncio.create_task(handle_send_click()))
    new_search_btn.on('click', lambda _: asyncio.create_task(handle_new_search_click()))

async def handle_new_search_click():
    input_box.value = ''
    build_plan_step.clear()
    build_plan_step.close()
    search_step.clear()
    search_step.close()
    report_step.clear()
    report_step.close()
    main_card_section.clear()

async def export(markdown: str):
    path = export_pdf(markdown)
    ui.download(path)
        

async def handle_send_click():
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
        ui.button('Export PDF', on_click=lambda: export(report.markdown_report))
    with main_card_section:
        ui.markdown(report.markdown_report)


# %% Run App
ui.run(title='Deep Search Agent', port=int(os.environ.get('APP_PORT', 9000)), reload=True) 

# %%
