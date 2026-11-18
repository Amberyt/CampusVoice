# Running AURA in VS Code — Step-by-Step

The repo ships with `.vscode/launch.json`, `.vscode/tasks.json`, and
`.vscode/extensions.json`, so once your interpreter is set up, running is a
single keypress (**F5**).

---

## Step 1 — Open the project

`File → Open Folder…` and select the **project root** (the folder containing
`python/` and `src/`). Opening the root (not just `python/`) keeps the provided
`.vscode` configs active.

## Step 2 — Install the Python extension

VS Code will show a **"Do you want to install recommended extensions?"** toast —
click **Install**. It adds:

- **Python** (`ms-python.python`)
- **Python Debugger** (`ms-python.debugpy`)

(Or search "Python" in the Extensions panel and install the official Microsoft one.)

## Step 3 — Create the virtual environment

Open the integrated terminal (**View → Terminal**, or `` Ctrl+` ``) and run:

```bash
python3 -m venv python/.venv
# Windows:  python -m venv python\.venv
```

VS Code will detect the new environment and pop up:
**"We noticed a new environment has been created. Do you want to select it?"** →
click **Yes**.

If no toast appears: `Ctrl+Shift+P` → **Python: Select Interpreter** → pick the
entry that reads something like `Python 3.x ('.venv') ./python/.venv/bin/python`.

## Step 4 — Install dependencies

```bash
# macOS / Linux — use the venv's pip directly (no activation needed):
python/.venv/bin/pip install -r requirements.txt

# Windows:
python\.venv\Scripts\pip install -r requirements.txt
```

(Working directory here is the project *root*; the `-r` path resolves into
`python/requirements.txt` if you `cd python` first — either way works.)

## Step 5 — Run it — pick any of the three ways

**A. Press F5** (debug mode — recommended)
Two configs are provided in the Run & Debug dropdown:

- **AURA: FastAPI (uvicorn)** — launches `main:app` under the debugger
- **AURA: main.py** — runs the `__main__` block (same server, with `--reload`)

Once you see `Uvicorn running on http://0.0.0.0:8000`, open
**http://localhost:8000** in Chrome or Edge.

**B. Terminal → Run Task…** → **AURA: run server**
This chains the install task (`AURA: install dependencies`) then starts the
server in the integrated terminal.

**C. Plain terminal**

```bash
cd python
..\\.venv\\Scripts\\python main.py    # Windows
python/.venv/bin/python main.py        # …or, from root, macOS/Linux:
python main.py                         # if the venv is activated
```

## Step 6 — Debugging tips (this is where VS Code shines)

- Click the gutter next to any line in `engine.py` (e.g. inside
  `answer_question`) to set a **breakpoint**, press F5, then hit
  `http://localhost:8000/api/ask` with a question (curl or the UI) — execution
  pauses and you can inspect `q`, `day_hit`, `course_hits`, etc.
- Set breakpoints in `main.py` inside `ask()` or `data()` to watch FastAPI flows.
- Use the **Debug Console** to evaluate expressions mid-breakpoint,
  e.g. `day_entries(4)` to list Thursday's slots.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `No module named 'fastapi'` when running | Wrong interpreter. Re-did Step 3's **Select Interpreter** and choose the `.venv` one (check the status bar bottom-left). |
| `F5` asks to "Select a debug configuration" | The Python extension isn't installed/enabled, or you opened `python/` instead of the project root. |
| Task "AURA: run server" fails at install step | Create the venv first (Step 3) — tasks assume `python/.venv` exists. |
| Port 8000 busy | Edit `python/main.py` port, or kill the older server instance. |
| Bulb/terminal icon shows `.venv` inactive in terminal | Terminals opened *before* interpreter selection are stale — kill the panel and open a fresh one. |
| Permission popup on first launch | That's Uvicorn binding port 8000; allow it. |

## Mobile / remote note

Running inside **WSL, Containers, SSH, or Codespaces**? Same steps — VS Code
auto-forwards port 8000 to your local browser (check the **PORTS** panel; if
missing, right-click → Forward Port 8000).


## College onboarding and custom campus data

For a new institution, start the **Python/FastAPI** server and open
`http://localhost:8000/college`. Register the institution and its first
administrator, then use the automatically opened `/college/portal` to upload
campus data in normal text. The portal shows a Student join code and a Teacher
join code. Students enter the college code as shown; teachers enter the same
code with `teach` prefixed (for example, `teachABC123`) in the College code
field during account creation. Each institution's campus records are kept in its own SQLite file under
`python/tenants/`, while the built-in Astra demo retains its seeded records.

This multi-college portal feature is implemented in the Python/FastAPI edition.
For this workflow, run `python/main.py` and use port `8000` (not the separate
Next.js development server on port `3000`).
