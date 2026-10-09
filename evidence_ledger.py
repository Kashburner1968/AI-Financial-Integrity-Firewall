"""SQLite append-only application ledger, SHA-256 chained; not immutable against DB administrators."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64

def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)

class Ledger:
    def __init__(self, path="data/firewall.db"):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS alerts(
                seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL, payload TEXT NOT NULL,
                prev_hash TEXT NOT NULL, hash TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS bars(
                symbol TEXT NOT NULL, minute TEXT NOT NULL,
                close REAL NOT NULL, volume REAL, source TEXT NOT NULL,
                received_at TEXT NOT NULL, PRIMARY KEY(symbol, minute, source))""")
    def _db(self):
        return sqlite3.connect(self.path, timeout=30)
    def bar(self, symbol, minute, close, volume, source):
        with self._db() as db:
            db.execute("""INSERT OR IGNORE INTO bars VALUES (?, ?, ?, ?, ?, ?)""",
                (symbol, minute, float(close), None if volume is None else float(volume),
                 source, datetime.now(timezone.utc).isoformat()))
    def alert(self, event_id, payload):
        created = datetime.now(timezone.utc).isoformat()
        body = canonical(payload)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT hash FROM alerts WHERE event_id=?", (event_id,)).fetchone()
            if existing:
                return existing[0]
            last = db.execute("SELECT hash FROM alerts ORDER BY seq DESC LIMIT 1").fetchone()
            previous = last[0] if last else GENESIS
            digest = hashlib.sha256((previous + "|" + event_id + "|" + created + "|" + body).encode()).hexdigest()
            db.execute("""INSERT INTO alerts(event_id,created_at,payload,prev_hash,hash)
                          VALUES(?,?,?,?,?)""", (event_id, created, body, previous, digest))
        return digest
    def verify(self):
        previous = GENESIS
        with self._db() as db:
            for event_id, created, body, prev_hash, digest in db.execute(
                "SELECT event_id,created_at,payload,prev_hash,hash FROM alerts ORDER BY seq"):
                calculated = hashlib.sha256(
                    (previous + "|" + event_id + "|" + created + "|" + body).encode()).hexdigest()
                if prev_hash != previous or digest != calculated:
                    return False
                previous = digest
        return True
