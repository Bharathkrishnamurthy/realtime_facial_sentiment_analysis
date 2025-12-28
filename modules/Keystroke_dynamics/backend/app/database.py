# backend/app/database.py
import sqlite3
import time
import os
import shutil
import logging
from datetime import datetime

from .config import DB_NAME

logger = logging.getLogger("keystroke_db")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = logging.FileHandler("keystroke_db.log")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

# DB lives one level above app/
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "keystroke_new.db"   # new DB for today’s samples
SCHEMA_PATH = os.path.join(BASE_DIR, "..", "schema.sql")


def _now_utc_ts_str():
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def get_conn():
    """
    Low-level connection (no row_factory set).
    Use get_db() in application code (it sets row_factory).
    """
    # Ensure DB directory exists
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn


def get_db():
    """
    Preferred connection to use in app code.
    Sets row_factory so rows behave like dicts.
    """
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    return conn


def now_ts():
    """
    Simple integer timestamp helper (used by main.py and other modules).
    """
    return int(time.time())


def _backup_corrupt_db(reason="corrupt"):
    """
    Moves the existing DB to a timestamped backup path.
    Returns path to backup file (or None).
    """
    if not os.path.exists(DB_PATH):
        return None
    bak_name = DB_PATH + f".{reason}_backup_{_now_utc_ts_str()}"
    try:
        shutil.copy2(DB_PATH, bak_name)
        logger.warning("Backed up corrupt DB %s -> %s", DB_PATH, bak_name)
        return bak_name
    except Exception as e:
        logger.exception("Failed to backup corrupt DB: %s", e)
        return None


def _create_fresh_db_from_schema(conn):
    """
    Create DB schema using SCHEMA_PATH. Raises exception if it fails.
    """
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"schema.sql not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf8") as f:
        sql = f.read()
    cur = conn.cursor()
    cur.executescript(sql)
    conn.commit()


def init_db(force_recreate=False):
    """
    Initialize DB. If DB is corrupt, back it up and recreate a fresh DB from schema.sql.
    This function is idempotent.
    """
    try:
        # Ensure containing folder exists
        db_dir = os.path.dirname(DB_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # If DB missing -> create fresh
        if not os.path.exists(DB_PATH) or force_recreate:
            logger.info("Creating fresh DB at %s", DB_PATH)
            # ensure old file removed if exists and force_recreate is True
            if os.path.exists(DB_PATH) and force_recreate:
                try:
                    os.remove(DB_PATH)
                except Exception:
                    pass
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            try:
                _create_fresh_db_from_schema(conn)
                logger.info("Fresh DB created from schema at %s", DB_PATH)
            finally:
                conn.close()
            return

        # If DB exists, run integrity_check
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cur = conn.cursor()
        try:
            res = cur.execute("PRAGMA integrity_check").fetchall()
        except sqlite3.DatabaseError as e:
            # Corrupt DB - back up and recreate (remove corrupt file first)
            logger.exception("DatabaseError during integrity_check; backing up and recreating DB")
            _backup_corrupt_db("corrupt")
            try:
                conn.close()
            except Exception:
                pass
            try:
                # remove corrupt DB file so new connect creates a fresh file
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                    logger.info("Removed corrupt DB file: %s", DB_PATH)
            except Exception:
                logger.exception("Failed to remove corrupt DB file before recreate")

            conn2 = sqlite3.connect(DB_PATH, check_same_thread=False)
            try:
                _create_fresh_db_from_schema(conn2)
                logger.info("Created fresh DB at %s after corruption", DB_PATH)
            finally:
                conn2.close()
            return

        # If integrity_check returned rows: commonly [('ok',)] on healthy DB
        if res and len(res) == 1 and (res[0][0] == "ok" or res[0] == ("ok",)):
            logger.info("PRAGMA integrity_check -> ok")
            conn.close()
            return
        else:
            # Unexpected response: treat as corruption -> backup + recreate
            logger.warning("PRAGMA integrity_check unexpected result: %r", res)
            try:
                conn.close()
            except Exception:
                pass
            _backup_corrupt_db("integrity_mismatch")
            try:
                if os.path.exists(DB_PATH):
                    os.remove(DB_PATH)
                    logger.info("Removed DB file after integrity mismatch: %s", DB_PATH)
            except Exception:
                logger.exception("Failed to remove DB file after integrity mismatch")

            conn2 = sqlite3.connect(DB_PATH, check_same_thread=False)
            try:
                _create_fresh_db_from_schema(conn2)
                logger.info("Created fresh DB at %s after integrity mismatch", DB_PATH)
            finally:
                conn2.close()
            return
    except Exception as exc:
        # Write a helpful log file for debugging and re-raise so callers can see
        tb = str(exc)
        with open("init_db_error.log", "w", encoding="utf8") as f:
            f.write(tb + "\n")
        logger.exception("init_db() failed: %s", exc)
        raise
