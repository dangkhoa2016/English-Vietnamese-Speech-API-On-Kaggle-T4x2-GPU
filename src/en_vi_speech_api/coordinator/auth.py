from __future__ import annotations

import hmac
import os
import secrets
from pathlib import Path

from fastapi import Request

from en_vi_speech_api.errors import ApiError


def load_or_create_api_key(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            try:
                path.chmod(0o600)
            except OSError:
                pass
            return value
    value = secrets.token_urlsafe(32)
    path.write_text(f"{value}\n", encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return value


def authorization_required(request: Request, expected_key: str) -> None:
    header = request.headers.get("authorization", "")
    prefix = "Bearer "
    if not header.startswith(prefix):
        raise ApiError("unauthorized", "A valid bearer API key is required.", 401)
    candidate = header[len(prefix) :].strip()
    if not candidate or not hmac.compare_digest(candidate, expected_key):
        raise ApiError("unauthorized", "A valid bearer API key is required.", 401)


def auth_required_from_env(default: bool = False) -> bool:
    raw = os.getenv("API_AUTH_REQUIRED")
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError("API_AUTH_REQUIRED must be a boolean value")
