"""Row-level upload validation for the teacher studio — stdlib only.

Each validator returns (values, errors). Errors are row-addressed strings,
e.g. "row 2 · code: must be 1-12 chars", mirroring the Next.js zod details.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

TIME_RE = re.compile(r"^\d{1,2}:\d{2}$")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

ROOM_TYPES = {"lecture", "lab", "seminar", "hall", "facility"}
NOTICE_CATS = {"urgent", "exams", "placements", "events", "sports", "facility", "admin"}
EVENT_CATS = {"tech", "club", "cultural", "sports", "social"}


def _pad_time(t: str) -> str:
    h, m = t.split(":", 1)
    return f"{min(23, int(h)):02d}:{min(59, int(m)):02d}"


def _err(idx: int, field: str | None, msg: str) -> str:
    return f"row {idx + 1}{' · ' + field if field else ''}: {msg}"


def _num(v, lo, hi, default=None):
    try:
        n = int(float(v))
        return lo <= n <= hi, n
    except (TypeError, ValueError):
        if default is not None:
            return True, default
        return False, 0


def _upper(v) -> str:
    return str(v or "").strip().upper()


def rooms(rows: list) -> tuple[list[dict], list[str]]:
    out, errors = [], []
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            errors.append(_err(i, None, "row must be an object"))
            continue
        code = _upper(r.get("code"))
        name = str(r.get("name") or "").strip()
        block = str(r.get("block") or "").strip()
        meta = r.get("meta")
        if not (1 <= len(code) <= 12):
            errors.append(_err(i, "code", "required, 1-12 chars"))
        if len(name) < 2:
            errors.append(_err(i, "name", "required, 2+ chars"))
        if len(block) < 2:
            errors.append(_err(i, "block", "required, 2+ chars"))
        okf, floor = _num(r.get("floor", 0), 0, 20, 0)
        okc, capacity = _num(r.get("capacity", 0), 0, 3000, 0)
        if not okf:
            errors.append(_err(i, "floor", "integer 0-20"))
        if not okc:
            errors.append(_err(i, "capacity", "integer 0-3000"))
        rtype = str(r.get("type") or "lecture")
        if rtype not in ROOM_TYPES:
            errors.append(_err(i, "type", f"one of {sorted(ROOM_TYPES)}"))
        if meta is not None and not isinstance(meta, str):
            errors.append(_err(i, "meta", "string or null"))
        if errors and any(e.startswith(f"row {i + 1}") for e in errors):
            continue
        out.append({"code": code, "name": name, "block": block, "floor": floor, "capacity": capacity, "type": rtype, "meta": meta})
    return out, errors


def courses(rows: list) -> tuple[list[dict], list[str]]:
    out, errors = [], []
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            errors.append(_err(i, None, "row must be an object"))
            continue
        code = _upper(r.get("code"))
        title = str(r.get("title") or "").strip()
        prof = str(r.get("professor") or "").strip()
        dept = str(r.get("department") or "").strip()
        color = str(r.get("color") or "#22d3ee").strip()
        if len(code) < 2:
            errors.append(_err(i, "code", "required, 2+ chars"))
        if len(title) < 2:
            errors.append(_err(i, "title", "required, 2+ chars"))
        if len(prof) < 2:
            errors.append(_err(i, "professor", "required"))
        if len(dept) < 2:
            errors.append(_err(i, "department", "required"))
        if not HEX_RE.match(color):
            errors.append(_err(i, "color", "hex color like #22d3ee"))
        okcr, credits = _num(r.get("credits", 3), 1, 12, 3)
        if not okcr:
            errors.append(_err(i, "credits", "integer 1-12"))
        if errors and any(e.startswith(f"row {i + 1}") for e in errors):
            continue
        out.append({
            "code": code, "title": title, "aliases": str(r.get("aliases") or "").strip(),
            "professor": prof, "department": dept, "credits": credits, "color": color,
        })
    return out, errors


def timetable(rows: list) -> tuple[list[dict], list[str]]:
    out, errors = [], []
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            errors.append(_err(i, None, "row must be an object"))
            continue
        ccode = _upper(r.get("courseCode"))
        rcode = _upper(r.get("roomCode"))
        st = str(r.get("startTime") or "").strip()
        en = str(r.get("endTime") or "").strip()
        okd, day = _num(r.get("dayOfWeek"), 1, 7)
        if len(ccode) < 2:
            errors.append(_err(i, "courseCode", "required"))
        if not rcode:
            errors.append(_err(i, "roomCode", "required"))
        if not okd:
            errors.append(_err(i, "dayOfWeek", "integer 1=Mon … 7=Sun"))
        if not TIME_RE.match(st):
            errors.append(_err(i, "startTime", "use HH:MM, e.g. 09:30"))
        if not TIME_RE.match(en):
            errors.append(_err(i, "endTime", "use HH:MM, e.g. 10:25"))
        if errors and any(e.startswith(f"row {i + 1}") for e in errors):
            continue
        st_n, en_n = _pad_time(st), _pad_time(en)
        if st_n >= en_n:
            errors.append(_err(i, "endTime", "must be after startTime"))
            continue
        out.append({"courseCode": ccode, "roomCode": rcode, "dayOfWeek": day, "startTime": st_n, "endTime": en_n})
    return out, errors


def notices(rows: list) -> tuple[list[dict], list[str]]:
    out, errors = [], []
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            errors.append(_err(i, None, "row must be an object"))
            continue
        title = str(r.get("title") or "").strip()
        body = str(r.get("body") or "").strip()
        cat = str(r.get("category") or "admin")
        if len(title) < 3:
            errors.append(_err(i, "title", "required, 3+ chars"))
        if len(body) < 3:
            errors.append(_err(i, "body", "required, 3+ chars"))
        if cat not in NOTICE_CATS:
            errors.append(_err(i, "category", f"one of {sorted(NOTICE_CATS)}"))
        if errors and any(e.startswith(f"row {i + 1}") for e in errors):
            continue
        ph = r.get("publishedHoursAgo")
        publish = datetime.now()
        if ph is not None:
            try:
                publish = datetime.now() - timedelta(hours=float(ph))
            except (TypeError, ValueError):
                pass
        out.append({
            "title": title, "body": body, "category": cat,
            "pinned": 1 if r.get("pinned") in (True, 1, "true", "1") else 0,
            "published_at": publish,
        })
    return out, errors


def events(rows: list) -> tuple[list[dict], list[str]]:
    out, errors = [], []
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            errors.append(_err(i, None, "row must be an object"))
            continue
        title = str(r.get("title") or "").strip()
        location = str(r.get("location") or "").strip()
        cat = str(r.get("category") or "tech")
        starts_iso = r.get("startsAt")
        in_days = r.get("inDays")
        if len(title) < 3:
            errors.append(_err(i, "title", "required, 3+ chars"))
        if len(location) < 2:
            errors.append(_err(i, "location", "required"))
        if cat not in EVENT_CATS:
            errors.append(_err(i, "category", f"one of {sorted(EVENT_CATS)}"))
        if not starts_iso and in_days is None:
            errors.append(_err(i, "startsAt", "provide ISO startsAt or inDays"))
        if errors and any(e.startswith(f"row {i + 1}") for e in errors):
            continue
        start = None
        if starts_iso:
            try:
                start = datetime.fromisoformat(str(starts_iso).replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                errors.append(_err(i, "startsAt", "invalid ISO datetime"))
                continue
        else:
            try:
                start = datetime.now() + timedelta(days=float(in_days))
            except (TypeError, ValueError):
                errors.append(_err(i, "inDays", "number expected"))
                continue
            t = str(r.get("time") or "09:00")
            if TIME_RE.match(t):
                h, m = t.split(":")
                start = start.replace(hour=min(23, int(h)), minute=min(59, int(m)), second=0, microsecond=0)
        out.append({
            "title": title, "description": str(r.get("description") or "").strip(),
            "location": location, "category": cat,
            "organizer": str(r.get("organizer") or "").strip(), "starts_at": start,
        })
    return out, errors


def faculty(rows: list) -> tuple[list[dict], list[str]]:
    out, errors = [], []
    for i, r in enumerate(rows):
        if not isinstance(r, dict):
            errors.append(_err(i, None, "row must be an object"))
            continue
        name = str(r.get("name") or "").strip()
        title = str(r.get("title") or "").strip()
        dept = str(r.get("department") or "").strip()
        email = str(r.get("email") or "").strip()
        office = str(r.get("office") or "").strip()
        hours = str(r.get("officeHours") or r.get("office_hours") or "").strip()
        if len(name) < 3:
            errors.append(_err(i, "name", "required, 3+ chars"))
        if len(title) < 2:
            errors.append(_err(i, "title", "required"))
        if len(dept) < 2:
            errors.append(_err(i, "department", "required"))
        if not EMAIL_RE.match(email):
            errors.append(_err(i, "email", "valid email required"))
        if len(office) < 2:
            errors.append(_err(i, "office", "required"))
        if len(hours) < 2:
            errors.append(_err(i, "officeHours", "required"))
        if errors and any(e.startswith(f"row {i + 1}") for e in errors):
            continue
        out.append({
            "name": name, "title": title, "department": dept, "email": email,
            "office": office, "office_hours": hours, "tags": str(r.get("tags") or "").strip(),
        })
    return out, errors


# ---------------------------------------------------------------------------
# Plain-text upload parsing
# ---------------------------------------------------------------------------

def _segments(text: str) -> list[str]:
    """Split teacher prose into record-sized paragraphs."""
    blocks = []
    for raw in re.split(r"\n\s*\n+", text.replace("\r\n", "\n")):
        block = " ".join(x.strip() for x in raw.splitlines() if x.strip())
        block = re.sub(r"\s+", " ", block).strip(" \t•-")
        if block:
            blocks.append(block)
    return blocks


def _first(pattern: str, text: str, flags=re.I) -> str:
    m = re.search(pattern, text, flags)
    if not m:
        return ""
    value = m.group(1) if m.lastindex else m.group(0)
    return value.strip(" .,:;-")


def _day_number(value: str) -> int | None:
    names = {"monday": 1, "mon": 1, "tuesday": 2, "tue": 2, "tues": 2,
             "wednesday": 3, "wed": 3, "thursday": 4, "thu": 4, "thur": 4,
             "friday": 5, "fri": 5, "saturday": 6, "sat": 6,
             "sunday": 7, "sun": 7}
    v = str(value or "").strip().lower()
    return names.get(v)


def _clock(value: str) -> str:
    value = str(value or "").strip().lower().replace(".", "")
    m = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$", value)
    if not m:
        return value
    h = int(m.group(1)); minute = int(m.group(2) or 0); ap = m.group(3)
    if ap == "pm" and h < 12: h += 12
    if ap == "am" and h == 12: h = 0
    return f"{min(h,23):02d}:{min(minute,59):02d}"


def _parse_rooms_text(text: str) -> list[dict]:
    out = []
    for b in _segments(text):
        code_m = re.search(r"\b([A-Z]{1,5}-\d{1,4}|[A-Z]{2,5}\d{1,4})\b", b, re.I)
        code = code_m.group(1).upper() if code_m else ""
        name = _first(r"(?:is|called|named)\s+(.+?)(?=\s+(?:in|at)\s+[^,.;]+\s+(?:block|building)|\s+(?:on|at)\s+floor|\s+floor\s*[:=]?|\s+capacity|\s+(?:room )?type\b|[.;]|$)", b)
        if not name and code_m:
            lead = b[:code_m.end()]
            rest = b[code_m.end():].lstrip(" :-")
            name = rest.split(",", 1)[0].strip()
        block = _first(r"(?:\b(?:in|at)\b|\b(?:block|building)\b)\s*[:=]?\s*([A-Za-z][A-Za-z .&'\-]*(?:Block|Building|Centre|Center))", b)
        if not block:
            block = _first(r"(?:block|building)\s*[:=]\s*([^,;]+)", b)
        floor = _first(r"floor\s*[:=]?\s*(\d+)", b)
        capacity = _first(r"(?:capacity|seats?)\s*[:=]?\s*(\d+)", b)
        rtype = _first(r"(?:room )?type\s*[:=]?\s*(lecture|lab|seminar|hall|facility)\b", b)
        if not rtype:
            rtype = next((x for x in ("lecture", "lab", "seminar", "hall", "facility") if re.search(rf"\b{x}\b", b, re.I)), "lecture")
        meta = _first(r"(?:meta|note|notes?)\s*[:=]\s*(.+)$", b)
        out.append({"code": code, "name": name or (f"Room {code}" if code else ""), "block": block, "floor": floor or 0,
                    "capacity": capacity or 0, "type": rtype, "meta": meta or None})
    return out


def _parse_courses_text(text: str) -> list[dict]:
    out = []
    for b in _segments(text):
        code_m = re.search(r"\b([A-Z]{2,6}-\d{2,4}|[A-Z]{2,8}\d{2,4})\b", b, re.I)
        code = code_m.group(1).upper() if code_m else ""
        title = _first(r"(?:course\s+)?(?:is|called|named)\s+(.+?)(?=\s+(?:taught\s+by|by|professor|department|dept)\b|,\s*(?:taught|by|professor|department)|[.;]|$)", b)
        if not title and code_m:
            rest = b[code_m.end():].lstrip(" :-")
            title = re.split(r"\s+(?:taught\s+by|by|professor)\s+", rest, maxsplit=1, flags=re.I)[0]
            title = title.split(",", 1)[0].strip()
        professor = _first(r"(?:taught\s+by|professor|instructor|by)\s*[:=-]?\s*(Dr\.?\s+[^,;.]+|Prof\.?\s+[^,;.]+|[^,;.]+)", b)
        department = _first(r"(?:department|dept)\s*[:=-]?\s*([^,;.]+)", b)
        credits = _first(r"(?:credits?|cr)\s*[:=-]?\s*(\d+)", b) or _first(r"\b(\d+)\s+(?:credits?|cr)\b", b) or 3
        aliases = _first(r"(?:aliases|also known as)\s*[:=-]?\s*([^.;]+)", b)
        color = _first(r"(?:color|colour)\s*[:=-]?\s*(#[0-9a-fA-F]{6})", b) or "#22d3ee"
        out.append({"code": code, "title": title, "aliases": aliases, "professor": professor, "department": department,
                    "credits": credits, "color": color})
    return out


def _parse_timetable_text(text: str) -> list[dict]:
    out = []
    for b in _segments(text):
        cm = re.search(r"\b([A-Z]{2,6}-\d{2,4}|[A-Z]{2,8}\d{2,4})\b", b, re.I)
        course = cm.group(1).upper() if cm else ""
        rm = re.search(r"\b([A-Z]{1,5}-\d{1,4}|[A-Z]{2,5}\d{1,4})\b", b[cm.end():] if cm else b, re.I)
        room = rm.group(1).upper() if rm else _first(r"(?:room|in)\s+([A-Z]{1,5}-\d{1,4})", b).upper()
        day_name = _first(r"\b(?:on|every)\s+(monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|friday|fri|saturday|sat|sunday|sun)\b", b)
        day = _day_number(day_name) or int(_first(r"(?:day|dayOfWeek)\s*[:=]?\s*([1-7])", b) or 0)
        tm = re.search(r"(?:from\s+)?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", b, re.I)
        start = _clock(tm.group(1)) if tm else _clock(_first(r"(?:start|starts)\s*(?:at|:)\s*([^,;.]+)", b))
        end = _clock(tm.group(2)) if tm else _clock(_first(r"(?:end|ends)\s*(?:at|:)\s*([^,;.]+)", b))
        out.append({"courseCode": course, "roomCode": room, "dayOfWeek": day, "startTime": start, "endTime": end})
    return out


def _parse_notices_text(text: str) -> list[dict]:
    out = []
    for b in _segments(text):
        title = _first(r"(?:title)\s*[:=-]\s*([^.;]+)", b)
        if not title:
            title = b.split(":", 1)[0].strip() if ":" in b else b[:100].strip()
        body = _first(r"(?:body|message|details?)\s*[:=-]\s*(.+)$", b)
        if not body and ":" in b:
            body = b.split(":", 1)[1].strip()
        if not body:
            body = b
        category = next((x for x in ("urgent", "exams", "placements", "events", "sports", "facility", "admin") if re.search(rf"\b{x}\b", b, re.I)), "admin")
        pinned = bool(re.search(r"\b(pin|pinned|important)\b", b, re.I))
        ph = _first(r"(?:published|posted)\s+(?:about\s+)?(\d+(?:\.\d+)?)\s*hours?\s+ago", b)
        out.append({"title": title, "body": body, "category": category, "pinned": pinned, "publishedHoursAgo": ph or None})
    return out


def _parse_events_text(text: str) -> list[dict]:
    out = []
    for b in _segments(text):
        title = _first(r"(?:event|title)\s*[:=-]\s*([^.;]+)", b)
        if not title:
            title = b.split(" at ", 1)[0].strip(" .") if " at " in b.lower() else b[:100].strip()
        location = _first(r"(?:location|venue)\s*[:=-]\s*([^.;]+)", b)
        if not location:
            location = _first(r"\bat\s+(.+?)(?=,\s*(?:category|organized|organised|in)\b|\s+(?:on|for|from|in)\s+|\.|$)", b)
        category = next((x for x in ("tech", "club", "cultural", "sports", "social") if re.search(rf"\b{x}\b", b, re.I)), "tech")
        organizer = _first(r"(?:organizer|organised\s+by|organized\s+by)\s*[:=-]?\s*([^,;.]+)", b)
        desc = _first(r"(?:description|details?)\s*[:=-]\s*(.+)$", b)
        in_days = _first(r"(?:in|after)\s+(\d+(?:\.\d+)?)\s+days?\b", b)
        tm = re.search(r"(?:at|time)\s*(?:[:=])?\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", b, re.I)
        iso = _first(r"(20\d\d-\d\d-\d\d(?:[T ]\d\d:\d\d(?::\d\d)?)?)", b)
        row = {"title": title, "description": desc, "location": location, "category": category, "organizer": organizer}
        if iso:
            row["startsAt"] = iso
        elif in_days:
            row["inDays"] = in_days
            row["time"] = _clock(tm.group(1)) if tm else "09:00"
        else:
            row["inDays"] = 1
            row["time"] = _clock(tm.group(1)) if tm else "09:00"
        out.append(row)
    return out


def _parse_faculty_text(text: str) -> list[dict]:
    out = []
    for b in _segments(text):
        email = _first(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", b)
        name = _first(r"(?:name)\s*[:=-]\s*([^,;.]+)", b)
        if not name:
            nm = re.match(r"((?:Dr\.?|Prof\.?)?\s*[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,4})", b)
            name = nm.group(1).strip() if nm else ""
        title = _first(r"(?:title|designation|position)\s*[:=-]\s*([^,;.]+)", b)
        if not title:
            title = next((x for x in ("Assistant Professor", "Associate Professor", "Professor", "Lecturer", "Dean", "Head of Department") if re.search(re.escape(x), b, re.I)), "")
        dept = _first(r"(?:department|dept)\s*(?:[:=-]\s*|\s+)([^,;.]+)", b)
        office = _first(r"(?:office|room)\s*[:=-]?\s*([^,;.]+)", b)
        hours = _first(r"(?:office hours|hours)\s*(?:[:=-]\s*|\s+)(.+?)(?=,\s*(?:tags|skills)\b|[.;]|$)", b)
        tags = _first(r"(?:tags|skills)\s*[:=-]\s*([^.;]+)", b)
        out.append({"name": name, "title": title, "department": dept, "email": email, "office": office,
                    "officeHours": hours, "tags": tags})
    return out


def parse_text(dataset: str, text: str):
    """Turn teacher-friendly prose into raw upload rows.

    The parser intentionally uses deterministic stdlib rules, so it works offline
    and keeps the existing row validators as the source of truth.
    """
    dataset = str(dataset or "").lower().strip()
    text = str(text or "").strip()
    if not text:
        return None, ["Input is empty."]
    # Advanced fallback: JSON pasted into the plain-text box still works.
    import json
    try:
        parsed = json.loads(text)
        if dataset == "campus" and isinstance(parsed, dict):
            return parsed, []
        if dataset != "campus" and isinstance(parsed, list):
            return parsed, []
    except Exception:
        pass

    if dataset == "rooms": return _parse_rooms_text(text), []
    if dataset == "courses": return _parse_courses_text(text), []
    if dataset == "timetable": return _parse_timetable_text(text), []
    if dataset == "notices": return _parse_notices_text(text), []
    if dataset == "events": return _parse_events_text(text), []
    if dataset == "faculty": return _parse_faculty_text(text), []
    if dataset == "campus":
        sections = {k: [] for k in VALIDATORS}
        current = None
        for raw in text.replace("\r\n", "\n").splitlines():
            line = raw.strip()
            if not line:
                continue
            heading = re.sub(r"^[#\[\] ]+", "", line).rstrip(":").strip().lower()
            alias = heading.replace("campus pack", "").strip()
            if alias in VALIDATORS:
                current = alias
                continue
            if current:
                sections[current].append(line)
        parsed = {}
        funcs = {"rooms": _parse_rooms_text, "courses": _parse_courses_text, "timetable": _parse_timetable_text,
                 "notices": _parse_notices_text, "events": _parse_events_text, "faculty": _parse_faculty_text}
        for key, lines in sections.items():
            if lines:
                parsed[key] = funcs[key]("\n\n".join(lines))
        if not parsed:
            return None, ["For a campus pack, add section headings such as Rooms, Courses, Timetable, Notices, Events and Faculty."]
        return parsed, []
    return None, [f"Unknown dataset {dataset!r}."]


VALIDATORS = {
    "rooms": rooms, "courses": courses, "timetable": timetable,
    "notices": notices, "events": events, "faculty": faculty,
}
