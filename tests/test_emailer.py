import pytest
from unittest.mock import patch, MagicMock
from app.emailer import send_email

class DummySMTP:
    def __init__(self, host, port):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
    def starttls(self):
        pass
    def login(self, user, pwd):
        pass
    def send_message(self, msg):
        # simulate send success
        return True

def test_send_email_success(monkeypatch):
    payload = {
        'to': 'test@example.com',
        'subject': 'Hello',
        'body': 'This is a test'
    }
    # patch smtplib.SMTP to avoid real network calls
    monkeypatch.setattr('smtplib.SMTP', lambda host, port: DummySMTP(host, port))
    # also ensure Config values exist; import lazily
    from app.config import Config
    # Run send_email and expect True
    result = send_email(payload)
    assert result is True

def test_send_email_failure(monkeypatch):
    payload = {
        'to': 'test@example.com',
        'subject': 'Hello',
        'body': 'This is a test'
    }
    # Patch SMTP to raise when sending
    class FailingSMTP(DummySMTP):
        def send_message(self, msg):
            raise Exception('SMTP down')
    monkeypatch.setattr('smtplib.SMTP', lambda host, port: FailingSMTP(host, port))
    result = send_email(payload)
    assert result is False
