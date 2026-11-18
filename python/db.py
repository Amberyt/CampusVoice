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
