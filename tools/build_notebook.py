"""Build the self-contained Colab notebook from this source tree.

Run from the repository root: python tools/build_notebook.py
The archive excludes notebooks so rebuilding cannot recursively embed itself.
"""

import base64
import io
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]


def main():
    buffer = io.BytesIO()
    roots = ["src", "tests", "docs", "reports", ".github", "tools"]
    standalone = ["pyproject.toml", "README.md", "LICENSE", "Dockerfile", "compose.yaml",
                  ".gitignore", ".dockerignore", ".env.example", "requirements-tested.txt",
                  "requirements-semantic-tested.txt"]
    paths = [ROOT / p for p in standalone if (ROOT / p).is_file()]
    for directory in roots:
        paths.extend(p for p in (ROOT / directory).rglob("*") if p.is_file()
                     and "__pycache__" not in p.parts and ".egg-info" not in str(p))
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(paths):
            archive.write(path, path.relative_to(ROOT))
    encoded = base64.b64encode(buffer.getvalue()).decode()
    notebook = nbf.v4.new_notebook(metadata={
        "colab": {"name": "EvidenceDesk_Colab.ipynb", "provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    })
    cells = []

    def md(text):
        cells.append(nbf.v4.new_markdown_cell(textwrap.dedent(text).strip()))

    def code(text, **metadata):
        cells.append(nbf.v4.new_code_cell(textwrap.dedent(text).strip(), metadata=metadata))

    md("""
    # EvidenceDesk — AI Engineering Portfolio
    ### Document questions with verifiable source quotations
    **Jaber Mobarak · Python / FastAPI / Hybrid Retrieval / Learned Embeddings / Evaluation**

    Choose **Runtime → Run all**. The default uses real MiniLM sentence embeddings and requires no API key.
    It downloads a small pretrained model. CPU is enough for retrieval; select a T4 GPU if enabling local Qwen.
    The first installation/model download can take several minutes. The interface appears at the end.

    This notebook includes the application source; you do not need a GitHub repository first.
    All sample policies are fictional. Do not upload private information to a shared notebook.
    Exact quotations establish source provenance, not truth or complete answer correctness.
    """)
    code('''
    #@title 1. Choose the demo mode
    USE_SEMANTIC = True #@param {type:"boolean"}
    USE_LOCAL_LLM = False #@param {type:"boolean"}
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    LOCAL_LLM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
    print("Learned embeddings:", USE_SEMANTIC, "| Local Qwen:", USE_LOCAL_LLM)
    ''')
    md("""
    ## Install the complete project
    The next cell extracts a source archive generated from the repository. It includes the API, UI, tests,
    authored data, and evaluation harness. No credentials or private files are embedded.
    """)
    code('''
    #@title 2. Extract and install (embedded source)
    import base64, io, os, subprocess, sys, zipfile
    from pathlib import Path
    PROJECT_ROOT = Path(os.getenv("ED_NOTEBOOK_ROOT", "/content/evidencedesk_portfolio")).resolve()
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    SOURCE_ARCHIVE = "''' + encoded + '''"
    with zipfile.ZipFile(io.BytesIO(base64.b64decode(SOURCE_ARCHIVE))) as archive:
        for name in archive.namelist():
            target = (PROJECT_ROOT / name).resolve()
            if not target.is_relative_to(PROJECT_ROOT):
                raise ValueError("Invalid archive member")
        archive.extractall(PROJECT_ROOT)
    extras = ".[dev,semantic]" if USE_SEMANTIC or USE_LOCAL_LLM else ".[dev]"
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-e", extras], cwd=PROJECT_ROOT, check=True)
    os.chdir(PROJECT_ROOT)
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    print("Installed source:", PROJECT_ROOT)
    ''', cellView="form")
    code('''
    #@title 3. Verify the software
    subprocess.run([sys.executable, "-m", "ruff", "check", "."], check=True)
    subprocess.run([sys.executable, "-m", "pytest", "-q"], check=True)
    ''')
    md("""
    ## Run a real retrieval demonstration
    The extractive mode uses exact sentences from the retrieved passages. MiniLM changes the vector branch
    from classical TF-IDF to learned dense embeddings. The `generation_backend` field tells you whether
    an LLM was actually used.
    """)
    code('''
    #@title 4. Build the index and ask questions
    import json
    from dataclasses import replace
    from evidencedesk.config import Settings
    from evidencedesk.schemas import Question
    from evidencedesk.service import EvidenceService
    from evidencedesk.store import Store
    settings = Settings(database=str(PROJECT_ROOT / "data/demo.sqlite3"),
                        embedding_model=EMBEDDING_MODEL if USE_SEMANTIC else "")
    service = EvidenceService(Store(settings.database), settings)
    service.load_demo()
    for question in ["How quickly must a critical incident be acknowledged?",
                     "What is the penalty for late expense claims?"]:
        result = service.ask(Question(question=question))
        print("\\nQUESTION:", question)
        print(result.model_dump_json(indent=2))
    ''')
    code('''
    #@title 5. Reproduce the benchmark and its failure cases
    from evidencedesk.evaluation import evaluate
    offline = evaluate("reports/colab-offline.json")
    report = evaluate("reports/colab-semantic.json", settings) if USE_SEMANTIC else offline
    print(json.dumps(report, indent=2))
    full = json.loads(Path("reports/colab-semantic.json" if USE_SEMANTIC else "reports/colab-offline.json").read_text())
    print("\\nFailed development cases:")
    for row in full["modes"]["hybrid"]["rows"]:
        if not row["passed"]:
            print(row["id"], row["question"], "→", row["actual"])
    print("\\nThis authored development set is not a held-out accuracy benchmark.")
    ''')
    md("""
    ## Optional local Qwen
    Enable `USE_LOCAL_LLM` in the first cell and run all to use this path. It downloads real model weights
    and starts a local model adapter. GPU is recommended; CPU generation may hit the 45-second API timeout.
    A 1.5B model is small and can choose the wrong evidence or return invalid JSON. Invalid quotations are
    rejected, but a valid source quote can still be irrelevant. Inspect the actual outputs.
    """)
    code('''
    #@title 6. Start Qwen when enabled
    import time
    import httpx
    local_model_process = None
    if USE_LOCAL_LLM:
        model_log = open(PROJECT_ROOT / "local-model.log", "w")
        local_model_process = subprocess.Popen(
            [sys.executable, "-m", "evidencedesk.local_model", "--model", LOCAL_LLM_MODEL],
            stdout=model_log, stderr=subprocess.STDOUT,
            env={**os.environ, "OMP_NUM_THREADS": "2"})
        for _attempt in range(600):
            if local_model_process.poll() is not None:
                raise RuntimeError(Path("local-model.log").read_text()[-4000:])
            try:
                response = httpx.get("http://127.0.0.1:11434/health", timeout=2, trust_env=False)
                if response.status_code == 200:
                    print(response.json())
                    break
            except httpx.HTTPError:
                pass
            time.sleep(1)
        else:
            raise TimeoutError("Model startup timed out; inspect local-model.log")
        service.settings = replace(settings, llm_model=LOCAL_LLM_MODEL)
        answer = service.ask(Question(question="What is the meal reimbursement limit?", use_llm=True))
        print(answer.model_dump_json(indent=2))
    else:
        print("Local Qwen disabled. Learned retrieval still uses a real model when USE_SEMANTIC is enabled.")
    ''')
    md("""
    ## Open the application
    Load your own PDF/TXT/Markdown documents, inspect the evidence, switch retrieval methods, and try
    unsupported questions. The sample workspace has already been loaded. The UI token is randomly generated
    for this runtime: paste the printed value into the **Workspace token** field. Clear token-containing outputs before sharing a running notebook.
    The inline preview uses Colab's port proxy; it is not a public deployment.
    """)
    code('''
    #@title 7. Launch the web application
    import secrets
    workspace_token = secrets.token_urlsafe(24)
    old_web_process = globals().get("web_process")
    if old_web_process is not None and old_web_process.poll() is None:
        old_web_process.terminate()
        old_web_process.wait(timeout=10)
    web_log = open(PROJECT_ROOT / "web.log", "w")
    server_env = {**os.environ, "ED_DATABASE": settings.database, "ED_API_TOKEN": workspace_token,
                  "ED_ALLOW_COLAB_EMBED": "true",
                  "ED_EMBEDDING_MODEL": settings.embedding_model,
                  "ED_LLM_MODEL": LOCAL_LLM_MODEL if USE_LOCAL_LLM else ""}
    web_process = subprocess.Popen([sys.executable, "-m", "evidencedesk.cli", "serve", "--port", "8000"],
                                   env=server_env, stdout=web_log, stderr=subprocess.STDOUT)
    for _attempt in range(60):
        if web_process.poll() is not None:
            raise RuntimeError(Path("web.log").read_text()[-4000:])
        try:
            response = httpx.get("http://127.0.0.1:8000/health", timeout=2, trust_env=False)
            if response.status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(.5)
    else:
        raise TimeoutError("Web application did not start")
    print("Workspace token (paste into the UI):", workspace_token)
    try:
        from google.colab import output
        output.serve_kernel_port_as_iframe(8000, height=1000)
    except ImportError:
        print("Open http://127.0.0.1:8000 in your local environment.")
    ''')
    md("""
    ## Keep your work
    Colab runtimes are temporary. Download your project before disconnecting. This archive includes source
    and reports; private documents, SQLite data, runtime logs, tokens, and caches are excluded.
    You can upload the source to a new GitHub repository and pin it on your profile.
    Read `docs/INTERVIEW_GUIDE.md` before using the project in an application.
    """)
    code('''
    #@title 8. Package source and measured reports
    export_path = PROJECT_ROOT.parent / "EvidenceDesk_Colab_Export.zip"
    excluded = {"data", ".git", ".venv", ".pytest_cache", ".ruff_cache", "__pycache__"}
    with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(PROJECT_ROOT.rglob("*")):
            relative = path.relative_to(PROJECT_ROOT)
            if path.is_file() and not any(part in excluded or part.endswith(".egg-info") for part in relative.parts):
                if path.suffix != ".log" and path.name != ".env":
                    archive.write(path, relative)
    print("Created:", export_path)
    # In Colab, uncomment to trigger a browser download:
    # from google.colab import files
    # files.download(str(export_path))
    ''')
    code('''
    #@title 9. Stop servers when finished
    # Set STOP_SERVERS = True and run this cell to release the runtime resources.
    STOP_SERVERS = False
    if STOP_SERVERS:
        for name in ("web_process", "local_model_process"):
            process = globals().get(name)
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
        print("Servers stopped.")
    ''')
    notebook.cells = cells
    destination = ROOT / "notebooks/EvidenceDesk_Colab.ipynb"
    destination.parent.mkdir(exist_ok=True)
    nbf.validate(notebook)
    nbf.write(notebook, destination)
    subprocess.run([sys.executable, "-m", "ruff", "check", str(destination), "--fix"], check=True)
    print(destination)


if __name__ == "__main__":
    main()
