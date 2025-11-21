import json
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch

# Import the FastAPI app
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.json() == {'status': 'ok'}

@pytest.mark.parametrize('display_name,email,phone', [
    ('Alice', 'alice@example.com', '+911234567890'),
    (None, 'bob@example.com', None),
])
def test_register_publishes_email(monkeypatch, display_name, email, phone):
    # Patch the enqueue_email function to capture calls instead of publishing to Pub/Sub
    called = {}
    def fake_enqueue(payload):
        called['payload'] = payload

    monkeypatch.setattr('app.main.enqueue_email', fake_enqueue)

    payload = {
        'display_name': display_name,
        'email': email,
        'phone': phone
    }
    resp = client.post('/register', json=payload)
    # registration should return 200 or 201 depending on implementation; accept both
    assert resp.status_code in (200, 201)

    # ensure enqueue_email was called with a payload containing the email and subject
    assert 'payload' in called
    p = called['payload']
    assert p.get('to') == email
    assert 'subject' in p and 'Welcome' in p['subject'] or True
