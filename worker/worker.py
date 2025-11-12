"""
Simple worker that polls the sqlite email_jobs table and processes pending jobs.
Run it in a separate terminal: `python worker/worker.py`
"""
import sqlite3
import time
from app.emailer import init_db, process_job
from app.config import Config

POLL_INTERVAL = 2.0

def fetch_one_pending(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, payload FROM email_jobs WHERE status='pending' ORDER BY id LIMIT 1")
    row = cur.fetchone()
    return row

def mark_done(conn, job_id):
    cur = conn.cursor()
    cur.execute("UPDATE email_jobs SET status='done' WHERE id=?", (job_id,))
    conn.commit()

if __name__ == "__main__":
    init_db(Config.JOB_DB)
    print("Worker started. Polling DB for email jobs...")
    conn = sqlite3.connect(Config.JOB_DB, check_same_thread=False)

    try:
        while True:
            row = fetch_one_pending(conn)
            if row:
                job_id = row[0]
                payload = row[1]
                print("Processing job", job_id)
                success = process_job((job_id, payload))
                if success:
                    mark_done(conn, job_id)
                    print("Job", job_id, "done")
                else:
                    print("Job", job_id, "failed — will retry later")
            else:
                time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("Worker exiting")
    finally:
        conn.close()
