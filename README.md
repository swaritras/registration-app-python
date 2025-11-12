# Registration Web App — Python demo (FastAPI)

This repository provides a runnable local demo of a registration web application:

- Lets an anonymous user register / create an account (via HTTP REST endpoint).
- Persists user data to Firestore (using the Firestore emulator for local development).
- Sends a confirmation email asynchronously via a lightweight background worker (SQLite-backed queue).


## Quickstart

1. Create a Python 3.10+ virtualenv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate    # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Start a local SMTP debug server (to capture outgoing emails):

```bash
# Option A: Python built-in debugging SMTP server (prints emails to console)
python -m smtpd -n -c DebuggingServer localhost:1025

# Option B: (recommended UI) run MailHog via Docker
# docker run -p 1025:1025 -p 8025:8025 mailhog/mailhog
# then open http://localhost:8025 to see messages
```

3. Start the Firestore emulator (requires firebase-tools):

```bash
npm i -g firebase-tools
firebase emulators:start --only firestore
```

4. Run the worker (in separate shell):

```bash
python worker/worker.py
```

5. Run FastAPI:

```bash
export FIRESTORE_EMULATOR_HOST=localhost:8080
export SMTP_HOST=localhost
export SMTP_PORT=1025
export SMTP_FROM=noreply@example.com

uvicorn app.main:app --reload --port 5000
```

6. Register a user (example using curl):

```bash
curl -X POST http://127.0.0.1:5000/register \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Jay","email":"jay@example.com","password":"s3cret"}'
```
