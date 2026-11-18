"""Session management for the AURA Python edition (stdlib + FastAPI Request)."""
from __future__ import annotations

import secrets
import sqlite3
from datetime import datetime, timedelta

from fastapi import Request

SESSION_COOKIE = "aura_session"
SESSION_TTL_DAYS = 7


def create_session(conn: sqlite3.Connection, user_id: int) -> tuple[str, datetime]:
    token = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(days=SESSION_TTL_DAYS)
    conn.execute(
        "INSERT INTO sessions (token,user_id,expires_at) VALUES (?,?,?)",
        (token, user_id, expires_at.isoformat(timespec="seconds")),
    )
    conn.commit()
    return token, expires_at


def destroy_session(conn: sqlite3.Connection, token: str) -> None:
    conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()


def get_session_user(conn: sqlite3.Connection, request: Request) -> dict | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    row = conn.execute(
        "SELECT u.id, u.email, u.name, u.role, u.college_id, c.name AS college_name, "
        "c.code AS college_code, s.expires_at FROM sessions s "
        "JOIN users u ON u.id = s.user_id "
        "LEFT JOIN colleges c ON c.id = u.college_id "
        "WHERE s.token = ?",
        (token,),
    ).fetchone()
    if not row:
        return None
    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
    except Exception:
        return None
    if expires_at < datetime.now():
        destroy_session(conn, token)
        return None
    raw_role = row["role"] if row["role"] in ("student", "teacher", "college_admin") else "student"
    return {
        "id": row["id"], "email": row["email"], "name": row["name"],
        "role": raw_role,
        "college_id": row["college_id"] or 1,
        "college_name": row["college_name"] or "Astra University",
        "college_code": row["college_code"] or "ASTRA",
    }
