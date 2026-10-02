"""SQLite store. One file on the data volume; WAL; the ledger and checkpoints are append-only by trigger."""
import os
import sqlite3

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL CHECK (length(username) BETWEEN 3 AND 40),
  role TEXT NOT NULL CHECK (role IN ('operator','metallurgist','mineralogist','manager','admin')),
  pw TEXT NOT NULL,
  created REAL NOT NULL,
  disabled INTEGER NOT NULL DEFAULT 0,
  failed INTEGER NOT NULL DEFAULT 0,
  locked_until REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS sessions(
  token_hash TEXT PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  role TEXT NOT NULL,
  actor TEXT NOT NULL,
  csrf TEXT NOT NULL,
  created REAL NOT NULL,
  last_seen REAL NOT NULL);
CREATE TABLE IF NOT EXISTS ledger(
  seq INTEGER PRIMARY KEY,
  ts REAL NOT NULL,
  type TEXT NOT NULL,
  ref INTEGER,
  actor_role TEXT NOT NULL,
  actor TEXT NOT NULL,
  body TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  hash TEXT NOT NULL UNIQUE);
CREATE TRIGGER IF NOT EXISTS ledger_no_update BEFORE UPDATE ON ledger BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS ledger_no_delete BEFORE DELETE ON ledger BEGIN SELECT RAISE(ABORT, 'ledger is append-only'); END;
CREATE TABLE IF NOT EXISTS checkpoints(
  id INTEGER PRIMARY KEY,
  seq INTEGER NOT NULL,
  hash TEXT NOT NULL,
  ts REAL NOT NULL,
  doc TEXT NOT NULL);
CREATE TRIGGER IF NOT EXISTS checkpoints_no_update BEFORE UPDATE ON checkpoints BEGIN SELECT RAISE(ABORT, 'checkpoints are append-only'); END;
CREATE TRIGGER IF NOT EXISTS checkpoints_no_delete BEFORE DELETE ON checkpoints BEGIN SELECT RAISE(ABORT, 'checkpoints are append-only'); END;
CREATE TABLE IF NOT EXISTS uploads(
  id TEXT PRIMARY KEY,
  owner TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('csv','image')),
  sha256 TEXT NOT NULL,
  size INTEGER NOT NULL,
  created REAL NOT NULL,
  expires REAL,
  meta TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS hits(key TEXT NOT NULL, ts REAL NOT NULL);
CREATE INDEX IF NOT EXISTS hits_key ON hits(key, ts);
"""


def connect(path):
    """A connection per request. isolation_level=None: explicit transactions only (BEGIN IMMEDIATE for writers)."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    con = sqlite3.connect(path, timeout=10, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA busy_timeout=10000")
    return con


def init(path):
    con = connect(path)
    con.executescript(SCHEMA)
    con.close()
