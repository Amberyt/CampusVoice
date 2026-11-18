# AURA Python Edition — Complete Run Guide

End-to-end instructions to install, run, verify, use, and troubleshoot the Python
(FastAPI + SQLite) edition of AURA, the voice-based college assistant.

> **Using VS Code?** The repo includes ready-made `.vscode` launch configs and
> tasks — see [`VSCODE-SETUP.md`](./VSCODE-SETUP.md) for the one-press-F5 route.

---

## 1. What you're running

```
Browser (voice + UI)  ──►  FastAPI server (port 8000)  ──►  SQLite file campus.db
  static/index.html        main.py · engine.py             db.py (auto-created + seeded)
```

- The **voice layer** (speech recognition + spoken answers) runs entirely in the
  browser via the Web Speech API.
- The **server** answers natural-language campus questions with structured JSON
  (`text`, `speak`, `cards`, `suggestions`) and serves the UI.
- The **database** is a plain SQLite file in this folder. No services to install.

**Prerequisites**

| Requirement | Minimum | Recommended |
|---|---|---|
| Python | 3.9 | 3.11+ |
| pip | any recent | 23+ |
| Browser (for voice) | any (typing works) | Chrome / Edge for full voice |
| OS | Windows / macOS / Linux | — |

Check your versions:

```bash
python3 --version        # Windows: py --version
python3 -m pip --version
```

---

## 2. Quickstart (5 commands)

```bash
cd python                                  # 1. enter the edition folder
python3 -m venv .venv                      # 2. create an isolated environment
source .venv/bin/activate                  # 3. activate it  (Windows: .venv\Scripts\activate)
pip install -r requirements.txt            # 4. install FastAPI + Uvicorn (only 2 packages)
python main.py                             # 5. start the server
```

Expected output:

```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

Open **http://localhost:8000** in your browser. Done — the campus database was
created and seeded automatically on first boot.

Stop the server anytime with `Ctrl+C`.

---

## 3. Sign in and use it

1. Open `http://localhost:8000` — you'll land on the **login gate**. Two demo
   accounts are provided:
   - **Student** `student@astra.edu` / `student123` → the voice agent
   - **Teacher** `teacher@astra.edu` / `teacher123` → the Faculty Portal (`/teacher`)
2. As a **student**: click the glowing **orb** (or press **M**), allow mic
   permission, ask out loud. Toggle **EN ⇄ हिं** in the header to ask in Hindi —
   try *"आज कितनी क्लासें हैं?"* or type Devanagari and it answers in Hindi
   automatically.
3. As a **teacher**: the portal shows live campus stats, a quick
   **notice publisher**, and the **Upload Studio** (rooms, courses, timetable,
   notices, events, faculty, or a full campus pack — merge or replace, with
   row-level validation). Everything you add is answerable by AURA instantly.
4. To register an account, click **Create an account**. Students enter the college join code exactly as shown in the College Portal (e.g. `ABC123`). Teachers enter that same code prefixed with `teach` (e.g. `teachABC123`). No separate faculty invite code is needed.

### First-time voice usage
1. Open `http://localhost:8000` in **Chrome or Edge** for the full voice experience.
2. Click the glowing **orb** (or press **M** on your keyboard).
3. The browser will ask for microphone permission — click **Allow**.
   (The Web Speech API requires a secure context; `http://localhost` counts as one.)
4. Say something like:

   - *"What classes do I have today?"*
   - *"Where is DBMS held?"*
   - *"Free labs right now"*
   - *"Any exam notices?"*
   - *"When is the hackathon?"*
   - *"Dr. Mehta's office hours"*

5. AURA answers **out loud** and renders rich cards (schedule slots, room status,
   notices, events, faculty) in the console.

Shortcuts and controls:

| Control | Action |
|---|---|
| **M** | Start / stop listening (global) |
| **Esc** | Stop speaking / stop listening |
| Orb click while speaking | Interrupts the spoken answer (barge-in) |
| Speaker icon (top right) | Mute / unmute spoken answers |
| Input field | Type questions instead — works in every browser (including Firefox) |
| Suggestion chips | One-click follow-up questions |

Firefox has no built-in speech recognition; the app detects this and the mic icon
crosses out — typed questions work fully.

---

## 4. Verify your installation (60 seconds)

While the server runs, in a second terminal:

```bash
# 1. health check
curl -s http://localhost:8000/api/health
# -> {"ok":true,"engine":"python","db":"sqlite"}

# 2. ask a question headlessly
curl -s -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"where is DBMS held"}'
# -> {"ok":true,"intent":"courses.where","text":"Database Management Systems (CS-303) is held in B-102 ...", "cards":[...]}

# 3. browse the raw campus dataset
curl -s http://localhost:8000/api/data | head -c 400
```

If all three respond, everything — engine, database, and API — is working.

---

## 5. Configuration

| What | How |
|---|---|
| Port | `python main.py` uses **8000**. For another port, run via CLI instead: `uvicorn main:app --port 8001` |
| Host binding | `uvicorn main:app --host 0.0.0.0` (default) — reach it from other devices on your network via the machine's IP |
| Database location | Set the environment variable `AURA_DB`, e.g. `AURA_DB=/path/to/my.db python main.py` |
| Reset / reseed data | Stop the server, delete `campus.db`, start again. (Seed timestamps are relative to first run — reseed if event dates feel stale.) |
| Auto-reload for development | `python main.py` already runs with `reload=True`; edits to `.py` files restart the server |

---

## 6. File map

```
python/
├── main.py            FastAPI app — /api/ask, /api/data, /api/health, serves the UI
├── engine.py          Intent engine (no dependencies) — question → structured answer
├── db.py              SQLite schema + seed dataset (no dependencies)
├── static/
│   └── index.html     Voice UI — canvas orb, chat console, cards (no build step)
├── requirements.txt   fastapi + uvicorn (that's all)
├── README.md          Architecture overview
├── RUNNING.md         ← you are here
└── campus.db          (created on first run — safe to delete)
```

---

## 7. Troubleshooting

**`ModuleNotFoundError: No module named 'fastapi'`**
Your venv isn't active, or packages landed elsewhere. Reactivate
(`source .venv/bin/activate`) and re-run the install. Verify with
`python -c "import fastapi; print(fastapi.__version__)"`.

**`error: externally-managed-environment` (PEP 668)** — common on modern Debian/Ubuntu/Fedora
Best fix: use the venv shown above. If `python3 -m venv` itself fails with
*ensurepip is not available*, install it first:
`sudo apt install python3-venv` (then repeat quickstart).
Last-resort workaround without a venv: `pip install --user --break-system-packages -r requirements.txt`.

**Windows: `'python' is not recognized`**
Use the Python launcher: `py -m venv .venv`, `.venv\Scripts\activate`,
`py -m pip install -r requirements.txt`, `py main.py`.
Or install Python from python.org and tick **"Add python.exe to PATH"**.

**`Address already in use` / port 8000 taken**
Something else (maybe an older AURA instance) holds the port.
Run `uvicorn main:app --port 8001`, or find and stop the old process.

**The orb idles but never hears me**
- Use **Chrome or Edge** (Firefox/Safari lack `SpeechRecognition` — typing still works).
- Check the browser's site permissions: click the lock icon → Microphone → Allow.
- Headsets on macOS may need a system-level mic grant for the browser.

**Answers show on screen but nothing is spoken**
- Toggle the speaker icon in the header (mutes/unmutes).
- Some setups load voices lazily — ask one question, then again.
- CORS / cross-tab audio autoplay policies: click anywhere on the page first
  (browsers block audio before any user gesture).

**Events look like they're "in the past"**
Seed times are relative to the first boot. Delete `campus.db` and restart.

**Antivirus/firewall popup on first run**
That's Uvicorn binding to port 8000 — allow it (or bind to localhost only by
running `uvicorn main:app --host 127.0.0.1`).

---

## 8. Running it more seriously

- **Production-style start** (no reload, bind all interfaces):
  `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`
  (Keep 1 worker; the SQLite connection is process-local.)
- **Behind a name + HTTPS** (required for mic access outside localhost):
  put Caddy or nginx in front and terminate TLS; then the Web Speech API works
  from any device hitting the domain.
- **Swap SQLite for PostgreSQL**: `db.py` uses parameterised queries only —
  replace `connect()` with a psycopg/SQLAlchemy connection and change `?`
  placeholders to `%s` (SQLModel maps the tables 1:1).
- **Optional upgrades**: server-side ASR via `faster-whisper` over a WebSocket;
  neural TTS via Piper; LLM intent parsing via a local Ollama model — each plugs
  into the seams of `main.py`/`engine.py` without touching the UI.

---

## 9. Known limitations (by design)

- College, student and teacher accounts are supported; institutions must share their join code with users during sign-up.
- The intent engine is rule-based — great for campus facts, silent for general trivia
  (it tells you so gracefully).
- SQLite is intended for a local demo or single-node deployment; a production service should use robust backups, HTTPS, monitoring and a managed database strategy.

Everything else — timetable, rooms, live-occupancy, notices, events, faculty,
spoken answers, barge-in — is fully functional out of the box.

## College-specific portals

1. Start the server as usual and open `http://localhost:8000/college`.
2. Register the institution and its first administrator. The portal will sign you in and open `/college/portal`.
3. In the Upload Studio, use normal text to enter rooms, courses, timetable entries, notices, events, and faculty. Upload rooms and courses before timetable rows.
4. The dashboard displays both join codes. Students use the college code as shown (e.g. `ABC123`); teachers use that same code with `teach` prefixed (e.g. `teachABC123`). Enter the appropriate code in the College code field on the main login screen.
5. New institutions use a separate campus database at `python/tenants/college_<id>.db`; the Astra demo data and each other institution's records remain isolated.

The college-code field is required during sign-up. Use the built-in Astra demo buttons to sign in to the demo accounts; teacher registration no longer uses a separate faculty invite code. Since the teacher code is derived predictably from the student code, add a separate staff-verification mechanism before deploying with sensitive or production data.
