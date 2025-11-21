import os
import sqlite3
from app.emailer import init_db, enqueue_email, process_job
from app.config import Config

def test_enqueue_and_process(tmp_path, monkeypatch):
    dbfile = str(tmp_path / "test_jobs.db")
    monkeypatch.setenv("JOB_DB", dbfile)
    # Ensure Config reads updated env - Config is simple so we rely on default path parameter below
    init_db(dbfile)
    enqueue_email("sub","test@example.com","hello world")
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()
    cur.execute("SELECT id, payload FROM email_jobs WHERE status='pending'")
    row = cur.fetchone()
    assert row is not None
    success = process_job(row)
    assert success
