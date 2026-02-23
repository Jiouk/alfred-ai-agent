"""
Authentication helpers for client-scoped API endpoints.
"""

import os
import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session, select

from app.models import Client, ClientStatus, get_session


def _parse_client_id(raw_value: Optional[str]) -> Optional[int]:
    """Parse and validate client id header value."""
    if raw_value is None:
        return None

    try:
        parsed = int(str(raw_value).strip())
    except (TypeError, ValueError):
        return None

    return parsed if parsed > 0 else None


def _verify_client_token(x_client_token: Optional[str]) -> None:
    """Validate optional shared client auth token from env."""
    expected_token = os.getenv("CLIENT_AUTH_TOKEN", "").strip()
    if not expected_token:
        return

    if not x_client_token or not secrets.compare_digest(x_client_token, expected_token):
        raise HTTPException(status_code=401, detail="Invalid client authentication token")


async def get_current_client_id(
    x_client_id: Optional[str] = Header(default=None, alias="X-Client-Id"),
    x_client_token: Optional[str] = Header(default=None, alias="X-Client-Token"),
    db: Session = Depends(get_session),
) -> int:
    """
    Resolve authenticated client id from headers.

    Required header:
    - X-Client-Id: numeric client id

    Optional hardening:
    - If CLIENT_AUTH_TOKEN env var is configured, X-Client-Token must match it.
    """
    client_id = _parse_client_id(x_client_id)
    if not client_id:
        raise HTTPException(status_code=401, detail="Missing or invalid X-Client-Id header")

    _verify_client_token(x_client_token)

    client = db.exec(select(Client).where(Client.id == client_id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if client.status != ClientStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="Client is not active")

    return client_id
