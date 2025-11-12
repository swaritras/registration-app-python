import os

class Config:
    FIRESTORE_EMULATOR_HOST = os.environ.get("FIRESTORE_EMULATOR_HOST", "localhost:8080")
    SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 1025))
    SMTP_FROM = os.environ.get("SMTP_FROM", "noreply@example.com")
    JOB_DB = os.environ.get("JOB_DB", "email_jobs.db")
    DEBUG_EMAIL_PRINT = os.environ.get("DEBUG_EMAIL_PRINT", "true").lower() in ("1","true","yes")
