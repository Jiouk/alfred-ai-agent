import pytest
from fastapi import HTTPException

from app.core.auth import _parse_client_id, _verify_client_token


def test_parse_client_id_accepts_positive_int_string():
    assert _parse_client_id("42") == 42


def test_parse_client_id_rejects_missing_non_numeric_or_non_positive_values():
    assert _parse_client_id(None) is None
    assert _parse_client_id("abc") is None
    assert _parse_client_id("0") is None
    assert _parse_client_id("-5") is None


def test_verify_client_token_noop_when_not_configured(monkeypatch):
    monkeypatch.delenv("CLIENT_AUTH_TOKEN", raising=False)
    _verify_client_token(None)
    _verify_client_token("anything")


def test_verify_client_token_raises_on_missing_or_invalid_token(monkeypatch):
    monkeypatch.setenv("CLIENT_AUTH_TOKEN", "super-secret")

    with pytest.raises(HTTPException) as missing:
        _verify_client_token(None)
    assert missing.value.status_code == 401

    with pytest.raises(HTTPException) as wrong:
        _verify_client_token("wrong")
    assert wrong.value.status_code == 401


def test_verify_client_token_accepts_valid_token(monkeypatch):
    monkeypatch.setenv("CLIENT_AUTH_TOKEN", "super-secret")
    _verify_client_token("super-secret")
