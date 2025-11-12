import sqlite3
import json
import time
from email.message import EmailMessage
import smtplib
from app.config import Config

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS email_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at INTEGER NOT NULL
);
"""

def init_db(path: str = None):
    path = path or Config.JOB_DB
    conn = sqlite3.connect(path)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()

def enqueue_email(subject: str, recipient: str, body: str):
    payload = json.dumps({"subject": subject, "recipient": recipient, "body": body})
    conn = sqlite3.connect(Config.JOB_DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO email_jobs (payload, status, created_at) VALUES (?, 'pending', ?)", (payload, int(time.time())))
    conn.commit()
    conn.close()

def send_email_immediately(subject: str, recipient: str, body: str):
    msg = EmailMessage()
    msg["From"] = Config.SMTP_FROM
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(body)

    if Config.DEBUG_EMAIL_PRINT:
        print("--- sending email (debug print) ---")
        print("To:", recipient)
        print("Subject:", subject)
        print(body)
        print("---\n")
        return True

    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as s:
        s.send_message(msg)
    return True

def process_job(job_row):
    job_id, payload_json = job_row[0], job_row[1]
    data = json.loads(payload_json)
    try:
        send_email_immediately(data["subject"], data["recipient"], data["body"])
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False
