#  AI Code-Generation Agent

A local AI agent that turns a plain-English project description into a **complete, working codebase** — file structure, roadmap, and all source files — powered by **Google Gemini**.

---

##  What It Does

Describe any project in one sentence and the agent will:

1. **Plan** — Generate a structured roadmap and file tree
2. **Generate** — Write every file with full, working code
3. **Save** — Create the project in `output/<project-name>/` ready to run

---

##  Quick Start

### 1. Clone / enter the project
```bash
cd code-gen-agent
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key
```bash
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_actual_key
```
Get a free key at: https://aistudio.google.com/app/apikey

### 5. Run the agent
```bash
# Interactive mode (recommended for first time)
python main.py

# Or pass a prompt directly
python main.py --prompt "create a portfolio website with HTML, CSS and JavaScript"
```

---

##  Example Prompts

| Prompt | Output |
|--------|--------|
| `create a portfolio website with HTML, CSS and JavaScript` | `output/portfolio-site/` with full HTML/CSS/JS |
| `create a Python Flask REST API with /health and /items endpoints` | `output/flask-api/` with app.py, requirements, etc. |
| `create a simple todo app using vanilla JavaScript` | `output/todo-app/` with HTML/CSS/JS |
| `create a React landing page for a SaaS startup` | `output/saas-landing/` with React components |

---

##  Project Structure

```
code-gen-agent/
├── main.py          ← CLI entry point
├── agent.py         ← Pipeline orchestrator
├── planner.py       ← LLM → structured JSON plan
├── writer.py        ← Writes generated files to disk
├── llm.py           ← Google Gemini API wrapper
├── prompts.py       ← All LLM system prompts
├── requirements.txt
├── .env.example
└── output/          ← Generated projects appear here
    └── <project-name>/
        ├── index.html
        ├── style.css
        └── ...
```

---

##  Configuration

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Google Gemini API key (required) |

---

##  How It Works

```
Your prompt
    │
    ▼
planner.py  ──  Gemini API  ──  JSON plan (roadmap + files)
    │
    ▼
writer.py   ──  Creates output/<project>/ with all files
    │
    ▼
agent.py    ──  Beautiful terminal output with Rich
```

The LLM is instructed to return a strict JSON schema with full file contents — no placeholders, no TODOs.
