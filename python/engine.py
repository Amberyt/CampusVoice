"""Rule-based campus intent engine with Hindi support — Python edition.

Faithful port of the localized TypeScript engine: shared intent pipeline,
localized response builders (EN/HI), localized cards and suggestion chips.
"""
from __future__ import annotations

import math
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from hindi import (
    COURSE_HI, HI_DAYS, detect_language, hi_day_label, hi_day_phrase,
    hi_voice_code, in_days_label_hi, normalize_hi, time_ago_hi, with_english_map,
)
from locales import pack_for

DAY_NAMES = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
IST = ZoneInfo("Asia/Kolkata")

def india_now() -> datetime:
    """Current India Standard Time as a naive datetime for legacy campus records."""
    return datetime.now(IST).replace(tzinfo=None)

DAY_WORDS = {
    "monday": 1, "mon": 1,
    "tuesday": 2, "tue": 2, "tues": 2,
    "wednesday": 3, "wed": 3,
    "thursday": 4, "thu": 4, "thur": 4, "thurs": 4,
    "friday": 5, "fri": 5,
    "saturday": 6, "sat": 6,
    "sunday": 7, "sun": 7,
}

STOP = {
    "the", "and", "for", "with", "what", "when", "where", "who", "how", "any", "are",
    "there", "about", "tell", "show", "give", "have", "does", "from", "this", "that",
    "your", "you",
}

NOTICE_CATEGORY_WORDS = [
    (re.compile(r"\b(exams?|midsems?|mid sems?|tests?|results?|hall tickets?|revaluation|backlogs?|quizzes)\b"), "exams"),
    (re.compile(r"\b(placements?|jobs?|drives?|internships?|compan(y|ies)|recruitment|offers?)\b"), "placements"),
    (re.compile(r"\b(sports?|football|cricket|badminton|basketball|tournaments?|matches|tryouts?|trials)\b"), "sports"),
    (re.compile(r"\b(events?|fests?|culturals?|workshops?|clubs?|celebrations?|concerts?)\b"), "events"),
    (re.compile(r"\b(holidays?|fees?|deadlines?|registrations?|id cards?|payments?|erp)\b"), "admin"),
    (re.compile(r"\b(wifi|wi-fi|library|maintenance|canteen|hostel|infrastructure|power|water|facility|facilities)\b"), "facility"),
    (re.compile(r"\b(urgent|important|alert|alerts|mandatory|immediately)\b"), "urgent"),
]

NOTICE_LABEL = {
    "exams": "exam", "placements": "placement", "sports": "sports", "events": "event",
    "admin": "administrative", "facility": "facility", "urgent": "urgent",
}
NOTICE_LABEL_HI = {
    "exams": "एग्जाम", "placements": "प्लेसमेंट", "sports": "स्पोर्ट्स", "events": "इवेंट",
    "admin": "एडमिन", "facility": "फैसिलिटी", "urgent": "अर्जेंट",
}

FACILITY_WORDS = [
    (re.compile(r"\b(library|libraries|books?)\b"), "LIB-1"),
    (re.compile(r"\b(canteen|food court|food|cafe|cafeteria|eat)\b"), "CAN-1"),
    (re.compile(r"\b(auditorium|audi|theatre|theater)\b"), "AUD-1"),
    (re.compile(r"\b(health centre|health center|clinic|medical|doctor|hospital|sick)\b"), "INF-1"),
    (re.compile(r"\b(career|crc|placement (cell|centre|center|office))\b"), "CRC-1"),
]

FACULTY_INTENT_WORDS = re.compile(
    r"\b(office|offices|hours|email|contact|meet|find|reach|cabin|room|where|teaches|professor|prof|faculty|head|hod|dean)\b"
)


# ------------------------------------------------------------- time helpers


def campus_now(dt: datetime | None = None) -> dict:
    dt = dt or india_now()
    return {"day": dt.isoweekday(), "minutes": dt.hour * 60 + dt.minute, "date": dt}


def to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def fmt_time(hhmm: str) -> str:
    h, m = int(hhmm[:2]), int(hhmm[3:5])
    suffix = "PM" if h >= 12 else "AM"
    hr = 12 if h % 12 == 0 else h % 12
    return f"{hr}:00 {suffix}" if m == 0 else f"{hr}:{m:02d} {suffix}"


def fmt_clock(dt: datetime) -> str:
    suffix = "PM" if dt.hour >= 12 else "AM"
    hr = 12 if dt.hour % 12 == 0 else dt.hour % 12
    return f"{hr}:00 {suffix}" if dt.minute == 0 else f"{hr}:{dt.minute:02d} {suffix}"


def add_days(day: int, n: int) -> int:
    return (day - 1 + n) % 7 + 1


def day_label_for(day: int, today: int) -> str:
    if day == today:
        return "today"
    if day == add_days(today, 1):
        return "tomorrow"
    return DAY_NAMES[day]


def time_ago(d: datetime, now: datetime | None = None) -> str:
    now = now or india_now()
    diff = max(0, (now - d).total_seconds())
    mins = int(diff // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} min ago"
    hrs = mins // 60
    if hrs < 24:
        return "1 hour ago" if hrs == 1 else f"{hrs} hours ago"
    days = hrs // 24
    if days < 7:
        return "yesterday" if days == 1 else f"{days} days ago"
    weeks = days // 7
    return "1 week ago" if weeks == 1 else f"{weeks} weeks ago"


def in_days_label(starts_at: datetime, now: datetime | None = None) -> str:
    now = now or india_now()
    diff = (starts_at.date() - now.date()).days
    if diff <= 0:
        return "today"
    if diff == 1:
        return "tomorrow"
    if diff < 7:
        return f"in {diff} days"
    weeks = diff // 7
    return "next week" if weeks == 1 else f"in {weeks} weeks"


def voice_code(code: str) -> str:
    return " ".join(c for c in code if c not in "- ")


# --------------------------------------------------------- extraction helpers


def normalize(raw: str) -> str:
    s = re.sub(r"[^a-z0-9\s-]", " ", raw.lower())
    s = s.replace("-", " ")
    return " " + re.sub(r"\s+", " ", s).strip() + " "


def has_word(q: str, *words: str) -> bool:
    return any(f" {w} " in q for w in words)


def extract_day(q: str, today: int) -> dict | None:
    for word, day in DAY_WORDS.items():
        if f" {word} " in q or f" {word}s " in q:
            return {"day": day, "rel": "named"}
    if " day after tomorrow " in q:
        return {"day": add_days(today, 2), "rel": "dayAfter"}
    if has_word(q, "tomorrow"):
        return {"day": add_days(today, 1), "rel": "tomorrow"}
    if has_word(q, "weekend"):
        return {"day": 6, "rel": "named"}
    if has_word(q, "today", "tonight"):
        return {"day": today, "rel": "today"}
    return None


def extract_code(q: str, rooms_by_code: dict, courses_by_code: dict) -> dict | None:
    s = q.lower()
    m = re.search(r"\b(lib|aud|can|inf|crc)\s*-?\s*1\b", s)
    if m:
        room = rooms_by_code.get(f"{m.group(1).upper()}-1")
        if room:
            return {"kind": "room", "room": room}
    m = re.search(r"\bl\s*-?\s*([1-9])\b", s) or re.search(r"\blab\s*(?:number\s*)?([1-9])\b", s)
    if m:
        room = rooms_by_code.get(f"L-{m.group(1)}")
        if room:
            return {"kind": "room", "room": room}
    for m in re.finditer(r"\b([a-z]{2})\s*-?\s*(\d{3})\b", s):
        course = courses_by_code.get(f"{m.group(1)}-{m.group(2)}".upper())
        if course:
            return {"kind": "course", "course": course}
    for m in re.finditer(r"\b([a-z])\s*-?\s*(\d{3})\b", s):
        room = rooms_by_code.get(f"{m.group(1)}-{m.group(2)}".upper())
        if room:
            return {"kind": "room", "room": room}
    return None


def match_courses(q: str, courses: list) -> list:
    scored = []
    for c in courses:
        score = 0
        alias_hit = False
        for a in [s.strip() for s in c["aliases"].split(",") if s.strip()]:
            if f" {a} " in q:
                alias_hit = True
                score += 4 + len(a.split())
        title_words = [w for w in re.split(r"[^a-z]+", c["title"].lower()) if len(w) >= 3 and w not in STOP]
        coverage = sum(1 for w in title_words if f" {w} " in q)
        if coverage > 0 and coverage >= math.ceil(len(title_words) * 0.5):
            score += coverage
        if not alias_hit and score < 4:
            score = 0
        if score > 0 or alias_hit:
            scored.append((score, c))
    scored.sort(key=lambda t: -t[0])
    return [c for _, c in scored[:3]]


def match_faculty(q: str, faculty: list) -> list:
    scored = []
    for f in faculty:
        score = 0
        name = re.sub(r"^Dr\.?\s*(R\.\s*)?", "", f["name"], flags=re.IGNORECASE)
        for w in re.split(r"[^a-z]+", name.lower()):
            if len(w) >= 3 and f" {w} " in q:
                score += 6
        for t in f["tags"].lower().split():
            if len(t) >= 3 and f" {t} " in q:
                score += 2
        if score > 0:
            scored.append((score, f))
    hits = sorted((s for s in scored if s[0] >= 6), key=lambda t: -t[0])
    if hits:
        return [f for _, f in hits[:2]]
    if has_word(q, "hod", "head", "dean"):
        tag_hits = sorted((s for s in scored if s[0] >= 2), key=lambda t: -t[0])
        return [f for _, f in tag_hits[:2]]
    return []


# ------------------------------------------------------------------- engine


def answer_question(raw_query: str, data: dict, lang_pref: str = "auto") -> dict:
    if lang_pref == "hi":
        hindi = True
    elif lang_pref == "en":
        hindi = False
    else:
        hindi = detect_language(raw_query) == "hi"
    lang = "hi" if hindi else "en"
    L = pack_for(lang)
    now = campus_now()

    q = with_english_map(normalize_hi(raw_query)) if hindi else normalize(raw_query)
    trimmed = q.strip()

    # ---- localized composables ----
    def day_lbl(day: int) -> str:
        return hi_day_label(day, now["day"]) if hindi else day_label_for(day, now["day"])

    def day_phrase(day: int) -> str:
        if hindi:
            return hi_day_phrase(day, now["day"])
        if day == now["day"]:
            return "today"
        if day == add_days(now["day"], 1):
            return "tomorrow"
        return f"on {DAY_NAMES[day]}"

    def ago(d: datetime) -> str:
        return time_ago_hi(d) if hindi else time_ago(d)

    def in_days(d: datetime) -> str:
        return in_days_label_hi(d) if hindi else in_days_label(d)

    def day_name(d: int) -> str:
        return HI_DAYS[d] if hindi else DAY_NAMES[d]

    def v_code(code: str) -> str:
        return hi_voice_code(code) if hindi else voice_code(code)

    def floor_word(f: int) -> str:
        if f == 0:
            return "ग्राउंड फ़्लोर" if hindi else "the ground floor"
        return f"फ़्लोर {f}" if hindi else f"floor {f}"

    def cat_label(cat: str | None) -> str | None:
        if not cat:
            return None
        return (NOTICE_LABEL_HI.get(cat, cat) if hindi else NOTICE_LABEL.get(cat, cat))

    rooms_by_code = {r["code"].upper(): r for r in data["rooms"]}
    courses_by_code = {c["code"].upper(): c for c in data["courses"]}

    def day_entries(day: int) -> list:
        return sorted(
            [t for t in data["timetable"] if t["day_of_week"] == day],
            key=lambda t: to_minutes(t["start_time"]),
        )

    def is_live(e: dict) -> bool:
        return (
            e["day_of_week"] == now["day"]
            and to_minutes(e["start_time"]) <= now["minutes"] < to_minutes(e["end_time"])
        )

    def class_card(e: dict, day_hit: int | None = None) -> dict:
        course = courses_by_code.get(e["course_code"].upper())
        room = rooms_by_code.get(e["room_code"].upper())
        return {
            "kind": "class",
            "code": e["course_code"],
            "title": course["title"] if course else e["course_code"],
            "professor": course["professor"] if course else "",
            "color": course["color"] if course else "#22d3ee",
            "dayLabel": day_lbl(day_hit if day_hit is not None else e["day_of_week"]),
            "startLabel": fmt_time(e["start_time"]),
            "endLabel": fmt_time(e["end_time"]),
            "roomCode": e["room_code"],
            "roomName": room["name"] if room else "",
            "block": room["block"] if room else "",
            "isLab": (room["type"] if room else "") == "lab",
            "live": is_live(e),
        }

    def room_status(code: str) -> dict | None:
        entries = [e for e in day_entries(now["day"]) if e["room_code"].upper() == code.upper()]
        if now["day"] == 7 or not entries:
            label = ("आज कोई क्लास नहीं" if now["day"] == 7 else "पूरे दिन खाली") if hindi else ("No classes today" if now["day"] == 7 else "Free all day")
            return {"label": label, "tone": "free"}
        for e in entries:
            if is_live(e):
                c = courses_by_code.get(e["course_code"].upper())
                if hindi:
                    label = f"{fmt_time(e['end_time'])} तक व्यस्त" + (f" · {c['code']}" if c else "")
                else:
                    label = f"Occupied until {fmt_time(e['end_time'])}" + (f" · {c['code']}" if c else "")
                return {"label": label, "tone": "busy"}
        nxt = next((e for e in entries if to_minutes(e["start_time"]) > now["minutes"]), None)
        if nxt:
            label = f"अभी खाली · अगली क्लास {fmt_time(nxt['start_time'])}" if hindi else f"Free now · next class {fmt_time(nxt['start_time'])}"
            return {"label": label, "tone": "free"}
        label = "दिन के बाक़ी समय खाली" if hindi else "Free for the rest of the day"
        return {"label": label, "tone": "free"}

    def room_card(room: dict, with_status: bool = True) -> dict:
        status = room_status(room["code"]) if with_status and room["type"] != "facility" else None
        fac_label = "सुविधा" if hindi else "Facility"
        return {
            "kind": "room",
            "code": room["code"], "name": room["name"], "block": room["block"],
            "floor": room["floor"], "capacity": room["capacity"], "type": room["type"],
            "meta": room["meta"],
            "status": status["label"] if status else (fac_label if room["type"] == "facility" else None),
            "statusTone": "info" if room["type"] == "facility" else (status["tone"] if status else "info"),
        }

    def notice_card(n: dict) -> dict:
        return {
            "kind": "notice", "title": n["title"], "body": n["body"],
            "category": n["category"], "pinned": n["pinned"], "ago": ago(n["published_at"]),
        }

    def event_card(e: dict) -> dict:
        st = e["starts_at"]
        js_day = st.isoweekday()
        return {
            "kind": "event", "title": e["title"], "description": e["description"],
            "location": e["location"], "organizer": e["organizer"], "category": e["category"],
            "dayNum": str(st.day), "month": MONTHS_SHORT[st.month - 1],
            "timeLabel": f"{day_name(js_day)} · {fmt_clock(st)}",
            "inLabel": in_days(st),
        }

    def faculty_card(f: dict) -> dict:
        return {
            "kind": "faculty", "name": f["name"], "title": f["title"],
            "department": f["department"], "email": f["email"],
            "office": f["office"], "officeHours": f["office_hours"],
        }

    def respond(intent: str, say: dict, cards: list | None = None, suggestions: list | None = None) -> dict:
        return {
            "ok": True, "intent": intent, "lang": lang,
            "text": say["text"], "speak": say["speak"],
            "cards": cards or [], "suggestions": suggestions or [],
        }

    # Explicit date/time questions use the same IST clock as timetable logic.
    raw_low = (raw_query or "").strip().lower()
    asks_time = bool(re.search(
        r"\b(current time|time right now|time now|what time is it|what is the time|what s the time|tell me the time)\b", q
    )) or bool(re.search(r"(अभी\s*कितने\s*बजे|कितने\s*बजे\s*हैं|समय\s*क्या\s*है|अभी\s*का\s*समय)", raw_low)) or bool(
        re.search(r"\b(abhi kitne baje|abhi time kya hai|samay kya hai|current time batao)\b", raw_low)
    )
    asks_date = bool(re.search(
        r"\b(what is the date|what s the date|what s today s date|current date|today s date|today date|what day is it|what day is today|which day is today|what is today s date)\b", q
    )) or bool(re.search(r"\b(today|current)\b.*\b(date|day)\b", q)) or bool(re.search(
        r"\bwhat\s+(is|s)\s+(the\s+)?(date|day)\b", q
    )) or bool(re.search(
        r"(आज की तारीख|आज कौन सा दिन|आज कौन-सा दिन|आज की डेट|आज तारीख क्या है|आज कौन सी तारीख)", raw_low
    )) or bool(re.search(
        r"\b(aaj ki date|aaj kya date hai|aaj kaun sa din|aaj kaunsa din|today ki date)\b", raw_low
    ))
    current = now["date"]
    if asks_time:
        clock = fmt_clock(current)
        text = f"अभी भारतीय समय के अनुसार {clock} बजे हैं।" if hindi else f"The current time in India is {clock} IST."
        return respond("datetime.time", {"text": text, "speak": text})
    if asks_date:
        date_en = current.strftime("%A, %d %B %Y")
        date_hi_days = ["", "सोमवार", "मंगलवार", "बुधवार", "गुरुवार", "शुक्रवार", "शनिवार", "रविवार"]
        date_hi_months = ["", "जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"]
        date_hi = f"{date_hi_days[current.isoweekday()]}, {current.day} {date_hi_months[current.month]} {current.year}"
        text = f"आज {date_hi} है।" if hindi else f"Today is {date_en}."
        return respond("datetime.date", {"text": text, "speak": text})

    # ---- extraction ----
    day_hit = extract_day(q, now["day"])
    code_hit = extract_code(q, rooms_by_code, courses_by_code)
    course_hits = match_courses(q, data["courses"])
    if hindi:
        hr = normalize_hi(raw_query)
        extra = [
            courses_by_code[code]
            for code, aliases in COURSE_HI.items()
            if code in courses_by_code
            and any(f" {a} " in hr for a in aliases)
            and not any(c["code"] == code for c in course_hits)
        ]
        if extra:
            course_hits = (extra + course_hits)[:3]
    if code_hit and code_hit["kind"] == "course" and code_hit.get("course"):
        if not any(c["code"] == code_hit["course"]["code"] for c in course_hits):
            course_hits.insert(0, code_hit["course"])
    faculty_hits = match_faculty(q, data["faculty"])

    # ------------------------------------------------------------- small talk
    if re.fullmatch(r"((hi+|hello+|hey+|yo|hiya|namaste|hola|good (morning|afternoon|evening|day))[.! ]*)+", trimmed) or trimmed == "sup":
        hour = now["date"].hour
        clock = fmt_clock(now["date"])
        if hindi:
            salutation = "सुप्रभात" if 5 <= hour < 12 else ("नमस्कार" if 12 <= hour < 17 else ("शुभ संध्या" if 17 <= hour < 21 else "नमस्कार"))
            text = f"{salutation}! अभी भारतीय समय के अनुसार {clock} बजे हैं। मैं आपकी क्लास, कमरों, नोटिस और कैंपस की जानकारी में मदद कर सकती हूँ।"
        else:
            salutation = "Good morning" if 5 <= hour < 12 else ("Good afternoon" if 12 <= hour < 17 else ("Good evening" if 17 <= hour < 21 else "Hello"))
            text = f"{salutation}! It's {clock} IST. I can help with your timetable, rooms, notices, faculty and campus events."
        return respond("greeting", {"text": text, "speak": text}, suggestions=L["sugg"]("default"))

    if has_word(q, "thanks", "thank", "thankyou", "thx") or " thank you " in q:
        return respond("thanks", L["thanks"](), suggestions=L["sugg"]("thanks"))

    if has_word(q, "bye", "goodbye", "goodnight", "night"):
        return respond("bye", L["bye"]())

    if has_word(q, "help", "commands", "options", "features", "madad") or " what can you do " in q:
        return respond("help", L["help"](), suggestions=L["sugg"]("default"))

    if "who are you" in q or " your name " in q:
        return respond("identity", L["identity"](), suggestions=L["sugg"]("default"))

    # --------------------------------------------------------------- notices
    if has_word(q, "notice", "notices", "announcement", "announcements", "circular", "circulars", "news", "updates", "update", "bulletin", "board"):
        category = next((cat for rex, cat in NOTICE_CATEGORY_WORDS if rex.search(q)), None)
        filtered = [n for n in data["notices"] if n["category"] == category] if category else list(data["notices"])
        filtered.sort(key=lambda n: (not n["pinned"], -n["published_at"].timestamp()))
        items = filtered[:4]
        lbl = cat_label(category)
        if not items:
            return respond("notices", L["noticesEmpty"](lbl), suggestions=L["sugg"]("default"))
        joiner = "। " if hindi else ". "
        items_txt = joiner.join(
            (f"\"{n['title']}\" — {ago(n['published_at'])}" if hindi else f"\"{n['title']}\" — posted {ago(n['published_at'])}")
            for n in items[:2]
        )
        return respond(
            "notices",
            L["noticesList"]({"catLabel": lbl, "count": len(items), "itemsTxt": items_txt, "firstTitle": items[0]["title"]}),
            [notice_card(n) for n in items],
            L["sugg"]("notices"),
        )

    # ---------------------------------------------------------------- events
    event_title_hits = []
    for e in data["events"]:
        words = [w for w in re.split(r"[^a-z]+", e["title"].lower()) if len(w) >= 3 and w not in STOP]
        hits = sum(1 for w in words if f" {w} " in q)
        if hits > 0 and words and hits >= math.ceil(len(words) * 0.4):
            event_title_hits.append(e)
    if hindi and not event_title_hits and has_word(q, "hackathon"):
        h = next((e for e in data["events"] if re.search(r"hackathon", e["title"], re.I)), None)
        if h:
            event_title_hits.append(h)

    event_keywords = (
        has_word(q, "event", "events", "happening", "fest", "hackathon", "workshop", "workshops", "concert", "competition", "competitions", "club", "clubs", "talk", "tryouts", "trials", "match", "matches")
        or " going on " in q or " coming up " in q
    )

    if event_title_hits or event_keywords:
        now_ts = now["date"].timestamp() - 3600
        pool = sorted((e for e in data["events"] if e["starts_at"].timestamp() >= now_ts), key=lambda e: e["starts_at"])

        if event_title_hits:
            e = event_title_hits[0]
            when = f"{in_days(e['starts_at'])}, {fmt_clock(e['starts_at'])}" if hindi else f"{in_days(e['starts_at'])} at {fmt_clock(e['starts_at'])}"
            return respond(
                "events.detail",
                L["eventsDetail"]({"title": e["title"], "when": when, "location": e["location"], "organizer": e["organizer"], "description": e["description"]}),
                [event_card(e)],
                L["sugg"]("eventsDetail"),
            )

        cat = None
        if re.search(r"\b(sports?|football|cricket|match|matches)\b", q):
            cat = "sports"
        elif has_word(q, "hackathon", "workshop", "workshops", "talk", "talks", "tech"):
            cat = "tech"
        elif has_word(q, "club", "clubs"):
            cat = "club"
        elif has_word(q, "cultural", "culturals", "concert", "fest", "fests"):
            cat = "cultural"
        if cat:
            pool = [e for e in pool if e["category"] == cat]
        if day_hit:
            pool = [e for e in pool if e["starts_at"].isoweekday() == day_hit["day"]]
        items = pool[:5]
        if not items:
            return respond("events", L["eventsEmpty"](), suggestions=L["sugg"]("default"))
        cat_lbl = (NOTICE_LABEL_HI.get(cat, cat) if hindi else cat) if cat else None
        when_phrase = f" {day_phrase(day_hit['day'])}" if day_hit else ""
        items_txt = "; ".join(f"{e['title']} ({in_days(e['starts_at'])}, {fmt_clock(e['starts_at'])})" for e in items[:3])
        speak_joiner = "। फिर, " if hindi else ". Then, "
        speak_items = speak_joiner.join(f"{e['title']}, {in_days(e['starts_at'])}" for e in items[:3])
        return respond(
            "events",
            L["eventsList"]({"catLabel": cat_lbl, "whenPhrase": when_phrase, "itemsTxt": items_txt, "speakItems": speak_items}),
            [event_card(e) for e in items],
            L["sugg"]("events"),
        )

    # ------------------------------------------------------------ free rooms
    if re.search(r"\b(free|available|vacant|empty)\b", q) and has_word(q, "room", "rooms", "classroom", "classrooms", "lab", "labs", "hall", "halls", "space"):
        want_labs = has_word(q, "lab", "labs")
        teaching = [r for r in data["rooms"] if (r["type"] == "lab" if want_labs else r["type"] != "facility")]
        free = [r for r in teaching if (room_status(r["code"]) or {}).get("tone") == "free"]
        busy_count = len(teaching) - len(free)
        shown = free[:8]
        picks_txt = ", ".join(
            (f"{r['code']} {r['block']} में" if hindi else f"{r['code']} in {r['block']}") for r in shown[:3]
        )
        picks_speak = (" और " if hindi else " and ").join(v_code(r["code"]) for r in shown[:2])
        return respond(
            "rooms.free",
            L["roomsFree"]({
                "sunday": now["day"] == 7, "allFree": busy_count == 0,
                "count": len(free), "busy": busy_count, "total": len(teaching),
                "wantLabs": want_labs, "picksTxt": picks_txt, "picksSpeak": picks_speak,
                "more": len(free) > 3,
            }),
            [room_card(r) for r in shown],
            L["sugg"]("freeRooms"),
        )

    # ------------------------------------------------------------- facility
    for rex, code in FACILITY_WORDS:
        if rex.search(q):
            room = rooms_by_code.get(code)
            if not room:
                break
            return respond(
                "facility",
                L["facility"]({"name": room["name"], "block": room["block"], "meta": room["meta"] or ""}),
                [room_card(room)],
                L["sugg"]("facility"),
            )

    # -------------------------------------------------------------- faculty
    teaches_match = " teaches " in q or " who takes " in q or " faculty for " in q or " professor for " in q
    if teaches_match and course_hits:
        course = course_hits[0]
        prof = next((f for f in data["faculty"] if f["name"] == course["professor"]), None)
        slots = sorted((t for t in data["timetable"] if t["course_code"] == course["code"]), key=lambda t: t["day_of_week"])
        if prof:
            return respond(
                "faculty.course",
                L["facultyCourse"]({
                    "prof": course["professor"], "profTitle": prof["title"], "dept": prof["department"],
                    "title": course["title"], "code": course["code"],
                    "office": prof["office"], "hours": prof["office_hours"], "email": prof["email"],
                }),
                [faculty_card(prof), *[class_card(s) for s in slots[:2]]],
                L["sugg"]("courseSchedule", course["title"] if hindi else course["code"]),
            )

    if faculty_hits and (FACULTY_INTENT_WORDS.search(q) or (not course_hits and not code_hit)):
        f = faculty_hits[0]
        return respond(
            "faculty",
            L["faculty"]({"name": f["name"], "title": f["title"], "dept": f["department"], "office": f["office"], "hours": f["office_hours"], "email": f["email"]}),
            [faculty_card(x) for x in faculty_hits],
            L["sugg"]("faculty"),
        )

    # ---------------------------------------------------------- room by code
    if code_hit and code_hit["kind"] == "room":
        room = code_hit["room"]
        status = room_status(room["code"])
        capacity = (f" इसमें {room['capacity']} सीटें हैं।" if hindi else f" It seats {room['capacity']}.") if room["capacity"] else ""
        if room["type"] != "facility" and status:
            status_txt = (f" अभी: {status['label']}।" if hindi else f" Right now: {status['label'].lower()}.")
        elif room["meta"]:
            status_txt = f" {room['meta']}"
        else:
            status_txt = ""
        return respond(
            "rooms.info",
            L["roomInfo"]({
                "code": room["code"], "voiceCode": v_code(room["code"]), "name": room["name"],
                "floor": floor_word(room["floor"]), "block": room["block"],
                "capacity": capacity, "statusTxt": status_txt, "extra": room["meta"] or "",
            }),
            [room_card(room)],
            L["sugg"]("roomInfo"),
        )

    # -------------------------------------------------- where is course held
    asks_where = has_word(q, "where", "held", "venue", "location") or (
        " room " in q and (course_hits or (code_hit and code_hit["kind"] == "course"))
    )
    if asks_where and (course_hits or (code_hit and code_hit["kind"] == "course")):
        course = course_hits[0]
        slots = sorted(
            (t for t in data["timetable"] if t["course_code"] == course["code"]),
            key=lambda t: (t["day_of_week"], to_minutes(t["start_time"])),
        )
        room_codes = list(dict.fromkeys(s["room_code"] for s in slots))
        room_rows = [rooms_by_code[c.upper()] for c in room_codes if c.upper() in rooms_by_code]
        first = room_rows[0] if room_rows else None
        if first:
            room_detail = (f" {first['name']} में {first['capacity']} सीटें हैं, {floor_word(first['floor'])}।" if hindi
                           else f" {first['name']} seats {first['capacity']} and is on {floor_word(first['floor'])}.")
        else:
            room_detail = ""
        joiner = " और " if hindi else " and "
        return respond(
            "courses.where",
            L["courseWhere"]({
                "title": course["title"], "code": course["code"],
                "placesTxt": joiner.join(f"{r['code']} ({r['block']})" for r in room_rows),
                "placesSpeak": joiner.join(v_code(r["code"]) for r in room_rows),
                "blockFirst": room_rows[0]["block"] if room_rows else "",
                "timesTxt": ", ".join(
                    (f"{day_lbl(s['day_of_week'])} {fmt_time(s['start_time'])} पर" if hindi
                     else f"{day_lbl(s['day_of_week'])} at {fmt_time(s['start_time'])}")
                    for s in slots
                ),
                "roomDetail": room_detail,
            }),
            [*[room_card(r) for r in room_rows], *[class_card(s) for s in slots]][:5],
            L["sugg"]("courseWhere", course["title"] if hindi else course["code"]),
        )

    # -------------------------------------------------------- class right now
    if re.search(r"\b(now|currently|right now|at the moment|this time)\b", q) and has_word(q, "class", "classes", "lecture", "lectures", "period", "periods", "lab", "labs", "going", "happening"):
        if now["day"] == 7:
            return respond("timetable.now", L["nowSunday"](), suggestions=L["sugg"]("default"))
        entries = day_entries(now["day"])
        active = next((e for e in entries if is_live(e)), None)
        nxt = next((e for e in entries if to_minutes(e["start_time"]) > now["minutes"]), None)
        if active:
            c = courses_by_code.get(active["course_code"].upper())
            nc = courses_by_code.get(nxt["course_code"].upper()) if nxt else None
            return respond(
                "timetable.now",
                L["nowActive"]({
                    "title": c["title"] if c else active["course_code"],
                    "professor": c["professor"] if c else ("फैकल्टी" if hindi else "faculty"),
                    "room": active["room_code"], "voiceRoom": v_code(active["room_code"]),
                    "endTime": fmt_time(active["end_time"]),
                    "nextTitle": (nc["title"] if nc else nxt["course_code"]) if nxt else None,
                    "nextTime": fmt_time(nxt["start_time"]) if nxt else None,
                    "nextRoom": nxt["room_code"] if nxt else None,
                }),
                [class_card(active), *([class_card(nxt)] if nxt else [])],
                L["sugg"]("nowActive"),
            )
        if nxt:
            nc = courses_by_code.get(nxt["course_code"].upper())
            return respond(
                "timetable.now",
                L["nowFree"]({"title": nc["title"] if nc else nxt["course_code"], "time": fmt_time(nxt["start_time"]), "room": nxt["room_code"], "voiceRoom": v_code(nxt["room_code"])}),
                [class_card(nxt)],
                L["sugg"]("nowFree"),
            )
        return respond("timetable.now", L["nowDone"](), suggestions=L["sugg"]("nowDone"))

    # ------------------------------------------------------------- next class
    if has_word(q, "next", "upcoming") and has_word(q, "class", "classes", "lecture", "lectures", "period", "periods", "lab", "labs"):
        for i in range(7):
            day = add_days(now["day"], i)
            entries = day_entries(day)
            nxt = (
                next((e for e in entries if to_minutes(e["end_time"]) > now["minutes"]), None)
                if i == 0 else (entries[0] if entries else None)
            )
            if nxt:
                c = courses_by_code.get(nxt["course_code"].upper())
                return respond(
                    "timetable.next",
                    L["nextClass"]({
                        "title": c["title"] if c else nxt["course_code"],
                        "when": day_lbl(day), "time": fmt_time(nxt["start_time"]),
                        "room": nxt["room_code"], "voiceRoom": v_code(nxt["room_code"]),
                        "professor": c["professor"] if c else None,
                    }),
                    [class_card(nxt, day)],
                    L["sugg"]("day") if hindi else L["sugg"]("next", DAY_NAMES[day]),
                )
        return respond("timetable.next", L["nextNone"]())

    # ------------------------------------------------------------ course when
    if course_hits and (has_word(q, "when", "timing", "timings", "schedule", "time", "slot", "slots") or (code_hit and code_hit["kind"] == "course") or not day_hit):
        course = course_hits[0]
        slots = sorted(
            (t for t in data["timetable"] if t["course_code"] == course["code"]),
            key=lambda t: (t["day_of_week"], to_minutes(t["start_time"])),
        )
        if day_hit:
            slots = [s for s in slots if s["day_of_week"] == day_hit["day"]]
        if not slots:
            weekly = len([t for t in data["timetable"] if t["course_code"] == course["code"]])
            return respond(
                "courses.schedule",
                L["courseScheduleNone"]({"title": course["title"], "dayName": day_name(day_hit["day"]), "weekly": weekly, "code": course["title"] if hindi else course["code"]}),
            )
        if day_hit:
            scope = f"{day_name(day_hit['day'])} को" if hindi else f"on {DAY_NAMES[day_hit['day']]}"
        else:
            scope = "इस हफ्ते" if hindi else "this week"
        if hindi:
            times_txt = "; ".join(f"{day_lbl(s['day_of_week'])} {fmt_time(s['start_time'])} पर {s['room_code']} में" for s in slots)
            speak_txt = "। ".join(f"{day_lbl(s['day_of_week'])} को {fmt_time(s['start_time'])} पर, {v_code(s['room_code'])} में" for s in slots)
        else:
            times_txt = "; ".join(f"{day_lbl(s['day_of_week'])} {fmt_time(s['start_time'])} in {s['room_code']}" for s in slots)
            speak_txt = ". ".join(f"{day_lbl(s['day_of_week'])} at {fmt_time(s['start_time'])} in {v_code(s['room_code'])}" for s in slots)
        return respond(
            "courses.schedule",
            L["courseSchedule"]({
                "title": course["title"], "code": course["code"], "professor": course["professor"],
                "count": len(slots), "scope": scope, "timesTxt": times_txt, "speakTxt": speak_txt,
            }),
            [class_card(s) for s in slots],
            L["sugg"]("courseSchedule", course["title"] if hindi else course["code"]),
        )

    # ------------------------------------------------------------- how many
    if " how many " in q and has_word(q, "class", "classes", "lecture", "lectures", "period", "periods", "lab", "labs"):
        day = day_hit["day"] if day_hit else now["day"]
        entries = day_entries(day)
        phrase = day_phrase(day)
        if not entries:
            return respond("timetable.count", L["countZero"]({"phrase": phrase, "sunday": day == 7}))
        return respond(
            "timetable.count",
            L["count"]({"count": len(entries), "phrase": phrase, "start": fmt_time(entries[0]["start_time"]), "end": fmt_time(entries[-1]["end_time"])}),
            [class_card(e, day) for e in entries],
            L["sugg"]("count", day_name(day)),
        )

    # ---------------------------------------------------------- day timetable
    class_word = has_word(q, "class", "classes", "timetable", "schedule", "lecture", "lectures", "period", "periods", "lab", "labs", "subject", "subjects") or has_word(q, "have", "attend")

    if day_hit and class_word:
        entries = day_entries(day_hit["day"])
        phrase = day_phrase(day_hit["day"])
        relative = day_hit["day"] in (now["day"], add_days(now["day"], 1))
        if not entries:
            after_title = after_day = after_time = None
            for i in range(1, 8):
                d = add_days(day_hit["day"], i)
                es = day_entries(d)
                if es:
                    c = courses_by_code.get(es[0]["course_code"].upper())
                    after_title = c["title"] if c else ""
                    after_day = day_name(d)
                    after_time = fmt_time(es[0]["start_time"])
                    break
            return respond(
                "timetable.day",
                L["dayEmpty"]({"phrase": phrase, "sunday": day_hit["day"] == 7, "afterTitle": after_title, "afterDay": after_day, "afterTime": after_time}),
                suggestions=L["sugg"]("day"),
            )
        items_txt = "; ".join(
            (f"{(courses_by_code.get(e['course_code'].upper()) or {}).get('title', e['course_code'])} {fmt_time(e['start_time'])} पर ({e['room_code']})" if hindi
             else f"{(courses_by_code.get(e['course_code'].upper()) or {}).get('title', e['course_code'])} at {fmt_time(e['start_time'])} ({e['room_code']})")
            for e in entries
        )
        speak_joiner = "। " if hindi else ". "
        speak_txt = speak_joiner.join(
            (f"{(courses_by_code.get(e['course_code'].upper()) or {}).get('title', '')} {fmt_time(e['start_time'])} पर" if hindi
             else f"{(courses_by_code.get(e['course_code'].upper()) or {}).get('title', '')} at {fmt_time(e['start_time'])}")
            for e in entries[:3]
        )
        return respond(
            "timetable.day",
            L["day"]({
                "phrase": phrase, "dayName": day_name(day_hit["day"]), "count": len(entries),
                "itemsTxt": items_txt, "speakTxt": speak_txt, "more": len(entries) - 3, "relative": relative,
            }),
            [class_card(e, day_hit["day"]) for e in entries],
            L["sugg"]("day") if hindi else L["sugg"]("day", day_name(day_hit["day"])),
        )

    if class_word and has_word(q, "week", "full", "whole", "complete"):
        summaries = [{"d": d, "n": len(day_entries(d))} for d in range(1, 8)]
        if all(s["n"] == 0 for s in summaries):
            return respond("timetable.week", L["weekEmpty"]())
        def _part(s):
            if hindi:
                return f"{HI_DAYS[s['d']]} — {s['n']} क्लासें"
            plural = "es" if s["n"] > 1 else ""
            return f"{DAY_NAMES[s['d']]} — {s['n']} class{plural}"
        parts = "; ".join(_part(s) for s in summaries if s["n"] > 0)
        upcoming = sorted(
            [t for t in data["timetable"] if t["day_of_week"] > now["day"] or (t["day_of_week"] == now["day"] and to_minutes(t["end_time"]) > now["minutes"])],
            key=lambda t: (t["day_of_week"], to_minutes(t["start_time"])),
        )[:4]
        return respond("timetable.week", L["week"]({"parts": parts}), [class_card(e) for e in upcoming], L["sugg"]("week"))

    if class_word:
        entries = day_entries(now["day"])
        if not entries:
            return respond("timetable.day", L["todayEmpty"]())
        items_txt = "; ".join(
            (f"{(courses_by_code.get(e['course_code'].upper()) or {}).get('title', e['course_code'])} {fmt_time(e['start_time'])} पर ({e['room_code']})" if hindi
             else f"{(courses_by_code.get(e['course_code'].upper()) or {}).get('title', e['course_code'])} at {fmt_time(e['start_time'])} ({e['room_code']})")
            for e in entries
        )
        speak_joiner = "। " if hindi else ". "
        speak_txt = speak_joiner.join(
            (f"{(courses_by_code.get(e['course_code'].upper()) or {}).get('title', '')} {fmt_time(e['start_time'])} पर" if hindi
             else f"{(courses_by_code.get(e['course_code'].upper()) or {}).get('title', '')} at {fmt_time(e['start_time'])}")
            for e in entries[:3]
        )
        return respond(
            "timetable.day",
            L["day"]({
                "phrase": "आज" if hindi else "today", "dayName": day_name(now["day"]),
                "count": len(entries), "itemsTxt": items_txt, "speakTxt": speak_txt,
                "more": len(entries) - 3, "relative": True,
            }),
            [class_card(e, now["day"]) for e in entries],
            L["sugg"]("day") if hindi else L["sugg"]("day", day_name(now["day"])),
        )

    # ------------------------------------------------------------ fallbacks
    if faculty_hits:
        f = faculty_hits[0]
        return respond(
            "faculty",
            L["faculty"]({"name": f["name"], "title": f["title"], "dept": f["department"], "office": f["office"], "hours": f["office_hours"], "email": f["email"]}),
            [faculty_card(x) for x in faculty_hits],
            L["sugg"]("faculty"),
        )

    if course_hits:
        course = course_hits[0]
        slots = sorted((t for t in data["timetable"] if t["course_code"] == course["code"]), key=lambda t: t["day_of_week"])
        scope = "हर हफ्ते" if hindi else "a week"
        times_txt = ", ".join(f"{day_name(s['day_of_week'])} {fmt_time(s['start_time'])}" for s in slots)
        if hindi:
            speak_txt = "। ".join(f"{day_name(s['day_of_week'])} को {fmt_time(s['start_time'])} पर" for s in slots)
        else:
            speak_txt = ". ".join(f"{day_name(s['day_of_week'])} at {fmt_time(s['start_time'])}" for s in slots)
        return respond(
            "courses.schedule",
            L["courseSchedule"]({
                "title": course["title"], "code": course["code"], "professor": course["professor"],
                "count": len(slots), "scope": scope, "timesTxt": times_txt, "speakTxt": speak_txt,
            }),
            [class_card(s) for s in slots],
            L["sugg"]("courseSchedule", course["title"] if hindi else course["code"]),
        )

    return respond("fallback", L["fallback"](), suggestions=L["sugg"]("default"))
