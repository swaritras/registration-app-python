from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from app.firestore_client import create_user_doc
from app.emailer import enqueue_email
from app.config import Config

app = FastAPI(title="Registration Demo")



@app.get('/health', tags=['health'])
async def health():
    """Health endpoint for readiness/liveness checks."""
    return {'status': 'ok'}
class RegisterRequest(BaseModel):
    display_name: str | None = None
    email: EmailStr
    password: str | None = None

@app.get("/")
async def index():
    return {"status": "ok", "message": "Registration demo (FastAPI)"}

@app.post("/register", status_code=201)
async def register(req: RegisterRequest):
    user = {
        "display_name": req.display_name,
        "email": req.email,
        "created_at": firestore_server_timestamp(),
        "password_placeholder": bool(req.password)
    }
    try:
        doc_id = create_user_doc(user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    subject = "Welcome to Registration Demo"
    body = f"Hi {req.display_name or 'User'},\n\nThanks for registering. Your user id is {doc_id}."
    enqueue_email(subject, req.email, body)

    return {"message": "registered", "user_id": doc_id}

def firestore_server_timestamp():
    import time
    return int(time.time())
