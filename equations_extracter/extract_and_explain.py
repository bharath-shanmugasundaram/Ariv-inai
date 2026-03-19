import sys
import builtins
def _custom_print(*args, **kwargs):
    kwargs.setdefault('file', sys.stderr)
    builtins.print(*args, **kwargs)
print = _custom_print

"""
extract_and_explain.py
======================
arXiv Paper Content Extractor – three independent pipelines:

  1. extract_formulas(pdf_path, output_dir)
     → reads PDF, finds ALL equations/formulas, explains each one,
       and writes  <paper_id>_formulas.md

  2. extract_workflow(pdf_path, output_dir)
     → reads PDF, outlines the end-to-end methodology / workflow,
       and writes  <paper_id>_workflow.md

  3. extract_pytorch_impl(pdf_path, output_dir)
     → reads PDF + uses formula/workflow context to ask OpenRouter for a
       complete, runnable PyTorch implementation of the paper's model,
       and writes  <paper_id>_implementation.py

All functions return the path of the file they created and can be
called independently from the MCP agent or via the CLI below.
"""

import os
import sys
import requests
import json
import pdfplumber

# ── Make Code Gen accessible ──────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_CODE_GEN_DIR = os.path.abspath(os.path.join(_HERE, "..", "Code Gen"))
if _CODE_GEN_DIR not in sys.path:
    sys.path.insert(0, _CODE_GEN_DIR)

try:
    from llm import generate as codegen_generate
    from planner import _strip_json_fences
except ImportError:
    codegen_generate = None
    _strip_json_fences = None

# ──────────────────────────────────────────────────────────────────────────────
#  Configuration  (override via environment variables if needed)
# ──────────────────────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise EnvironmentError(
        "OPENROUTER_API_KEY environment variable is not set. "
        "Set it in Railway's environment variables dashboard."
    )
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")


# ──────────────────────────────────────────────────────────────────────────────
#  Low-level helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ask_openrouter(prompt: str, temperature: float = 0.2, max_tokens: int = 6000) -> str:
    """Send a prompt to OpenRouter and return the generated text."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model":  OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=600)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Cannot connect to OpenRouter API.")
    except requests.exceptions.Timeout:
        raise TimeoutError("OpenRouter request timed out.")
    except requests.exceptions.HTTPError as e:
        raise ConnectionError(f"OpenRouter API error: {e}\n{response.text}")

    data = response.json()
    try:
        content = data["choices"][0]["message"].get("content")
        if content is None:
            print(f"\\n[WARNING] OpenRouter returned empty content. Full response: {data}\\n")
            return ""
        return content.strip()
    except (KeyError, IndexError):
        raise ValueError(f"Unexpected response format from OpenRouter: {data}")


def _read_pdf_text(pdf_path: str) -> str:
    """Extract raw text from all pages of a PDF."""
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages
        total = len(pages)
        for i, page in enumerate(pages, 1):
            print(f"    Reading page {i}/{total} …")
            text = page.extract_text()
            if text:
                full_text += text + "\n"

    if not full_text.strip():
        raise ValueError("Could not extract any text from the PDF.")
    return full_text


def _make_output_path(pdf_path: str, suffix: str, output_dir: str | None) -> str:
    """Build the output markdown file path."""
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    filename = f"{base}_{suffix}.md"
    folder = output_dir or os.path.dirname(os.path.abspath(pdf_path))
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename)


# ──────────────────────────────────────────────────────────────────────────────
#  Pipeline 1 – Formula / Equation explanation
# ──────────────────────────────────────────────────────────────────────────────

def _extract_raw_equations(pdf_text: str) -> str:
    """Step 1a – pull every equation/formula out of the raw PDF text."""
    prompt = (
        "You are an expert mathematician and researcher.\n"
        "I will give you the raw text extracted from a research paper PDF.\n\n"
        "YOUR TASK:\n"
        "1. Identify EVERY mathematical equation, formula, or symbolic expression.\n"
        "2. Output them as a clean numbered list, each in proper LaTeX notation.\n"
        "3. If PDF extraction garbled symbols, reconstruct the intended formula from context.\n"
        "4. Include ALL equations – loss functions, update rules, probability expressions, etc.\n\n"
        "--- BEGIN PDF TEXT ---\n"
        f"{pdf_text}\n"
        "--- END PDF TEXT ---\n\n"
        "Numbered list of LaTeX equations:"
    )
    return _ask_openrouter(prompt)


def _explain_equations(equations: str, pdf_text: str) -> str:
    """Step 1b – explain each formula in detail."""
    prompt = (
        "You are an expert AI researcher and math professor.\n"
        "Below is a numbered list of mathematical equations extracted from a research paper.\n"
        "I also provide you with context from the paper itself.\n\n"
        "YOUR TASK – for EACH equation:\n"
        "  • Give it a descriptive heading (e.g. '## 1. Cross-Entropy Loss')\n"
        "  • Reproduce the LaTeX formula in a $$...$$ block\n"
        "  • Variable breakdown table: | Symbol | Meaning | Type/Shape |\n"
        "  • 2-3 sentence intuitive explanation of what the formula computes\n"
        "  • Where it appears in the pipeline (e.g. 'used during training to …')\n\n"
        "--- EQUATIONS ---\n"
        f"{equations}\n\n"
        "--- PAPER CONTEXT (first pages) ---\n"
        f"{pdf_text[:]}\n"
        "--- END ---\n\n"
        "Detailed formula explanations:"
    )
    return _ask_openrouter(prompt, temperature=0.3, max_tokens=8000)


def extract_formulas(pdf_path: str, output_dir: str | None = None) -> str:
    """
    Extract and explain all mathematical formulas in *pdf_path*.

    Parameters
    ----------
    pdf_path   : absolute path to the input PDF
    output_dir : folder where the markdown file will be saved
                 (defaults to the same folder as the PDF)

    Returns
    -------
    str  – absolute path of the generated  <paper>_formulas.md  file
    """
    print(f"\n{'='*60}")
    print(f"    FORMULA EXTRACTION: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")

    print("\n  Reading PDF …")
    pdf_text = _read_pdf_text(pdf_path)

    print(f"\n  Asking {OPENROUTER_MODEL} to extract equations …")
    raw_equations = _extract_raw_equations(pdf_text)

    print(f"\n  Asking {OPENROUTER_MODEL} to explain each formula …")
    explained = _explain_equations(raw_equations, pdf_text)

    # ── Write output ──────────────────────────────────────────────────────────
    out_path = _make_output_path(pdf_path, "formulas", output_dir)
    paper_name = os.path.basename(pdf_path)

    file_content = (
        f"# Formula Explanations — {paper_name}\n\n"
        f"> Auto-generated by `extract_and_explain.py` · Model: `{OPENROUTER_MODEL}`\n\n"
        "---\n\n## Raw Extracted Equations\n\n"
        + raw_equations + "\n\n"
        "---\n\n## Detailed Formula Explanations\n\n"
        + explained + "\n"
    )
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        print(f"\n  Formulas file saved →  {out_path}\n")
    except OSError as e:
        print(f"\n  [WARNING] Could not save formulas to disk: {e}\n")
        out_path = "(not saved — ephemeral filesystem)"

    return f"Saved to: {out_path} FORMULAS:{explained}"


# ──────────────────────────────────────────────────────────────────────────────
#  Pipeline 2 – Workflow / Methodology explanation
# ──────────────────────────────────────────────────────────────────────────────

def _extract_workflow_steps(pdf_text: str) -> str:
    """Step 2a – identify the paper's methodology as ordered steps."""
    prompt = (
        "You are an expert AI/ML researcher and technical writer.\n"
        "I will give you the raw text extracted from a research paper PDF.\n\n"
        "YOUR TASK:\n"
        "1. Identify the end-to-end methodology / algorithm / workflow of the paper.\n"
        "2. Break it down into clear, numbered STEPS (e.g. Step 1: Data Preprocessing …).\n"
        "3. Each step should briefly state: what happens, why it matters.\n"
        "4. Include any key design choices, architectural components, or training procedures.\n"
        "5. If the paper proposes multiple experiments or variants, describe the main one.\n\n"
        "--- BEGIN PDF TEXT ---\n"
        f"{pdf_text}\n"
        "--- END PDF TEXT ---\n\n"
        "End-to-end workflow (numbered steps):"
    )
    return _ask_openrouter(prompt)


def _elaborate_workflow(workflow_steps: str, pdf_text: str) -> str:
    """Step 2b – elaborate on each workflow step in depth."""
    prompt = (
        "You are a senior ML engineer explaining a research paper to a technical team.\n"
        "Below are the high-level workflow steps of a paper, plus context from the paper itself.\n\n"
        "YOUR TASK – for each step:\n"
        "  • Use a '## Step N: <Title>' heading\n"
        "  • Subsections: Input | Process | Output | Key Design Decision\n"
        "  • Mention any relevant formula names (you don't need to re-derive them)\n"
        "  • Highlight what makes this step novel or non-obvious\n"
        "Add a '## Overall Architecture Diagram (Text)' section at the end, "
        "showing a simple ASCII or mermaid flow linking all steps.\n\n"
        "--- WORKFLOW STEPS ---\n"
        f"{workflow_steps}\n\n"
        "--- PAPER CONTEXT (first pages) ---\n"
        f"{pdf_text[:]}\n"
        "--- END ---\n\n"
        "Detailed workflow elaboration:"
    )
    return _ask_openrouter(prompt, temperature=0.3, max_tokens=8000)


def extract_workflow(pdf_path: str, output_dir: str | None = None) -> str:
    """
    Extract and explain the full methodology / workflow from *pdf_path*.

    Parameters
    ----------
    pdf_path   : absolute path to the input PDF
    output_dir : folder where the markdown file will be saved
                 (defaults to the same folder as the PDF)

    Returns
    -------
    str  – absolute path of the generated  <paper>_workflow.md  file
    """
    print(f"\n{'='*60}")
    print(f"    WORKFLOW EXTRACTION: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")

    print("\n  Reading PDF …")
    pdf_text = _read_pdf_text(pdf_path)

    print(f"\n  Asking {OPENROUTER_MODEL} to outline workflow steps …")
    workflow_steps = _extract_workflow_steps(pdf_text)

    print(f"\n  Asking {OPENROUTER_MODEL} to elaborate each step …")
    elaborated = _elaborate_workflow(workflow_steps, pdf_text)

    # ── Write output ──────────────────────────────────────────────────────────
    out_path = _make_output_path(pdf_path, "workflow", output_dir)
    paper_name = os.path.basename(pdf_path)

    file_content = (
        f"# Workflow Explanation — {paper_name}\n\n"
        f"> Auto-generated by `extract_and_explain.py` · Model: `{OPENROUTER_MODEL}`\n\n"
        "---\n\n## High-Level Workflow Steps\n\n"
        + workflow_steps + "\n\n"
        "---\n\n## Detailed Step-by-Step Breakdown\n\n"
        + elaborated + "\n"
    )
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(file_content)
        print(f"\n  Workflow file saved →  {out_path}\n")
    except OSError as e:
        print(f"\n  [WARNING] Could not save workflow to disk: {e}\n")
        out_path = "(not saved — ephemeral filesystem)"

    return f"Saved to: {out_path} WORKFLOW:{elaborated}"


# ──────────────────────────────────────────────────────────────────────────────
#  Pipeline 3 – PyTorch Implementation generation
# ──────────────────────────────────────────────────────────────────────────────

def _generate_pytorch_code(
    pdf_text: str,
    raw_equations: str,
    workflow_steps: str,
) -> str:
    """
    Ask the Code Gen LLM agent to produce a complete PyTorch implementation.
    """
    if codegen_generate is None:
        raise ImportError(
            "Could not import the Code Gen agent. Ensure the 'Code Gen' "
            "folder is present alongside 'equations_extracter'."
        )

    system_prompt = (
        "You are an expert software architect and senior deep learning engineer.\\n"
        "Your job is to translate a research paper into a COMPLETE, runnable PyTorch model.\\n\\n"
        "Rules:\\n"
        "- Respond ONLY with the raw python code. No explanations, no markdown fences, no surrounding text.\\n"
        "- The PyTorch module must import only standard ML libraries (torch, torch.nn, math, etc.).\\n"
        "- Implement every architectural component as a separate nn.Module subclass.\\n"
        "- Include equations from the context as inline comments citing equation numbers.\\n"
        "- End the file with an `if __name__ == '__main__':` block running a sanity check forward pass with random tensors."
    )

    user_prompt = (
        "Write the PyTorch implementation for this research paper.\\n\\n"
        "--- A) PAPER EXCERPTS (first pages) ---\\n"
        f"{pdf_text[:]}\\n\\n"
        "--- B) EQUATIONS ---\\n"
        f"{raw_equations}\\n\\n"
        "--- C) WORKFLOW STEPS ---\\n"
        f"{workflow_steps}\\n"
    )

    raw_response = codegen_generate(system_prompt, user_prompt)
    
    # Strip accidental markdown fences if the model included them anyway
    code = raw_response.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        if len(lines) > 0 and lines[0].startswith("```"):
            lines = lines[1:]
        if len(lines) > 0 and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\\n".join(lines)
        
    return code


def extract_pytorch_impl(pdf_path: str, output_dir: str | None = None, formulas_text: str | None = None, workflow_text: str | None = None) -> str:
    """
    Generate a complete PyTorch implementation of the model in *pdf_path*.

    Parameters
    ----------
    pdf_path       : absolute path to the input PDF
    output_dir     : folder where the .py file will be saved
                     (defaults to the same folder as the PDF)
    formulas_text  : pre-computed raw equations string (optional).
                     If None, the PDF is re-analysed for equations.
    workflow_text  : pre-computed workflow steps string (optional).
                     If None, the PDF is re-analysed for workflow.

    Returns
    -------
    dict  – with keys 'implementation' (str) and 'path' (str)
    """
    print(f"\n{'='*60}")
    print(f"    PYTORCH IMPL GENERATION: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")

    print("\n  Reading PDF …")
    pdf_text = _read_pdf_text(pdf_path)

    # Derive equations context if not supplied
    if formulas_text is None:
        print(f"\n  Extracting equations for context ({OPENROUTER_MODEL}) …")
        formulas_text = _extract_raw_equations(pdf_text)

    # Derive workflow context if not supplied
    if workflow_text is None:
        print(f"\n  Extracting workflow for context ({OPENROUTER_MODEL}) …")
        workflow_text = _extract_workflow_steps(pdf_text)

    print("\n  Asking Code Gen Agent to write the PyTorch implementation …")
    pytorch_code = _generate_pytorch_code(pdf_text, formulas_text, workflow_text)

    # Strip accidental markdown fences the model may have added inside the JSON content
    pytorch_code = pytorch_code.strip()
    if pytorch_code.startswith("```"):
        lines = pytorch_code.splitlines()
        # drop opening fence (e.g. ```python)
        lines = lines[1:]
        # drop closing fence if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        pytorch_code = "\n".join(lines)

    # ── Write output ──────────────────────────────────────────────────────────
    out_path = _make_output_path(pdf_path, "implementation", output_dir)
    # Ensure .py extension
    out_path = os.path.splitext(out_path)[0] + ".py"

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(pytorch_code + "\n")
        print(f"\n  PyTorch implementation saved →  {out_path}\n")
    except OSError as e:
        print(f"\n  [WARNING] Could not save implementation to disk: {e}\n")
        out_path = "(not saved — ephemeral filesystem)"

    return f"Saved to: {out_path} IMPLEMENTATION:{pytorch_code}"


# ──────────────────────────────────────────────────────────────────────────────
#  Convenience: run ALL THREE pipelines in one call
# ──────────────────────────────────────────────────────────────────────────────

def extract_all(pdf_path: str, output_dir: str | None = None) -> dict:
    """
    Run all three extraction pipelines on *pdf_path*.

    The equations and workflow text are computed once and reused by
    `extract_pytorch_impl` to avoid redundant LLM calls.

    Returns
    -------
    dict with keys:
      'formulas_path'        – path to <paper>_formulas.md
      'workflow_path'        – path to <paper>_workflow.md
      'implementation_path'  – path to <paper>_implementation.py
    """
    print(f"\n{'='*60}")
    print(f"    FULL EXTRACTION: {os.path.basename(pdf_path)}")
    print(f"{'='*60}")

    # ── Shared PDF read (once) ─────────────────────────────────────────────
    print("\n  Reading PDF once for all pipelines …")
    pdf_text = _read_pdf_text(pdf_path)

    # ── Shared LLM calls (reused across pipelines) ─────────────────────────
    print(f"\n  Extracting raw equations ({OPENROUTER_MODEL}) …")
    raw_equations = _extract_raw_equations(pdf_text)

    print(f"\n  Extracting workflow steps ({OPENROUTER_MODEL}) …")
    workflow_steps = _extract_workflow_steps(pdf_text)

    # ── Pipeline 1 – formulas ──────────────────────────────────────────────
    print(f"\n  Explaining equations ({OPENROUTER_MODEL}) …")
    explained_formulas = _explain_equations(raw_equations, pdf_text)

    out_formulas = _make_output_path(pdf_path, "formulas", output_dir)
    paper_name   = os.path.basename(pdf_path)
    try:
        with open(out_formulas, "w", encoding="utf-8") as f:
            f.write(f"# Formula Explanations — {paper_name}\n\n")
            f.write(f"> Auto-generated by `extract_and_explain.py` · Model: `{OPENROUTER_MODEL}`\n\n")
            f.write("---\n\n## Raw Extracted Equations\n\n")
            f.write(raw_equations + "\n\n")
            f.write("---\n\n## Detailed Formula Explanations\n\n")
            f.write(explained_formulas + "\n")
        print(f"  Formulas saved →  {out_formulas}")
    except OSError as e:
        print(f"  [WARNING] Could not save formulas to disk: {e}")
        out_formulas = "(not saved — ephemeral filesystem)"

    # ── Pipeline 2 – workflow ──────────────────────────────────────────────
    print(f"\n  Elaborating workflow ({OPENROUTER_MODEL}) …")
    elaborated_workflow = _elaborate_workflow(workflow_steps, pdf_text)

    out_workflow = _make_output_path(pdf_path, "workflow", output_dir)
    try:
        with open(out_workflow, "w", encoding="utf-8") as f:
            f.write(f"# Workflow Explanation — {paper_name}\n\n")
            f.write(f"> Auto-generated by `extract_and_explain.py` · Model: `{OPENROUTER_MODEL}`\n\n")
            f.write("---\n\n## High-Level Workflow Steps\n\n")
            f.write(workflow_steps + "\n\n")
            f.write("---\n\n## Detailed Step-by-Step Breakdown\n\n")
            f.write(elaborated_workflow + "\n")
        print(f"  Workflow saved →  {out_workflow}")
    except OSError as e:
        print(f"  [WARNING] Could not save workflow to disk: {e}")
        out_workflow = "(not saved — ephemeral filesystem)"

    # ── Pipeline 3 – PyTorch implementation ───────────────────────────────
    print("\n  Generating PyTorch implementation via Code Gen Agent …")
    pytorch_code = _generate_pytorch_code(pdf_text, raw_equations, workflow_steps)

    # Strip accidental markdown fences
    pytorch_code = pytorch_code.strip()
    if pytorch_code.startswith("```"):
        lines = pytorch_code.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        pytorch_code = "\n".join(lines)

    out_impl = os.path.splitext(_make_output_path(pdf_path, "implementation", output_dir))[0] + ".py"
    try:
        with open(out_impl, "w", encoding="utf-8") as f:
            f.write(pytorch_code + "\n")
        print(f"  PyTorch implementation saved →  {out_impl}")
    except OSError as e:
        print(f"  [WARNING] Could not save implementation to disk: {e}")
        out_impl = "(not saved — ephemeral filesystem)"

    return {
        "formulas_path":        out_formulas,
        "workflow_path":        out_workflow,
        "implementation_path":  out_impl,
        # Content is returned inline so remote MCP clients can read it
        # regardless of whether the server-side file write succeeded.
        "formulas_content":        explained_formulas,
        "workflow_content":        elaborated_workflow,
        "implementation_content":  pytorch_code,
    }


# ──────────────────────────────────────────────────────────────────────────────
#  CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import os
    # Ensure arxiv_extract can be imported
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(_ROOT, "arxiv_extract"))
    try:
        from pdf_download import download_pdf
    except ImportError:
        print(" Could not import download_pdf from arxiv_extract. Check directory structure.")
        sys.exit(1)

    print("╔══════════════════════════════════════════╗")
    print("║  arXiv Paper Extractor & Explainer       ║")
    print("╚══════════════════════════════════════════╝\n")

    arxiv_id = input("Enter the arXiv paper ID: ").strip()
    if not arxiv_id:
        print(" Invalid arXiv ID.")
        sys.exit(1)

    print("\nWhat do you want to extract?")
    print("  [1] Formulas / Equations only")
    print("  [2] Workflow / Methodology only")
    print("  [3] PyTorch Implementation only")
    print("  [4] All three  (default)")
    choice = input("\nChoice [1/2/3/4]: ").strip() or "4"

    out_dir = input("\nOutput folder (press Enter to save under arxiv_papers/): ").strip().strip("'\"") or None

    try:
        print("\n Downloading PDF...")
        pdf_input = download_pdf(arxiv_id)
    except Exception as e:
        print(f" Download failed: {e}")
        sys.exit(1)

    if choice == "1":
        path = extract_formulas(pdf_input, out_dir)
        print(f"\n  Formula file        : {path}")
    elif choice == "2":
        path = extract_workflow(pdf_input, out_dir)
        print(f"\n  Workflow file        : {path}")
    elif choice == "3":
        path = extract_pytorch_impl(pdf_input, out_dir)
        print(f"\n  PyTorch impl file    : {path}")
    else:
        result = extract_all(pdf_input, out_dir)
        print(f"\n  Formula file        : {result['formulas_path']}")
        print(f"  Workflow file        : {result['workflow_path']}")
        print(f"  PyTorch impl file    : {result['implementation_path']}")
