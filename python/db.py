"""SQLite data layer for the AURA Python edition.

Stdlib only. The dataset mirrors the Next.js/Drizzle edition exactly,
including portal accounts (users + sessions) for the student/teacher login.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta

DB_PATH = os.environ.get("AURA_DB", os.path.join(os.path.dirname(__file__), "campus.db"))

SCRYPT_N = 16384

SCHEMA = """
CREATE TABLE IF NOT EXISTS colleges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  code TEXT UNIQUE NOT NULL,
  contact_email TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS rooms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  block TEXT NOT NULL,
  floor INTEGER NOT NULL DEFAULT 0,
  capacity INTEGER NOT NULL DEFAULT 0,
  type TEXT NOT NULL DEFAULT 'lecture',
  meta TEXT
);
CREATE TABLE IF NOT EXISTS courses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  aliases TEXT NOT NULL DEFAULT '',
  professor TEXT NOT NULL,
  department TEXT NOT NULL,
  credits INTEGER NOT NULL DEFAULT 3,
  semester INTEGER NOT NULL DEFAULT 5,
  section TEXT NOT NULL DEFAULT 'A',
  color TEXT NOT NULL DEFAULT '#22d3ee'
);
CREATE TABLE IF NOT EXISTS timetable (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  course_code TEXT NOT NULL,
  room_code TEXT NOT NULL,
  day_of_week INTEGER NOT NULL,
  start_time TEXT NOT NULL,
  end_time TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'admin',
  pinned INTEGER NOT NULL DEFAULT 0,
  audience TEXT NOT NULL DEFAULT 'all',
  published_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  location TEXT NOT NULL,
  starts_at TEXT NOT NULL,
  category TEXT NOT NULL DEFAULT 'tech',
  organizer TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS faculty (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  title TEXT NOT NULL,
  department TEXT NOT NULL,
  email TEXT NOT NULL,
  office TEXT NOT NULL,
  office_hours TEXT NOT NULL,
  tags TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'student',
  pass_hash TEXT NOT NULL,
  salt TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  college_id INTEGER REFERENCES colleges(id)
);
CREATE TABLE IF NOT EXISTS sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT UNIQUE NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT NOT NULL
);
"""

ROOMS = [
    ("A-204", "Lecture Theatre 204", "Aryabhatta Block", 2, 90, "lecture", None),
    ("A-305", "Smart Classroom 305", "Aryabhatta Block", 3, 72, "lecture", None),
    ("A-101", "Seminar Hall", "Aryabhatta Block", 1, 110, "hall", "Bookable for club screenings and department talks."),
    ("B-102", "Lecture Hall 102", "Bhaskara Block", 1, 120, "lecture", None),
    ("B-208", "Smart Classroom 208", "Bhaskara Block", 2, 60, "lecture", None),
    ("B-310", "Tutorial Room 310", "Bhaskara Block", 3, 36, "seminar", None),
    ("C-101", "Lecture Hall 101", "C. V. Raman Block", 1, 140, "lecture", None),
    ("C-201", "Seminar Room 201", "C. V. Raman Block", 2, 48, "seminar", None),
    ("L-1", "Turing Computing Lab", "Innovation Block", 1, 60, "lab", "Systems programming and OS lab machines, dual-boot Linux."),
    ("L-2", "Hopper Systems Lab", "Innovation Block", 1, 60, "lab", "Networking racks, VLAN playground and packet analysers."),
    ("L-3", "Lovelace Data Lab", "Innovation Block", 2, 48, "lab", "GPU workstations for data science and AI coursework."),
    ("L-4", "Edison Electronics Lab", "Innovation Block", 2, 40, "lab", "Oscilloscopes, solder stations and embedded kits."),
    ("LIB-1", "Central Library", "Knowledge Centre", 0, 400, "facility", "Open 8 AM to 10 PM on weekdays and 9 AM to 6 PM on weekends. Midnight opening during exam weeks. Carry your ID card."),
    ("AUD-1", "Vikram Sarabhai Auditorium", "Knowledge Centre", 0, 800, "facility", "Book through the Student Affairs office for club events and screenings."),
    ("CAN-1", "Orbit Canteen", "Student Centre", 0, 200, "facility", "Open 8 AM to 8 PM every day. Friday special: the masala dosa counter."),
    ("INF-1", "Campus Health Centre", "Student Centre", 1, 30, "facility", "Open 9 AM to 5 PM on weekdays. 24x7 emergency line: 04444."),
    ("CRC-1", "Career Resource Centre", "Aryabhatta Block", 4, 50, "facility", "Walk in for resume reviews, mock interviews and placement prep, 10 AM to 5 PM on weekdays."),
]

COURSES = [
    ("CS-301", "Data Structures and Algorithms", "data structures,dsa,algorithms,ds,data structures and algorithms", "Dr. Arjun Mehta", "Computer Science", 4, "#22d3ee"),
    ("CS-302", "Operating Systems", "os,operating systems,operating system", "Dr. Nandini Rao", "Computer Science", 4, "#a78bfa"),
    ("CS-303", "Database Management Systems", "dbms,database,databases,database systems,database management", "Prof. Vikram Iyer", "Computer Science", 4, "#34d399"),
    ("CS-304", "Computer Networks", "networks,cn,computer networks,networking", "Dr. Sara Ali", "Computer Science", 3, "#fbbf24"),
    ("CS-305", "Artificial Intelligence", "ai,artificial intelligence", "Dr. Kabir Anand", "Computer Science", 3, "#f472b6"),
    ("MA-301", "Discrete Mathematics", "maths,math,discrete,discrete maths,mathematics,discrete math", "Dr. Kavya Sharma", "Mathematics", 3, "#60a5fa"),
    ("HM-203", "Professional Ethics", "ethics,professional ethics,humanities", "Dr. Leela Nair", "Humanities", 2, "#fb7185"),
    ("CS-391", "DBMS Laboratory", "dbms lab,database lab,sql lab", "Prof. Vikram Iyer", "Computer Science", 2, "#34d399"),
    ("CS-392", "Networks Laboratory", "networks lab,cn lab,networking lab", "Dr. Sara Ali", "Computer Science", 2, "#fbbf24"),
    ("EC-301", "Signals and Systems", "signals,signals and systems,ece,sns", "Dr. Farhan Qureshi", "Electronics", 3, "#fb923c"),
]

TIMETABLE = [
    (1, "09:00", "09:55", "CS-301", "A-204"), (1, "10:00", "10:55", "CS-302", "B-208"),
    (1, "11:15", "12:10", "CS-303", "B-102"), (1, "13:05", "14:00", "MA-301", "C-101"),
    (1, "14:05", "15:00", "CS-305", "A-305"),
    (2, "09:00", "09:55", "MA-301", "C-101"), (2, "10:00", "10:55", "CS-301", "A-204"),
    (2, "11:15", "12:10", "CS-302", "B-208"), (2, "14:00", "15:50", "CS-392", "L-2"),
    (2, "16:00", "16:55", "HM-203", "C-201"),
    (3, "09:00", "09:55", "CS-303", "B-102"), (3, "10:00", "10:55", "CS-305", "A-305"),
    (3, "11:15", "12:10", "CS-304", "B-208"), (3, "13:05", "14:00", "CS-301", "A-204"),
    (3, "14:00", "15:50", "CS-391", "L-3"),
    (4, "09:00", "09:55", "CS-302", "B-208"), (4, "10:00", "10:55", "MA-301", "C-101"),
    (4, "11:15", "12:10", "CS-304", "B-208"), (4, "14:05", "15:00", "CS-305", "A-305"),
    (4, "15:05", "16:00", "EC-301", "A-101"),
    (5, "09:00", "09:55", "CS-301", "A-204"), (5, "10:00", "10:55", "CS-303", "B-102"),
    (5, "11:15", "12:10", "EC-301", "A-101"), (5, "14:05", "15:00", "CS-304", "B-208"),
    (5, "16:00", "16:55", "HM-203", "C-201"),
    (6, "09:30", "10:25", "CS-305", "L-3"), (6, "10:30", "11:25", "CS-392", "L-2"),
]

FACULTY = [
    ("Dr. Arjun Mehta", "Professor", "Computer Science", "arjun.mehta@astra.edu", "Room A-412, Faculty Block", "Monday and Wednesday, 3 to 4 PM", "data structures algorithms dsa cs-301"),
    ("Dr. Nandini Rao", "Associate Professor", "Computer Science", "nandini.rao@astra.edu", "Room A-414, Faculty Block", "Tuesday and Friday, 11 AM to 12 PM", "operating systems os cs-302"),
    ("Prof. Vikram Iyer", "Assistant Professor", "Computer Science", "vikram.iyer@astra.edu", "Room B-401, Faculty Block", "Monday and Thursday, 2 to 3:30 PM", "dbms database sql cs-303 cs-391"),
    ("Dr. Sara Ali", "Assistant Professor", "Computer Science", "sara.ali@astra.edu", "Room B-402, Faculty Block", "Wednesday, 3 to 5 PM", "networks networking cn cs-304 cs-392"),
    ("Dr. Kabir Anand", "Professor", "Computer Science", "kabir.anand@astra.edu", "Room C-305, R&D Wing", "Friday, 2 to 4 PM", "ai artificial intelligence machine learning cs-305"),
    ("Dr. Kavya Sharma", "Associate Professor", "Mathematics", "kavya.sharma@astra.edu", "Room M-210, Science Block", "Tuesday and Thursday, 12 to 1 PM", "discrete mathematics maths ma-301"),
    ("Dr. Leela Nair", "Professor", "Humanities", "leela.nair@astra.edu", "Room H-104, Humanities Block", "Friday, 5 to 6 PM", "ethics humanities hm-203"),
    ("Dr. Farhan Qureshi", "Associate Professor", "Electronics", "farhan.qureshi@astra.edu", "Room E-302, Innovation Block", "Monday and Friday, 4 to 5 PM", "signals systems ece ec-301"),
    ("Dr. Priya Menon", "Head of Department", "Computer Science", "hod.cse@astra.edu", "Room A-401, Faculty Block", "Tuesday and Thursday, 2 to 3:30 PM", "hod head of department cse computer science admin"),
    ("Dr. R. Chandran", "Dean, Academic Affairs", "Administration", "dean.academics@astra.edu", "Admin Block, 2nd Floor", "Weekdays, 11 AM to 1 PM", "dean academics exams revaluation administration"),
]


def _hours_ago(h: float) -> str:
    return (datetime.now() - timedelta(hours=h)).isoformat(timespec="seconds")


def _in_days(days: float, hour: int, minute: int = 0) -> str:
    d = datetime.now() + timedelta(days=days)
    return d.replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat(timespec="seconds")


def _notices():
    return [
        ("Mid-semester exam timetable released", "Theory mid-semester exams run from the 14th to the 18th. Hall tickets are live on the student portal. Seating plans go up outside each block a day before every exam.", "exams", 1, _hours_ago(5)),
        ("ID cards mandatory at all entry gates", "Security audit this month: carry your institute ID at all times. Gates will deny entry without it. Duplicates can be printed at the Admin Block helpdesk.", "urgent", 0, _hours_ago(8)),
        ("AI-ML workshop: transformers, hands-on", "Dr. Anand's research group runs a hands-on transformer workshop this Saturday at 11 AM in the Lovelace Data Lab, L-3. Laptops optional. Sixty seats, first come first served.", "events", 0, _hours_ago(12)),
        ("Orbit Fest volunteer registrations open", "Astra's student-run tech and cultural fest needs four hundred volunteers across logistics, design, hospitality and media. Sign up through the fest app before Sunday.", "events", 0, _hours_ago(15)),
        ("Nexora Systems pre-placement talk", "Final-year CSE and ECE students: Nexora Systems hosts a pre-placement talk on Thursday at 4 PM in the Vikram Sarabhai Auditorium. Registration closes Wednesday midnight on the placement portal.", "placements", 0, _hours_ago(26)),
        ("Bhaskara Block Wi-Fi maintenance", "Network upgrades in Bhaskara Block on Saturday from 10 to 11 AM. Expect brief outages. Labs in the Innovation Block stay online throughout.", "facility", 0, _hours_ago(30)),
        ("Inter-department football trials", "Trials for the institute football squad on Tuesday at 5 PM, main ground. Wear your department colours and bring your boots and fitness record.", "sports", 0, _hours_ago(45)),
        ("Founder's Day celebrations this Friday", "Astra turns forty. Cultural programme from noon followed by the alumni meet. Classes after 12 PM stand suspended. Clubs report to the main grounds by 10 AM.", "events", 1, _hours_ago(50)),
        ("Backlog exam re-registration closes Friday", "Students with backlogs must re-register before 5 PM Friday at the examination cell. Carry your previous grade card and a copy of your fee receipt.", "exams", 0, _hours_ago(60)),
        ("Semester fee deadline extended", "The last date for semester fee payment is extended to the 20th. A late fee applies after the deadline. Payments accepted only through the ERP portal.", "admin", 0, _hours_ago(70)),
        ("Library open till midnight during exams", "The Central Library extends closing time to 12 AM starting exam week. Reading hall B stays open overnight. Carry your ID card for late entry.", "facility", 0, _hours_ago(90)),
        ("Internship fair: 30 companies on campus", "The Career Resource Centre hosts the annual internship fair next week in the Knowledge Centre atrium. Register on the CRC portal to skip the entry queue.", "placements", 0, _hours_ago(100)),
    ]


def _events():
    return [
        ("Robotics Build Night", "Line-follower chassis assembly and sensor calibration with the robotics core team. Kits provided; bring your teammates.", "Edison Electronics Lab, L-4", _in_days(2, 17, 30), "club", "Astra Robotics"),
        ("Guest Lecture: LLMs in Production", "Alumni panel from Nexora on shipping large language models at scale — inference costs, evals and guardrails. Open to all years.", "Vikram Sarabhai Auditorium", _in_days(3, 15), "tech", "CSE Association"),
        ("Sunrise Photography Walk", "Golden-hour shoot across the botanical trail behind the hostels. DSLRs available on request from the Lens Club inventory.", "Meet at North Gate", _in_days(4, 6, 30), "club", "Lens Club"),
        ("CodeSprint 48 — Hackathon", "A 48-hour build marathon with problem statements from three partner startups and a prize pool of one and a half lakh rupees.", "Innovation Block, Labs L-1 to L-4", _in_days(5, 18), "tech", "DevAstra Club"),
        ("Inter-Department Football Final", "CSE versus ECE under lights. Drumline at half-time. Entry is free with your institute ID.", "Main Ground", _in_days(6, 16), "sports", "Sports Council"),
        ("Green Campuses Panel", "City planners and faculty on Astra's net-zero roadmap, followed by an open mic for student proposals.", "Seminar Room C-201", _in_days(8, 14), "social", "Eco Club"),
        ("Blood Donation Camp", "Walk in any time before 3 PM. Donors receive a certificate, a health check and refreshments.", "Campus Health Centre", _in_days(10, 9), "social", "NSS Astra"),
        ("Orbit Fest 2026", "Three days, forty events, two headline concerts and the largest student maker fair in the state. Passes go live next week.", "Main Grounds", _in_days(21, 9), "cultural", "Student Senate"),
    ]


_lock = threading.Lock()


def connect(path: str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection. A custom path is used for isolated college datasets."""
    target = path or DB_PATH
    parent = os.path.dirname(os.path.abspath(target))
    os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(target, check_same_thread=False, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def tenant_db_path(college_id: int) -> str:
    """Return the data-file path for a non-default college."""
    tenant_dir = os.environ.get("AURA_TENANT_DB_DIR", os.path.join(os.path.dirname(DB_PATH), "tenants"))
    os.makedirs(tenant_dir, exist_ok=True)
    return os.path.join(tenant_dir, f"college_{int(college_id)}.db")


def ensure_tenant_schema(conn: sqlite3.Connection) -> None:
    """Create the campus tables without seeding Astra demo records or users."""
    with _lock:
        conn.executescript(SCHEMA)
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "college_id" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN college_id INTEGER")
        conn.commit()


def default_college_id(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT id FROM colleges WHERE code = 'ASTRA'").fetchone()
    return int(row["id"]) if row else 1


def ensure_college_registry(conn: sqlite3.Connection) -> int:
    """Migrate older databases and ensure the built-in Astra demo tenant exists."""
    with _lock:
        conn.executescript(SCHEMA)
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()}
        if "college_id" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN college_id INTEGER")
        now = datetime.now().isoformat(timespec="seconds")
        conn.execute(
            "INSERT OR IGNORE INTO colleges (id,name,code,contact_email,created_at) VALUES (1,?,?,?,?)",
            ("Astra University", "ASTRA", "admin@astra.edu", now),
        )
        row = conn.execute("SELECT id FROM colleges WHERE code='ASTRA'").fetchone()
        college_id = int(row["id"])
        conn.execute("UPDATE users SET college_id = ? WHERE college_id IS NULL", (college_id,))
        conn.commit()
    return college_id


# ------------------------------------------------------------------ passwords

def hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    pass_hash = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=SCRYPT_N, r=8, p=1).hex()
    return pass_hash, salt


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    try:
        derived = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=SCRYPT_N, r=8, p=1)
        expected = bytes.fromhex(expected_hash)
        return hmac.compare_digest(derived, expected)
    except Exception:
        return False


# ---------------------------------------------------------------------- seed

def _seed_users_if_empty(conn: sqlite3.Connection, college_id: int = 1) -> None:
    row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    if row["n"] > 0:
        return
    s_h, s_s = hash_password("student123")
    t_h, t_s = hash_password("teacher123")
    conn.execute(
        "INSERT OR IGNORE INTO users (email,name,role,pass_hash,salt,college_id) VALUES (?,?,?,?,?,?)",
        ("student@astra.edu", "Riya Sharma", "student", s_h, s_s, college_id),
    )
    conn.execute(
        "INSERT OR IGNORE INTO users (email,name,role,pass_hash,salt,college_id) VALUES (?,?,?,?,?,?)",
        ("teacher@astra.edu", "Dr. Arjun Mehta", "teacher", t_h, t_s, college_id),
    )
    conn.commit()


def _seed_campus_if_empty(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS n FROM rooms").fetchone()
    if row["n"] > 0:
        return
    conn.executemany(
        "INSERT OR IGNORE INTO rooms (code,name,block,floor,capacity,type,meta) VALUES (?,?,?,?,?,?,?)", ROOMS
    )
    conn.executemany(
        "INSERT OR IGNORE INTO courses (code,title,aliases,professor,department,credits,semester,section,color) VALUES (?,?,?,?,?,?,5,'A',?)",
        COURSES,
    )
    conn.executemany(
        "INSERT INTO timetable (course_code,room_code,day_of_week,start_time,end_time) VALUES (?,?,?,?,?)",
        [(co, ro, d, s, e) for (d, s, e, co, ro) in TIMETABLE],
    )
    conn.executemany("INSERT INTO notices (title,body,category,pinned,published_at) VALUES (?,?,?,?,?)", _notices())
    conn.executemany("INSERT INTO events (title,description,location,starts_at,category,organizer) VALUES (?,?,?,?,?,?)", _events())
    conn.executemany("INSERT INTO faculty (name,title,department,email,office,office_hours,tags) VALUES (?,?,?,?,?,?,?)", FACULTY)
    conn.commit()


_active_seed_lock = threading.Lock()


def ensure_seeded(conn: sqlite3.Connection) -> None:
    """Ensure the default demo tenant and its sample dataset are ready."""
    with _active_seed_lock:
        college_id = ensure_college_registry(conn)
        disable_demo_accounts = os.environ.get("AURA_DISABLE_DEMO_ACCOUNTS", "false").strip().lower() in {"1", "true", "yes", "on"}
        if not disable_demo_accounts:
            _seed_users_if_empty(conn, college_id)
        conn.execute("UPDATE users SET college_id = ? WHERE college_id IS NULL", (college_id,))
        conn.commit()
        _seed_campus_if_empty(conn)


# --------------------------------------------------------------------- reads

def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_campus(conn: sqlite3.Connection, seed: bool = True) -> dict:
    """Load a campus dataset. Default Astra is seeded; new colleges start empty."""
    if seed:
        ensure_seeded(conn)
    else:
        ensure_tenant_schema(conn)
    with _lock:
        rooms = [dict(r) for r in conn.execute("SELECT * FROM rooms").fetchall()]
        courses = [dict(r) for r in conn.execute("SELECT * FROM courses").fetchall()]
        timetable = [dict(r) for r in conn.execute("SELECT * FROM timetable").fetchall()]
        notices = [dict(r) for r in conn.execute("SELECT * FROM notices").fetchall()]
        events = [dict(r) for r in conn.execute("SELECT * FROM events").fetchall()]
        faculty = [dict(r) for r in conn.execute("SELECT * FROM faculty").fetchall()]
    for n in notices:
        n["pinned"] = bool(n["pinned"])
        n["published_at"] = _parse_dt(n["published_at"])
    for e in events:
        e["starts_at"] = _parse_dt(e["starts_at"])
    return {
        "rooms": rooms, "courses": courses, "timetable": timetable,
        "notices": notices, "events": events, "faculty": faculty,
    }
