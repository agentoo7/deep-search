# %% Import Libs
from duckpy import Client
import markdown, requests
from weasyprint import HTML
import tempfile, os

# %% Define functions

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
    return path
# %%
