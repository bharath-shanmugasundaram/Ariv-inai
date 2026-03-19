import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

"""
arxiv_mcp_server.py
====================
FastMCP server that exposes the full arXiv paper analysis pipeline as MCP tools.

Tools
-----
  fetch_metadata        – arXiv metadata for a paper ID
  download_pdf          – download PDF by ID → local path
  extract_formulas      – formula/equation explanation markdown
  extract_workflow      – workflow/methodology explanation markdown
  extract_pytorch_impl  – full PyTorch implementation .py file
  analyze_paper         – full pipeline (download + all 3 extractions)

Usage
-----
  # Interactive inspector (browser UI):
  mcp dev arxiv_mcp_server.py

  # Wire into Claude Desktop (add to claude_desktop_config.json):
  {
    "mcpServers": {
      "arxiv-paper-agent": {
        "command": "python",
        "args": ["/absolute/path/to/arxiv_mcp_server.py"]
      }
    }
  }

Environment Variables
---------------------
  OPENROUTER_API_KEY  – default: http://localhost:11434
  OPENROUTER_MODEL – default: nvidia/nemotron-3-nano-30b-a3b:free
  ARXIV_PAPERS_DIR – root folder for downloaded PDFs
                     default: <this_file's_dir>/arxiv_papers
"""

import os 
import sys 


_ROOT =os .path .dirname (os .path .abspath (__file__ ))
for _pkg in ("arxiv_extract","equations_extracter"):
    _path =os .path .join (_ROOT ,_pkg )
    if _path not in sys .path :
        sys .path .insert (0 ,_path )

from mcp .server .fastmcp import FastMCP 


from paper_meta_data import fetch_paper_metadata 
from pdf_download import download_pdf as _download_pdf 
import extract_and_explain as _xae 


_DEFAULT_PAPERS_DIR =os .environ .get (
"ARXIV_PAPERS_DIR",
os .path .join (_ROOT ,"arxiv_papers"),
)


mcp = FastMCP(
    "arxiv-paper-agent",
    instructions=(
        "An AI tool server for analysing arXiv research papers. "
        "You can fetch metadata, download PDFs, extract formulas, "
        "explain workflows, and generate PyTorch implementations — "
        "all by supplying just an arXiv paper ID."
    ),
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)






@mcp .tool ()
def fetch_metadata (arxiv_id :str )-> dict:
    """
    Fetch all available metadata for an arXiv paper.

    Returns a dictionary containing: title, abstract, authors,
    submitted_date, last_updated, primary_category, all_categories,
    journal_reference, doi, doi_url, comment, arxiv_url, pdf_url,
    version_history, and all available links.

    Parameters
    ----------
    arxiv_id : str
        arXiv paper ID, e.g. "1706.03762" or "2602.19021v1".
    """
    return fetch_paper_metadata (arxiv_id )






@mcp .tool ()
def download_pdf (arxiv_id :str ,output_root :str ="")->str :
    """
    Download the PDF of an arXiv paper by its ID.

    Saves the file under:
      <output_root>/<paper_title>/paper/<arxiv_id>.pdf

    Parameters
    ----------
    arxiv_id    : arXiv paper ID, e.g. "1706.03762"
    output_root : Root folder for downloads. Leave blank to use the
                  default  arxiv_papers/  folder next to this server.

    Returns
    -------
    str – absolute path of the downloaded PDF file.
    """
    root =output_root .strip ()or _DEFAULT_PAPERS_DIR 
    return _download_pdf (arxiv_id ,output_root =root )






@mcp .tool ()
def extract_formulas (pdf_path :str ,output_dir :str ="")-> str:
    """
    Extract and explain all mathematical formulas from a paper PDF.

    Uses a local OpenRouter model to:
      1. Identify every equation/formula in the PDF.
      2. Explain each formula with a variable breakdown and intuition.

    Writes the result to  <paper>_formulas.md  in the output directory.

    Parameters
    ----------
    pdf_path   : Absolute path to the PDF file on disk.
    output_dir : Folder to save the markdown file. Defaults to the same
                 folder as the PDF.

    Returns
    -------
    str – absolute path of the generated  <paper>_formulas.md  file.
    """
    out =output_dir .strip ()or None 
    return _xae .extract_formulas (pdf_path ,output_dir =out )






@mcp .tool ()
def extract_workflow (pdf_path :str ,output_dir :str ="")-> str:
    """
    Extract and explain the end-to-end methodology / workflow from a paper PDF.

    Uses a local OpenRouter model to:
      1. Break the paper's method into numbered steps.
      2. Elaborate each step with sub-sections and key design decisions.
      3. Append an overall architecture diagram (ASCII / Mermaid).

    Writes the result to  <paper>_workflow.md  in the output directory.

    Parameters
    ----------
    pdf_path   : Absolute path to the PDF file on disk.
    output_dir : Folder to save the markdown file. Defaults to the same
                 folder as the PDF.

    Returns
    -------
    str – absolute path of the generated  <paper>_workflow.md  file.
    """
    out =output_dir .strip ()or None 
    return _xae .extract_workflow (pdf_path ,output_dir =out )






@mcp .tool ()
def extract_pytorch_impl (pdf_path :str ,output_dir :str ="")-> str:
    """
    Generate a complete PyTorch implementation of the model described in a paper PDF.

    Uses a local OpenRouter model to write a runnable .py file that:
      • Implements every architectural component as an nn.Module subclass.
      • Translates each equation to torch operations with inline comments.
      • Includes a __main__ sanity-check block with random input tensors.

    Writes the result to  <paper>_implementation.py.

    Parameters
    ----------
    pdf_path   : Absolute path to the PDF file on disk.
    output_dir : Folder to save the .py file. Defaults to the same
                 folder as the PDF.

    Returns
    -------
    str – absolute path of the generated  <paper>_implementation.py  file.
    """
    out =output_dir .strip ()or None 
    return _xae .extract_pytorch_impl (pdf_path ,output_dir =out )






@mcp .tool ()
def analyze_paper (arxiv_id :str ,output_root :str ="")-> dict:
    """
    Full arXiv paper analysis pipeline in one call.

    Steps (automatically chained):
      1. Download the PDF from arXiv by ID.
      2. Extract and explain all formulas   → <paper>_formulas.md
      3. Extract and explain the workflow  → <paper>_workflow.md
      4. Generate a PyTorch implementation → <paper>_implementation.py

    PDF is read once; base LLM calls (equations + workflow) are shared
    across all three extraction steps for efficiency.

    Parameters
    ----------
    arxiv_id    : arXiv paper ID, e.g. "1706.03762"
    output_root : Root folder for downloads and extractions.
                  Defaults to the  arxiv_papers/  folder next to this server.

    Returns
    -------
    dict with keys:
      pdf_path            – absolute path to the downloaded PDF
      formulas_path       – absolute path to <paper>_formulas.md
      workflow_path       – absolute path to <paper>_workflow.md
      implementation_path – absolute path to <paper>_implementation.py
    """
    root =output_root .strip ()or _DEFAULT_PAPERS_DIR 


    print (f"\n{'='*60 }")
    print (f"    ANALYZE PAPER: {arxiv_id }")
    print (f"{'='*60 }")
    pdf_path =_download_pdf (arxiv_id ,output_root =root )


    paper_dir =os .path .dirname (pdf_path )
    results =_xae .extract_all (pdf_path ,output_dir =paper_dir )

    return {
    "pdf_path":pdf_path ,
    "formulas_path":results ["formulas_path"],
    "workflow_path":results ["workflow_path"],
    "implementation_path":results ["implementation_path"],
    }

if __name__ =="__main__":
    # Use SSE/HTTP transport by default on port 8000
    mcp.run(transport='sse')
