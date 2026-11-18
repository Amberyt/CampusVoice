# AURA — Python Edition

A complete port of the Astra University voice assistant to a Python stack —
with the campus portal (student/teacher login, faculty data uploads) and
full **Hindi** support, matching the Next.js edition feature-for-feature.

## Stack

| Concern           | This edition                                   | Next.js edition                  |
| ----------------- | ---------------------------------------------- | -------------------------------- |
| HTTP framework    | FastAPI + Uvicorn                              | Next.js App Router API routes    |
| Database          | SQLite (stdlib `sqlite3`, zero deps)           | PostgreSQL via Drizzle ORM       |
| Intent engine     | `engine.py` (pure Python, rule-based NLP)      | `src/lib/engine.ts`              |
| Voice (STT/TTS)   | Browser Web Speech API — identical in any stack | Same                            |
| Frontend          | `static/index.html` (vanilla JS + canvas orb)  | React + Tailwind + Framer Motion |

## Run it

```bash
cd python
python3 -m venv .venv && source .venv/bin/activate   # optional but tidy
pip install -r requirements.txt
python main.py
```

Open <http://localhost:8000>. The SQLite database (`campus.db`) is created and
seeded on first run — delete it to reseed.

**Full step-by-step instructions (install, usage, verification, URLs/ports,
troubleshooting): see [`RUNNING.md`](./RUNNING.md).**

## Separate College Portal (multi-college mode)

Open <http://localhost:8000/college> to register a new institution or sign in as a college administrator. Each college receives a unique join code and a separate SQLite campus data file under `python/tenants/`. The College Data Portal is at `/college/portal`; it lets the institution upload its own rooms, courses, timetable, notices, events, and faculty using the existing plain-text Upload Studio (JSON is also supported).

The portal shows two join codes: students enter the college code exactly as shown (for example, `ABC123`); teachers enter the same code with the prefix `teach` (for example, `teachABC123`). During account creation at the main login screen, the college-code field is required. Their assistant then reads only that college's campus data. Use the one-tap demo accounts for the built-in Astra demo.

The built-in Astra demo keeps its sample data and the demo accounts below. Each new college starts with an empty campus dataset so it can load verified institution-specific information.

## Accounts & roles

The portal seeds two demo accounts (visible on the login screen):

| Role | Email | Password | Lands on |
| --- | --- | --- | --- |
| Student | `student@astra.edu` | `student123` | Voice agent |
| Teacher | `teacher@astra.edu` | `teacher123` | Faculty portal (`/teacher`) |

- Student sign-up uses the college join code. Teacher sign-up uses the same code with the prefix `teach` (e.g. `teachABC123`); a separate faculty invite code is no longer required. This prefix is predictable rather than a secure invitation token, so for production deployments use a separate staff-verification mechanism before exposing sensitive campus data.
- Teachers upload data from the portal: single datasets (rooms, courses,
  timetable, notices, events, faculty) with **merge/replace** modes, or a full
  **campus pack** that replaces everything in one transaction. Rows are
  validated one-by-one; bad rows are reported with fixes.

## Live clock and time-aware answers

The voice assistant and student dashboard show a live date/time display in India Standard Time (IST). The clock is refreshed every second. The backend uses the same `Asia/Kolkata` clock for timetable queries such as next class, active class, and rooms free right now. The assistant can also answer direct questions such as “What time is it?”, “What is today’s date?”, “अभी कितने बजे हैं?” and “आज की तारीख क्या है?”. Greetings adapt to the current time of day.

## Automatic reply language

The student assistant starts in **AUTO** mode. It detects English or Hindi from
what the user types and replies in that language. Hindi detection supports
Devanagari and common Romanized Hindi/Hinglish (for example, `meri next class
kab hai`). The header control cycles through `AUTO` → Hindi override → English
override → `AUTO` if a manual override is needed. The API accepts `lang: "auto"`,
`"en"`, or `"hi"`.

Voice input uses the browser Web Speech Recognition API, which requires a
recognition locale instead of exposing reliable multilingual auto-detection. In
AUTO mode, the UI uses the browser locale or the last detected response language,
and retries the other supported locale if no speech is detected. The current
Python edition has localized response templates for English and Hindi; other
languages require additional locale/response support.

## API

- `POST /api/auth/login | signup | logout`, `GET /api/auth/me` — account flows (cookie sessions)
- `POST /api/ask` — `{ "query": "…", "lang": "en|hi|auto" }` → structured answer
  (`text`, `speak`, `cards`, `suggestions`, `lang`) — sign-in required
- `GET /api/data` — full campus dataset (sign-in required)
- `POST /api/teacher/upload` — `{ dataset, mode: "merge"|"replace", rows:[…] }` or
  `{ dataset: "campus", pack: {…} }` (teacher or college administrator)
- `POST /api/teacher/notices`, `DELETE /api/teacher/notices?id=N` (teacher or college administrator)
- `GET /api/health` — liveness + seed trigger
- `POST /api/college/register` and `POST /api/college/login` — college administrator account and portal session
- `GET /api/college/me` — college administrator identity and institution join code
- `GET /college` — public college portal registration / login
- `GET /college/portal` — protected college data-management portal

## Files

- `main.py` — FastAPI app: auth, ask, data, teacher upload, static hosting
- `engine.py` — intent engine with Hindi support (no deps)
- `locales.py` — EN/HI response builders (no deps)
- `hindi.py` — Devanagari detection, token mapping, transliteration (no deps)
- `db.py` — SQLite schema, seed data, sessions/passwords, self-healing loader (no deps)
- `authlib.py` — session tokens on top of `db.py` (stdlib)
- `python/tenants/college_<id>.db` — generated per-college campus dataset database (created at runtime)
- `validate.py` — row-level upload validation, mirrors the Next.js zod schemas (stdlib)
- `static/index.html` — voice UI: login gate, canvas orb, chat console, EN/हिं toggle
- `static/premium-ui.css` and `static/premium-ui.js` — shared Premium University layouts, side navigation, theme system, and responsive styling
- `static/teacher.html` — faculty portal: stats, notice ops, upload studio
- `static/college.html` — institution registration / administrator sign-in
- `static/college_portal.html` — protected institution data-management portal

## Swapping SQLite for PostgreSQL

`db.py` uses parameterised queries throughout. To run on PostgreSQL, replace
`connect()` with a SQLAlchemy/psycopg connection and change `?` placeholders to
`%s` (or use SQLModel — the table shapes map 1:1).

## Where a Python stack shines beyond this port

- **Server-side ASR** — stream mic audio over a WebSocket to `faster-whisper` or Vosk
  instead of the browser recogniser
- **Neural TTS** — Piper / Coqui for higher-quality voices
- **LLM intent parsing** — run a local model (Ollama) or call an API to replace the
  rule-based `engine.py` classifier while keeping the same data layer

### Teacher Upload Studio — plain text input

The Upload Studio now defaults to **normal text**. Teachers can enter one record per paragraph using everyday wording, for example:

```text
D-120 is Lecture Hall D-120 in New Academic Block, floor 1, capacity 96, type lecture.
```

Use the **How to write it** help on each dataset card for examples. JSON remains available from the **JSON** input toggle for advanced/bulk imports.


## Automatic reply language

The student assistant starts in **AUTO** mode. It detects English or Hindi from the question and builds the response in that language. Hindi detection supports Devanagari and common Romanized Hindi/Hinglish (for example, `meri next class kab hai`). The small header control cycles through `AUTO` → Hindi override → English override → `AUTO` when a manual override is needed.

Voice input uses the browser's Web Speech Recognition API, which requires a recognition locale instead of providing reliable multilingual auto-detection. In AUTO mode the interface uses the browser locale or the last detected response language, and retries the other supported locale if no speech is detected. Typed questions are detected directly. The Python edition currently has localized response templates for English and Hindi; other languages need additional locale/response support.

## Student campus portal

After student sign-in, the app opens `/student`, a college-specific dashboard that reads actual course titles, course codes, departments, faculty, credits, semesters, timetable slots, notices, events, and rooms from the signed-in college's campus database. If the college has not uploaded data, the dashboard shows an empty state rather than making up course names. Use **Open Voice Assistant** to return to `/`.

## Automatic speech language behavior

In `AUTO` mode, each request is classified independently by the backend. Browser speech recognition no longer reuses the language of the previous response as the next microphone locale: it starts with `en-IN` each time and retries `hi-IN` if no speech is detected. Hindi/English response language is selected from the transcript for each question. Browser speech recognition is locale-based rather than truly multilingual, so exact recognition quality still depends on the browser's speech engine.

