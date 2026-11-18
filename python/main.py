"""FastAPI application — AURA Python edition (login + teacher upload + Hindi).

Endpoints (mirror the Next.js edition):
  POST /api/auth/login | signup | logout         account flows
  GET  /api/auth/me                              current session user
  POST /api/ask     { "query": str, "lang"?: "en"|"hi"|"auto" }
  GET  /api/data                                 full campus dataset (guarded)
  POST /api/teacher/notices | DELETE?id=         notice ops (teacher)
  POST /api/teacher/upload                       dataset uploads (teacher)
  GET  /api/health                               liveness + seed trigger
  GET  /             voice UI (login-gated)
  GET  /teacher      faculty portal (login-gated, teacher)
  GET  /student      college-data dashboard (login-gated, student)
"""
from __future__ import annotations

import os
import re
import secrets
import threading
from datetime import timedelta

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

import authlib
import db
import engine
import validate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UI_BUILD = "premium-university-layout-redesign-2026-11-15"


def _page(filename: str) -> FileResponse:
    """Serve an HTML page without browser/proxy caching during local UI updates."""
    return FileResponse(
        os.path.join(STATIC_DIR, filename),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-CampusVoice-UI": UI_BUILD,
        },
    )

conn = db.connect()
db.ensure_seeded(conn)
DEFAULT_COLLEGE_ID = db.default_college_id(conn)
_TENANT_CONNECTIONS: dict[int, object] = {}
_TENANT_CONNECTIONS_LOCK = threading.Lock()

app = FastAPI(title="AURA — Multi-College Campus Assistant", version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SESSION_MAX_AGE_SEC = 7 * 86_400


def _err(status: int, message: str, **extra) -> JSONResponse:
    payload = {"ok": False, "error": message}
    payload.update(extra)
    return JSONResponse(status_code=status, content=payload)


def _current_user(request: Request) -> dict | None:
    try:
        return authlib.get_session_user(conn, request)
    except Exception:
        return None


def _campus_connection(user: dict):
    """Return the isolated campus database for the user's institution."""
    try:
        college_id = int(user.get("college_id") or DEFAULT_COLLEGE_ID)
    except (TypeError, ValueError):
        college_id = DEFAULT_COLLEGE_ID
    if college_id == DEFAULT_COLLEGE_ID:
        return conn
    with _TENANT_CONNECTIONS_LOCK:
        tenant = _TENANT_CONNECTIONS.get(college_id)
        if tenant is None:
            tenant = db.connect(db.tenant_db_path(college_id))
            db.ensure_tenant_schema(tenant)
            _TENANT_CONNECTIONS[college_id] = tenant
        return tenant


def _set_session_cookie(response: JSONResponse, token: str) -> None:
    cookie_secure = os.environ.get("COOKIE_SECURE", "false").strip().lower() in {"1", "true", "yes", "on"}
    response.set_cookie(
        authlib.SESSION_COOKIE, token,
        max_age=SESSION_MAX_AGE_SEC, httponly=True, samesite="lax",
        secure=cookie_secure, path="/",
    )


# ---------------------------------------------------------------- health
@app.get("/api/health")
def health() -> dict:
    db.ensure_seeded(conn)
    return {"ok": True, "engine": "python", "db": "sqlite", "ui_theme": "premium-university", "ui_build": UI_BUILD, "features": ["auth", "upload", "hindi", "auto-language", "multi-college", "premium-ui", "dark-mode"]}


# ------------------------------------------------------------------- auth
@app.post("/api/auth/login")
async def login(request: Request):
    db.ensure_seeded(conn)
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    want_role = "teacher" if body.get("role") == "teacher" else "student"
    if not email or not password:
        return _err(400, "Email and password are required.")
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not row or not db.verify_password(password, row["salt"], row["pass_hash"]):
        return _err(401, "Incorrect email or password.")
    if row["role"] != want_role:
        if row["role"] == "college_admin":
            return _err(403, "This is a college administrator account. Open /college to sign in to the College Portal.")
        return _err(403, f"This account is registered as a {row['role']}. Switch to the {row['role']} tab.")
    token, _expires = authlib.create_session(conn, row["id"])
    res = JSONResponse({"ok": True, "role": row["role"], "name": row["name"]})
    _set_session_cookie(res, token)
    return res


@app.post("/api/auth/signup")
async def signup(request: Request):
    db.ensure_seeded(conn)
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = str(body.get("email") or "").strip().lower()
    name = str(body.get("name") or "").strip()[:80]
    password = str(body.get("password") or "")
    role = "teacher" if body.get("role") == "teacher" else "student"
    submitted_code = str(body.get("collegeCode") or "").strip()
    if len(name) < 2:
        return _err(400, "Please enter your full name.")
    if not validate.EMAIL_RE.match(email):
        return _err(400, "That doesn't look like a valid email address.")
    if len(password) < 6:
        return _err(400, "Password must be at least 6 characters.")
    if not submitted_code:
        return _err(400, "College join code is required. Get it from your college administrator.")
    if role == "teacher":
        if not submitted_code.casefold().startswith("teach") or len(submitted_code) <= len("teach"):
            return _err(400, "For teacher registration, prefix your college code with 'teach' (example: teachABC123).")
        college_code = submitted_code[len("teach"):].strip().upper()
    else:
        college_code = submitted_code.upper()
    college = conn.execute("SELECT id,name FROM colleges WHERE code = ?", (college_code,)).fetchone()
    if not college and role == "student" and submitted_code.casefold().startswith("teach"):
        possible_base = submitted_code[len("teach"):].strip().upper()
        if possible_base and conn.execute("SELECT 1 FROM colleges WHERE code = ?", (possible_base,)).fetchone():
            return _err(400, "For student registration, use the college code without the 'teach' prefix.")
    if not college:
        expected = f"teach{college_code}" if role == "teacher" else college_code
        return _err(400, f"College code not found. Check the {('teacher' if role == 'teacher' else 'student')} join code: {expected}.")
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return _err(409, "An account with this email already exists — sign in instead.")
    pass_hash, salt = db.hash_password(password)
    cur = conn.execute(
        "INSERT INTO users (email,name,role,pass_hash,salt,created_at,college_id) VALUES (?,?,?,?,?,?,?)",
        (email, name, role, pass_hash, salt, __import__("datetime").datetime.now().isoformat(timespec="seconds"), college["id"]),
    )
    conn.commit()
    token, _expires = authlib.create_session(conn, cur.lastrowid)
    res = JSONResponse({"ok": True, "role": role, "name": name, "collegeName": college["name"], "collegeCode": college_code})
    _set_session_cookie(res, token)
    return res


@app.post("/api/college/register")
async def college_register(request: Request):
    """Register a college and its first college administrator."""
    db.ensure_seeded(conn)
    try:
        body = await request.json()
    except Exception:
        body = {}
    college_name = str(body.get("collegeName") or "").strip()[:120]
    admin_name = str(body.get("adminName") or "").strip()[:80]
    email = str(body.get("email") or "").strip().lower()
    contact_email = str(body.get("contactEmail") or email).strip().lower()
    password = str(body.get("password") or "")
    if len(college_name) < 3:
        return _err(400, "Enter a college or institution name (at least 3 characters).")
    if len(admin_name) < 2:
        return _err(400, "Enter the administrator's full name.")
    if not validate.EMAIL_RE.match(email):
        return _err(400, "Enter a valid administrator email address.")
    if contact_email and not validate.EMAIL_RE.match(contact_email):
        return _err(400, "Enter a valid college contact email address.")
    if len(password) < 8:
        return _err(400, "Choose a password with at least 8 characters.")
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        return _err(409, "An account with this administrator email already exists. Sign in or use a different email.")
    # Create a readable, institution-specific join code without exposing a sequential tenant ID.
    base = re.sub(r"[^A-Z0-9]", "", college_name.upper())[:6] or "CAMPUS"
    code = base
    while conn.execute("SELECT 1 FROM colleges WHERE code = ?", (code,)).fetchone():
        code = (base[:5] + secrets.token_hex(2).upper())[:9]
    pass_hash, salt = db.hash_password(password)
    created_at = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    try:
        conn.execute("BEGIN IMMEDIATE")
        cur = conn.execute(
            "INSERT INTO colleges (name,code,contact_email,created_at) VALUES (?,?,?,?)",
            (college_name, code, contact_email, created_at),
        )
        college_id = int(cur.lastrowid)
        cur_user = conn.execute(
            "INSERT INTO users (email,name,role,pass_hash,salt,created_at,college_id) VALUES (?,?,?,?,?,?,?)",
            (email, admin_name, "college_admin", pass_hash, salt, created_at, college_id),
        )
        tenant = db.connect(db.tenant_db_path(college_id))
        db.ensure_tenant_schema(tenant)
        tenant.close()
        conn.commit()
    except Exception as exc:
        conn.rollback()
        print(f"[college/register] failed: {exc}")
        return _err(500, "Could not create the college portal. Please retry with the same details after checking whether the account already exists.")
    token, _expires = authlib.create_session(conn, cur_user.lastrowid)
    res = JSONResponse({"ok": True, "role": "college_admin", "name": admin_name, "collegeName": college_name, "collegeCode": code})
    _set_session_cookie(res, token)
    return res


@app.post("/api/college/login")
async def college_login(request: Request):
    db.ensure_seeded(conn)
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = str(body.get("email") or "").strip().lower()
    password = str(body.get("password") or "")
    if not email or not password:
        return _err(400, "Email and password are required.")
    row = conn.execute("SELECT * FROM users WHERE email = ? AND role = 'college_admin'", (email,)).fetchone()
    if not row or not db.verify_password(password, row["salt"], row["pass_hash"]):
        return _err(401, "Incorrect college administrator email or password.")
    token, _expires = authlib.create_session(conn, row["id"])
    res = JSONResponse({"ok": True, "role": "college_admin", "name": row["name"]})
    _set_session_cookie(res, token)
    return res


@app.get("/api/college/me")
def college_me(request: Request):
    user = _current_user(request)
    if not user or user["role"] != "college_admin":
        return _err(401, "College administrator sign-in required.")
    return {"ok": True, "user": user}


@app.post("/api/auth/logout")
async def logout(request: Request):
    token = request.cookies.get(authlib.SESSION_COOKIE)
    if token:
        try:
            authlib.destroy_session(conn, token)
        except Exception:
            pass
    res = JSONResponse({"ok": True})
    res.delete_cookie(authlib.SESSION_COOKIE, path="/")
    return res


@app.get("/api/auth/me")
def me(request: Request):
    user = _current_user(request)
    if not user:
        return _err(401, "Not signed in.")
    return {"ok": True, "user": user}


# -------------------------------------------------------------------- ask
@app.post("/api/ask")
async def ask(request: Request):
    user = _current_user(request)
    if not user:
        return _err(401, "Your session has expired — please sign in again.", intent="auth")
    try:
        body = await request.json()
    except Exception:
        body = {}
    query = str(body.get("query") or "").strip()[:300]
    lang = body.get("lang") if body.get("lang") in ("en", "hi", "auto") else "auto"
    if not query:
        return _err(400, "I didn't catch a question. Try speaking or typing something like \"What classes do I have today?\"")
    try:
        campus_db = _campus_connection(user)
        campus = db.load_campus(campus_db, seed=(int(user.get("college_id") or DEFAULT_COLLEGE_ID) == DEFAULT_COLLEGE_ID))
        return engine.answer_question(query, campus, lang)
    except Exception as exc:  # pragma: no cover
        print(f"[/api/ask] failed: {exc}")
        return _err(500, "The campus database hiccuped for a moment. Give me one more try in a second.")


# ------------------------------------------------------------------- data
@app.get("/api/data", response_model=None)
def data(request: Request):
    user = _current_user(request)
    if not user:
        return _err(401, "Sign in required.")
    campus_db = _campus_connection(user)
    campus = db.load_campus(campus_db, seed=(int(user.get("college_id") or DEFAULT_COLLEGE_ID) == DEFAULT_COLLEGE_ID))
    now = engine.campus_now()
    courses_out = []
    for c in sorted(campus["courses"], key=lambda x: x["code"]):
        slots = sorted(
            [t for t in campus["timetable"] if t["course_code"] == c["code"]],
            key=lambda t: (t["day_of_week"], t["start_time"]),
        )
        row = dict(c)
        row["slots"] = slots
        courses_out.append(row)
    notices = sorted(
        campus["notices"], key=lambda n: (not n["pinned"], -n["published_at"].timestamp())
    )
    events = sorted(campus["events"], key=lambda e: e["starts_at"])
    return {
        "ok": True,
        "college": {"name": user.get("college_name", "Astra University"), "code": user.get("college_code", "ASTRA")},
        "now": {"day": now["day"], "minutes": now["minutes"], "iso": now["date"].isoformat()},
        "rooms": sorted(campus["rooms"], key=lambda r: r["code"]),
        "courses": courses_out,
        "notices": [{**n, "published_at": n["published_at"].isoformat()} for n in notices],
        "events": [{**e, "starts_at": e["starts_at"].isoformat()} for e in events],
        "faculty": sorted(campus["faculty"], key=lambda f: f["name"]),
    }


# ----------------------------------------------------------------- teacher
def _require_teacher(request: Request) -> dict | JSONResponse:
    user = _current_user(request)
    if not user:
        return _err(401, "Sign in required.")
    if user["role"] not in ("teacher", "college_admin"):
        return _err(403, "Teacher or college administrator access only.")
    return user


def _apply_dataset(dataset: str, mode: str, rows: list, campus_db=None):
    """Apply validated rows to the specified tenant database."""
    target = campus_db or conn
    if dataset == "rooms":
        if mode == "replace":
            target.execute("DELETE FROM timetable")
            target.execute("DELETE FROM rooms")
        for r in rows:
            target.execute(
                "INSERT INTO rooms (code,name,block,floor,capacity,type,meta) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(code) DO UPDATE SET name=excluded.name, block=excluded.block, floor=excluded.floor, "
                "capacity=excluded.capacity, type=excluded.type, meta=excluded.meta",
                (r["code"], r["name"], r["block"], r["floor"], r["capacity"], r["type"], r["meta"]),
            )
    elif dataset == "courses":
        if mode == "replace":
            target.execute("DELETE FROM timetable")
            target.execute("DELETE FROM courses")
        for r in rows:
            target.execute(
                "INSERT INTO courses (code,title,aliases,professor,department,credits,semester,section,color) "
                "VALUES (?,?,?,?,?,?,5,'A',?) "
                "ON CONFLICT(code) DO UPDATE SET title=excluded.title, aliases=excluded.aliases, "
                "professor=excluded.professor, department=excluded.department, credits=excluded.credits, color=excluded.color",
                (r["code"], r["title"], r["aliases"], r["professor"], r["department"], r["credits"], r["color"]),
            )
    elif dataset == "timetable":
        if mode == "replace":
            target.execute("DELETE FROM timetable")
        for r in rows:
            target.execute(
                "INSERT INTO timetable (course_code,room_code,day_of_week,start_time,end_time) VALUES (?,?,?,?,?)",
                (r["courseCode"], r["roomCode"], r["dayOfWeek"], r["startTime"], r["endTime"]),
            )
    elif dataset == "notices":
        if mode == "replace":
            target.execute("DELETE FROM notices")
        for r in rows:
            target.execute(
                "INSERT INTO notices (title,body,category,pinned,published_at) VALUES (?,?,?,?,?)",
                (r["title"], r["body"], r["category"], r["pinned"], r["published_at"].isoformat(timespec="seconds")),
            )
    elif dataset == "events":
        if mode == "replace":
            target.execute("DELETE FROM events")
        for r in rows:
            target.execute(
                "INSERT INTO events (title,description,location,category,organizer,starts_at) VALUES (?,?,?,?,?,?)",
                (r["title"], r["description"], r["location"], r["category"], r["organizer"], r["starts_at"].isoformat(timespec="seconds")),
            )
    elif dataset == "faculty":
        if mode == "replace":
            target.execute("DELETE FROM faculty")
        for r in rows:
            target.execute(
                "INSERT INTO faculty (name,title,department,email,office,office_hours,tags) VALUES (?,?,?,?,?,?,?)",
                (r["name"], r["title"], r["department"], r["email"], r["office"], r["office_hours"], r["tags"]),
            )
    else:
        return 0, f"Unknown dataset {dataset!r}"
    target.commit()
    return len(rows), None


@app.post("/api/teacher/upload")
async def teacher_upload(request: Request):
    guard = _require_teacher(request)
    if isinstance(guard, JSONResponse):
        return guard
    campus_db = _campus_connection(guard)
    try:
        body = await request.json()
    except Exception:
        return _err(400, "Body must be valid JSON.")
    dataset = str(body.get("dataset") or "").lower()
    mode = "replace" if body.get("mode") == "replace" else "merge"

    if dataset == "campus":
        pack = body.get("pack") if isinstance(body.get("pack"), dict) else (body.get("rows") if isinstance(body.get("rows"), dict) else None)
        if not pack:
            return _err(400, "Pack must be a JSON object with dataset arrays.")
        if not any(pack.get(k) for k in validate.VALIDATORS):
            return _err(400, "Pack must contain at least one non-empty dataset array.")
        parsed: dict[str, list] = {}
        details: list[str] = []
        for key, validator in validate.VALIDATORS.items():
            raw_rows = pack.get(key) or []
            if not isinstance(raw_rows, list):
                details.append(f"{key}: must be an array")
                continue
            values, errors = validator(raw_rows)
            if errors:
                details.extend(f"[{key}] {e}" for e in errors[:5])
            parsed[key] = values
        if details:
            return _err(400, "Campus pack failed validation.", details=details[:12])
        # cross-reference check
        course_codes = {r["code"] for r in parsed["courses"]}
        room_codes = {r["code"] for r in parsed["rooms"]}
        biz = []
        for i, t in enumerate(parsed["timetable"]):
            if t["courseCode"] not in course_codes:
                biz.append(f"timetable row {i + 1}: unknown courseCode {t['courseCode']}")
            if t["roomCode"] not in room_codes:
                biz.append(f"timetable row {i + 1}: unknown roomCode {t['roomCode']}")
        if biz:
            return _err(400, "Campus pack has broken references.", details=biz[:12])
        for table in ("timetable", "notices", "events", "faculty", "courses", "rooms"):
            campus_db.execute(f"DELETE FROM {table}")
        campus_db.commit()
        applied = 0
        for key, rows in parsed.items():
            if rows:
                n, err = _apply_dataset(key, "merge", rows, campus_db)
                if err:
                    return _err(500, err)
                applied += n
        return {"ok": True, "dataset": dataset, "mode": "replace", "applied": applied}

    validator = validate.VALIDATORS.get(dataset)
    if not validator:
        return _err(400, f"Unknown dataset {dataset!r}.")
    raw_rows = body.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        return _err(400, "Expected a non-empty JSON array of rows.")
    values, errors = validator(raw_rows)
    if errors:
        return _err(400, f"{dataset} rows failed validation.", details=errors[:12])

    if dataset == "timetable":
        course_set = {r["code"] for r in campus_db.execute("SELECT code FROM courses").fetchall()}
        room_set = {r["code"] for r in campus_db.execute("SELECT code FROM rooms").fetchall()}
        biz = []
        for i, t in enumerate(values):
            if t["courseCode"] not in course_set:
                biz.append(f"row {i + 1}: course {t['courseCode']} not found — upload it first")
            if t["roomCode"] not in room_set:
                biz.append(f"row {i + 1}: room {t['roomCode']} not found — upload it first")
        if biz:
            return _err(400, "Timetable references unknown codes.", details=biz[:12])

    applied, err = _apply_dataset(dataset, mode, values, campus_db)
    if err:
        return _err(500, err)
    return {"ok": True, "dataset": dataset, "mode": mode, "applied": applied}


@app.post("/api/teacher/upload-text")
async def teacher_upload_text(request: Request):
    """Accept teacher-friendly prose and route it through the same validators."""
    guard = _require_teacher(request)
    if isinstance(guard, JSONResponse):
        return guard
    campus_db = _campus_connection(guard)
    try:
        body = await request.json()
    except Exception:
        return _err(400, "Body must be valid JSON.")
    dataset = str(body.get("dataset") or "").lower().strip()
    mode = "replace" if body.get("mode") == "replace" else "merge"
    text = str(body.get("text") or "").strip()
    parsed, parse_errors = validate.parse_text(dataset, text)
    if parse_errors:
        return _err(400, "Could not understand the text input.", details=parse_errors[:12])

    if dataset == "campus":
        pack = parsed if isinstance(parsed, dict) else {}
        if not any(pack.get(k) for k in validate.VALIDATORS):
            return _err(400, "Campus pack must contain at least one dataset section.")
        checked: dict[str, list] = {}
        details: list[str] = []
        for key, validator in validate.VALIDATORS.items():
            raw_rows = pack.get(key) or []
            if not isinstance(raw_rows, list):
                details.append(f"{key}: must contain one or more text rows")
                continue
            values, errors = validator(raw_rows)
            if errors:
                details.extend(f"[{key}] {e}" for e in errors[:5])
            checked[key] = values
        if details:
            return _err(400, "Campus text failed validation.", details=details[:12])
        course_codes = {r["code"] for r in checked.get("courses", [])}
        room_codes = {r["code"] for r in checked.get("rooms", [])}
        biz = []
        for i, t in enumerate(checked.get("timetable", [])):
            if t["courseCode"] not in course_codes:
                biz.append(f"timetable row {i + 1}: unknown courseCode {t['courseCode']}")
            if t["roomCode"] not in room_codes:
                biz.append(f"timetable row {i + 1}: unknown roomCode {t['roomCode']}")
        if biz:
            return _err(400, "Campus text has broken references.", details=biz[:12])
        for table in ("timetable", "notices", "events", "faculty", "courses", "rooms"):
            campus_db.execute(f"DELETE FROM {table}")
        campus_db.commit()
        applied = 0
        for key, rows in checked.items():
            if rows:
                n, err = _apply_dataset(key, "merge", rows, campus_db)
                if err:
                    return _err(500, err)
                applied += n
        return {"ok": True, "dataset": dataset, "mode": "replace", "applied": applied, "input": "text"}

    validator = validate.VALIDATORS.get(dataset)
    if not validator:
        return _err(400, f"Unknown dataset {dataset!r}.")
    if not isinstance(parsed, list) or not parsed:
        return _err(400, "No records were found in the text input.")
    values, errors = validator(parsed)
    if errors:
        return _err(400, f"{dataset} rows failed validation.", details=errors[:12])
    if dataset == "timetable":
        course_set = {r["code"] for r in campus_db.execute("SELECT code FROM courses").fetchall()}
        room_set = {r["code"] for r in campus_db.execute("SELECT code FROM rooms").fetchall()}
        biz = []
        for i, t in enumerate(values):
            if t["courseCode"] not in course_set:
                biz.append(f"row {i + 1}: course {t['courseCode']} not found — upload it first")
            if t["roomCode"] not in room_set:
                biz.append(f"row {i + 1}: room {t['roomCode']} not found — upload it first")
        if biz:
            return _err(400, "Timetable references unknown codes.", details=biz[:12])
    applied, err = _apply_dataset(dataset, mode, values, campus_db)
    if err:
        return _err(500, err)
    return {"ok": True, "dataset": dataset, "mode": mode, "applied": applied, "input": "text"}


@app.post("/api/teacher/notices")
async def teacher_post_notice(request: Request):
    guard = _require_teacher(request)
    if isinstance(guard, JSONResponse):
        return guard
    try:
        body = await request.json()
    except Exception:
        body = {}
    campus_db = _campus_connection(guard)
    values, errors = validate.notices([body])
    if errors:
        return _err(400, "Notice failed validation.", details=errors[:8])
    n = values[0]
    cur = campus_db.execute(
        "INSERT INTO notices (title,body,category,pinned,published_at) VALUES (?,?,?,?,?)",
        (n["title"], n["body"], n["category"], n["pinned"], n["published_at"].isoformat(timespec="seconds")),
    )
    campus_db.commit()
    return {"ok": True, "id": cur.lastrowid}


@app.delete("/api/teacher/notices")
def teacher_delete_notice(request: Request, id: int = 0):
    guard = _require_teacher(request)
    if isinstance(guard, JSONResponse):
        return guard
    if id <= 0:
        return _err(400, "Valid id is required.")
    campus_db = _campus_connection(guard)
    campus_db.execute("DELETE FROM notices WHERE id = ?", (id,))
    campus_db.commit()
    return {"ok": True}


# ------------------------------------------------------------------ pages
@app.get("/")
def index() -> FileResponse:
    return _page("index.html")


@app.get("/student", response_model=None)
def student_page(request: Request):
    user = _current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)
    if user["role"] == "teacher":
        return RedirectResponse(url="/teacher", status_code=303)
    if user["role"] == "college_admin":
        return RedirectResponse(url="/college/portal", status_code=303)
    return _page("student.html")


@app.get("/teacher", response_model=None)
def teacher_page(request: Request):
    user = _current_user(request)
    if user and user["role"] == "college_admin":
        return RedirectResponse(url="/college/portal", status_code=303)
    if not user or user["role"] != "teacher":
        return RedirectResponse(url="/", status_code=303)
    return _page("teacher.html")


@app.get("/college")
def college_page(request: Request):
    user = _current_user(request)
    if user and user["role"] == "college_admin":
        return RedirectResponse(url="/college/portal", status_code=303)
    return _page("college.html")


@app.get("/college/portal", response_model=None)
def college_portal_page(request: Request):
    user = _current_user(request)
    if not user or user["role"] != "college_admin":
        return RedirectResponse(url="/college", status_code=303)
    return _page("college_portal.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
