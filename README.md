# Ariv-inai — arXiv Paper Analysis & Code Generation Agent

An AI-powered MCP (Model Context Protocol) server that automatically extracts insights from arXiv research papers and generates working PyTorch implementations. Connect it to Claude (Desktop or Web) and analyze any research paper with a single command.

---

## What It Does

Given any arXiv paper ID, the agent:
1. Fetches full paper metadata (authors, abstract, categories, DOI, etc.)
2. Downloads the PDF
3. Extracts and explains every mathematical equation with variable breakdowns
4. Converts the methodology into a step-by-step workflow with architecture diagrams
5. Generates a complete, runnable PyTorch implementation of the paper

It also includes a standalone **Code Generation Agent** that turns natural language descriptions into complete project scaffolds for any tech stack.

---

## Project Structure

```
Ariv-inai/
├── arxiv_mcp_server.py          # MCP server entry point (6 tools exposed)
├── requirements.txt             # Main dependencies
├── Dockerfile                   # Container deployment
├── .env.example                 # Environment variable template
│
├── arxiv_extract/               # PDF download & metadata module
│   ├── paper_meta_data.py       # Fetch arXiv metadata via API
│   ├── pdf_download.py          # Download PDFs from arXiv
│   ├── main.py                  # Search papers by title (CLI)
│   └── id_main.py               # Download + extract text (CLI)
│
├── equations_extracter/         # LLM-powered extraction pipelines
│   └── extract_and_explain.py   # Formulas, workflow, PyTorch code gen
│
└── Code Gen/                    # Standalone code generation agent
    ├── main.py                  # CLI entry point
    ├── agent.py                 # Orchestration + Rich UI
    ├── planner.py               # LLM → JSON project plan
    ├── writer.py                # Materializes files to disk
    ├── llm.py                   # OpenRouter API wrapper
    ├── prompts.py               # LLM system prompts
    ├── requirements.txt         # Code Gen dependencies
    └── output/                  # Generated projects land here
```

---

## MCP Tools (API Reference)

The server exposes **6 tools** accessible from any MCP client (Claude Desktop, Claude Web, etc.):

| Tool | Description | Returns |
|------|-------------|---------|
| `fetch_metadata(arxiv_id)` | Full paper metadata from arXiv API | `dict` with title, abstract, authors, dates, DOI, links |
| `download_pdf(arxiv_id, output_root?)` | Download PDF from arXiv | Absolute path to saved PDF |
| `extract_formulas(pdf_path, output_dir?)` | Extract + explain all equations | Path to `<id>_formulas.md` |
| `extract_workflow(pdf_path, output_dir?)` | Extract step-by-step methodology | Path to `<id>_workflow.md` |
| `extract_pytorch_impl(pdf_path, output_dir?)` | Generate PyTorch implementation | Path to `<id>_implementation.py` |
| `analyze_paper(arxiv_id, output_root?)` | **Full pipeline in one call** | `dict` with all paths + inline content |

### `analyze_paper` — Full Pipeline Output

```python
{
  "pdf_path": "/tmp/arxiv_papers/Attention Is All You Need/paper/1706.03762.pdf",
  "formulas_path": "...1706.03762_formulas.md",
  "workflow_path":  "...1706.03762_workflow.md",
  "implementation_path": "...1706.03762_implementation.py",
  "formulas":       "# Equations\n...",   # inline markdown
  "workflow":       "# Workflow\n...",    # inline markdown
  "implementation": "import torch\n..."   # inline Python
}
```

---

## Agent Workflow

```
User provides arXiv ID (e.g. "1706.03762")
         │
         ▼
 ┌───────────────┐
 │ fetch_metadata│  → Title, authors, abstract, DOI, categories
 └───────┬───────┘
         │
         ▼
 ┌───────────────┐
 │ download_pdf  │  → Saves PDF to /tmp/arxiv_papers/<Title>/paper/<ID>.pdf
 └───────┬───────┘
         │
         ├──────────────────────────────────────────┐
         │                                          │
         ▼                                          ▼
 ┌─────────────────┐                   ┌──────────────────────┐
 │extract_formulas │                   │  extract_workflow    │
 │                 │                   │                      │
 │ PDF text        │                   │ PDF text             │
 │  → LLM prompt   │                   │  → LLM (steps)       │
 │  → equations +  │                   │  → LLM (elaborate)   │
 │    explanations │                   │  → architecture diag │
 └────────┬────────┘                   └──────────┬───────────┘
          │                                        │
          └──────────────┬─────────────────────────┘
                         │
                         ▼
               ┌──────────────────────┐
               │ extract_pytorch_impl │
               │                      │
               │ equations + workflow │
               │  → Code Gen LLM      │
               │  → nn.Module classes │
               │  → sanity check main │
               └──────────┬───────────┘
                          │
                          ▼
               All outputs returned inline
               + saved to output directory
```

---

## Output Files

Generated files follow a consistent structure:

```
/tmp/arxiv_papers/
└── <Paper Title>/
    ├── paper/
    │   └── <arxiv_id>.pdf
    ├── <arxiv_id>_formulas.md        ← Equations + variable tables + explanations
    ├── <arxiv_id>_workflow.md         ← Step-by-step methodology + architecture
    └── <arxiv_id>_implementation.py   ← Runnable PyTorch code
```

### Formula Output (`_formulas.md`)
- LaTeX equations numbered sequentially
- Variable definition tables for each equation
- Intuitive explanation of what each formula computes

### Workflow Output (`_workflow.md`)
- High-level numbered steps (Input → Process → Output)
- Key design decisions per step
- ASCII or Mermaid architecture diagram

### Implementation Output (`_implementation.py`)
- Each component as an `nn.Module` subclass
- Inline comments citing equation numbers from the paper
- `if __name__ == '__main__':` sanity check with random tensors

---

## Code Generation Agent

A standalone agent in `Code Gen/` that generates complete projects from natural language.

### Workflow

```
User: "Create a REST API with Flask and SQLite"
         │
         ▼
 ┌─────────────────┐
 │   planner.py    │  LLM → Structured JSON plan:
 │                 │  { project_name, tech_stack,
 │                 │    roadmap, files: [{path, content}] }
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │   writer.py     │  Creates output/<project-name>/
 │                 │  Writes every file from the plan
 └────────┬────────┘
          │
          ▼
 ┌─────────────────┐
 │   agent.py      │  Displays Rich UI:
 │                 │  - Tech stack list
 │                 │  - Roadmap phases
 │                 │  - File tree
 └─────────────────┘
```

### Usage

```bash
cd "Code Gen"
pip install -r requirements.txt

# Interactive mode
python main.py

# CLI mode
python main.py --prompt "Build a FastAPI app with JWT auth and PostgreSQL"
```

Generated project lands in `Code Gen/output/<project-name>/`.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| MCP Framework | FastMCP |
| PDF Processing | pdfplumber |
| LLM Inference | OpenRouter API |
| Default LLM Model | `nvidia/nemotron-3-nano-30b-a3b:free` |
| Terminal UI | Rich |
| Transport | HTTP + SSE |
| Runtime | Python 3.11+ |
| Deployment | Docker |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | — | Your OpenRouter API key |
| `PORT` | No | `8000` | Server port |
| `ARXIV_PAPERS_DIR` | No | `/tmp/arxiv_papers` | PDF storage directory |
| `OPENROUTER_MODEL` | No | `nvidia/nemotron-3-nano-30b-a3b:free` | LLM model to use |

Copy `.env.example` to `.env` and fill in your key:

```bash
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY
```

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export OPENROUTER_API_KEY="sk-or-..."

# Start the MCP server
python arxiv_mcp_server.py
# Server running at http://localhost:8000/sse
```

**Dev mode with MCP Inspector:**

```bash
mcp dev arxiv_mcp_server.py
# Opens browser inspector UI for testing tools interactively
```

---

## Docker

```bash
# Build
docker build -t ariv-inai .

# Run
docker run -e OPENROUTER_API_KEY="sk-or-..." -p 8000:8000 ariv-inai
```

---

## Connecting to Claude

### Claude Desktop

Add to your Claude Desktop config file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "arxiv-paper-agent": {
      "command": "python",
      "args": ["/absolute/path/to/Ariv-inai/arxiv_mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop. The 6 tools will appear automatically.

### Claude Web (Pro/Team/Enterprise only)

1. Go to **claude.ai** → profile → **Settings** → **Integrations**
2. Click **Add Integration**
3. Enter your deployed server's SSE URL (e.g. `https://your-app.railway.app/sse`)
4. Enable it in any conversation via the connector icon

### Cloud Deployment (Railway / Render / Fly.io)

Deploy with Docker. Set `OPENROUTER_API_KEY` in the platform's environment variable dashboard. The SSE endpoint will be at `https://<your-app>/sse`.

---

## Example Prompts in Claude

Once connected, you can ask Claude:

```
Analyze this paper: 1706.03762
```

```
Download the PDF for arxiv paper 2301.07041 and extract all the formulas
```

```
Give me a PyTorch implementation of the paper at arxiv ID 1412.6980
```

Claude will call the appropriate MCP tools and return the results inline.

---

## Dependencies

**Main project (`requirements.txt`):**
```
mcp[cli]>=1.0
requests>=2.31.0
pdfplumber>=0.9
python-dotenv>=1.0.0
```

**Code Gen (`Code Gen/requirements.txt`):**
```
requests>=2.31.0
python-dotenv>=1.0.0
rich>=13.0.0
```

---

## Get an OpenRouter API Key

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Go to **Keys** → **Create Key**
3. Free models are available with no credit card required
