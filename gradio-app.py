import gradio as gr
import asyncio, os

from agents.planner import plan_searches
from agents.searcher import perform_searches
from agents.report import write_report
from utils import export_pdf
import time

def new_search():
    return "", "", "", "", gr.update(visible=False)

def deep_search_stream(query):
    # 1) Build plan
    plan = asyncio.run(plan_searches(query))
    plan_md = "### Build Search Plan\n"
    for i, p in enumerate(plan.searches):
        plan_md += (
            f"**{i+1}.** Reason: {p.reason}  \n"
            f"Query: `{p.query}`\n\n"
        )
        
        yield gr.Tabs(selected=0), plan_md, gr.update(value=""), gr.update(value=""), gr.update(visible=False)

    time.sleep(1)
    yield gr.Tabs(selected=1), plan_md, gr.update(value=""), gr.update(value=""), gr.update(visible=False)
    

    search_md = "### Search Results\n"
    results = []
    for i, p in enumerate(plan.searches):
        search_md += f"⏳ Step {i+1}: `{p.query}`\n\n"
        yield gr.Tabs(selected=1), gr.update(value=plan_md), search_md, gr.update(value=""), gr.update(visible=False)

        item = asyncio.run(perform_searches(plan, callback=None))[i]
        results.append(item)
    
        search_md = search_md.rstrip("⏳ Step {i+1}: `{p.query}`\n\n")
        search_md += (
            f"✔️ Step {i+1}: [{item.title}]({item.url})\n\n"
            f"{item.content}\n\n"
        )
        yield gr.Tabs(selected=1), gr.update(value=plan_md), search_md, gr.update(value=""), gr.update(visible=False)

    time.sleep(1)
    yield gr.Tabs(selected=2), plan_md, search_md, gr.update(value=""), gr.update(visible=False)
    
    # 3) Create report

    report = asyncio.run(write_report(query, results))
    report_md = report.markdown_report


    path = export_pdf(report_md)

    yield gr.Tabs(selected=2), gr.update(value=plan_md), gr.update(value=search_md), report_md, gr.update(visible=True, value= path)

# --- Build Gradio UI ---
with gr.Blocks() as demo:
    with gr.Row():
        gr.Markdown("## Simple Deep Search")
        new_btn = gr.Button("Create New SEARCH")

    with gr.Row():
        with gr.Column(scale=5):
            input_box = gr.TextArea(label="Enter query", lines=4,
                                    value="What are the most popular and successful AI Coder Tool in May 2025")
            send_btn = gr.Button("Send")
        with gr.Column(scale=7):
            with gr.Tabs() as tabs:
                with gr.TabItem("Build Plan", id=0):
                    plan_output = gr.Markdown()
                with gr.TabItem("Do Searching", id=1):
                    search_output = gr.Markdown()
                with gr.TabItem("Create Report", id=2):
                    report_output = gr.Markdown()

    export_btn = gr.File(label="Download Report PDF", visible=False)

    send_btn.click(
        fn=deep_search_stream,
        inputs=[input_box],
        outputs=[tabs, plan_output, search_output, report_output, export_btn]
    )
    new_btn.click(
        fn=new_search,
        outputs=[input_box, plan_output, search_output, report_output, export_btn]
    )

if __name__ == "__main__":
    demo.launch(server_port=int(os.environ.get("APP_PORT", 9000)))
