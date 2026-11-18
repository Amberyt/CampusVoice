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
    """Create any missing Astra demo users without depending on an empty users table.

    Existing users (including college administrators) are left untouched. This
    makes startup seeding safe when the database already contains other accounts
    or when only one of the two demo accounts exists.
    """
    demo_users = (
        ("student@astra.edu", "Riya Sharma", "student", "student123"),
        ("teacher@astra.edu", "Dr. Arjun Mehta", "teacher", "teacher123"),
    )

    for email, name, role, password in demo_users:
        # Compare case-insensitively so an address with different capitalization
        # is not duplicated in SQLite's default case-sensitive UNIQUE column.
        existing = conn.execute(
            "SELECT id FROM users WHERE lower(email) = lower(?) LIMIT 1",
            (email,),
        ).fetchone()
        if existing:
            continue

        pass_hash, salt = hash_password(password)
        conn.execute(
            """INSERT OR IGNORE INTO users
               (email, name, role, pass_hash, salt, college_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (email, name, role, pass_hash, salt, college_id),
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
        disable_demo_accounts = os.environ.get("AURA_DISABLE_DEMO_ACCOUNTS", "false").strip().lower() in {
            "1", "true", "yes", "on"
        }
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
        "rooms": rooms,
        "courses": courses,
        "timetable": timetable,
        "notices": notices,
        "events": events,
        "faculty": faculty,
