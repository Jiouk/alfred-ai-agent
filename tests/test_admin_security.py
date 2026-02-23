import pytest
from fastapi import HTTPException

from app.routers import admin


def test_verify_admin_key_requires_env_configuration(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    with pytest.raises(HTTPException) as exc:
        admin.verify_admin_key("anything")

    assert exc.value.status_code == 503


def test_verify_admin_key_rejects_missing_or_wrong_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "super-secret")

    with pytest.raises(HTTPException) as missing:
        admin.verify_admin_key(None)
    assert missing.value.status_code == 401

    with pytest.raises(HTTPException) as wrong:
        admin.verify_admin_key("wrong")
    assert wrong.value.status_code == 401


def test_verify_admin_key_accepts_valid_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "super-secret")

    assert admin.verify_admin_key("super-secret") is True
