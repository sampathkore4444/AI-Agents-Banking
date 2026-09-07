"""Shared primitives for vendor adapters: timeouts, retries, HTTP client."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

import httpx

from config import settings

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Raised when a vendor/provider call cannot complete."""
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


def retry_call(fn: Callable[[], Any], *, attempts: int | None = None, base_delay: float = 0.2) -> Any:
    """Call fn with exponential backoff. Retries network/5xx failures only."""
    attempts = attempts if attempts is not None else settings.vendor_max_retries
    last_error: Exception | None = None
    for i in range(attempts + 1):
        try:
            return fn()
        except (httpx.HTTPError, TimeoutError) as exc:
            last_error = exc
            if i < attempts:
                delay = base_delay * (2 ** i)
                logger.warning("Vendor call failed (%s); retrying in %.1fs", exc, delay)
                time.sleep(delay)
    raise ApiError(f"Vendor call failed after {attempts + 1} attempts: {last_error}")


def _client() -> httpx.Client:
    return httpx.Client(timeout=settings.vendor_timeout_seconds)


def post_json(url: str, token: str, payload: dict) -> dict:
    """POST JSON to a vendor endpoint with auth bearer + retries."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _do() -> httpx.Response:
        return _client().post(url, headers=headers, json=payload)

    resp = retry_call(_do)
    if resp.status_code >= 400:
        raise ApiError(f"{url} returned HTTP {resp.status_code}: {resp.text[:500]}", status=resp.status_code)
    body = resp.json()
    if body is None:
        return {}
    if not isinstance(body, dict):
        return {"raw": body}
    return body


def get_json(url: str, token: str, params: dict | None = None) -> dict:
    headers = {"Authorization": f"Bearer {token}"}

    def _do() -> httpx.Response:
        return _client().get(url, headers=headers, params=params)

    resp = retry_call(_do)
    if resp.status_code >= 400:
        raise ApiError(f"{url} returned HTTP {resp.status_code}: {resp.text[:500]}", status=resp.status_code)
    body = resp.json()
    return body if isinstance(body, dict) else {"raw": body}