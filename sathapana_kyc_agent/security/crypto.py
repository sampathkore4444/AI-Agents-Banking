"""Security primitives for the Sathapana KYC agent.

Implements symmetric encryption at rest (Fernet), deterministic tokenization
(HMAC-SHA256) for indexable identifiers, and a lightweight key bootstrap that
persists generated secrets to the local `.env` (flagged for a proper vault in
production).

Usage (prefers live OS env vars; falls back to `agent_root/.env`):
    from security import crypto
    token = crypto.encrypt("Sok Channda")
    crypto.decrypt(token)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import re
import threading
import uuid

logger = logging.getLogger(__name__)

AGENT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(AGENT_ROOT, ".env")

_SECRETS = {}

_lock = threading.Lock()


# ── .env helpers ───────────────────────────────────────────────────
def _read_env() -> dict[str, str]:
    result: dict[str, str] = {}
    if not os.path.exists(ENV_FILE):
        return result
    with open(ENV_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _write_env(key: str, value: str) -> None:
    env = _read_env()
    env[key] = value
    with open(ENV_FILE, "w", encoding="utf-8") as fh:
        fh.write("# Sathapana KYC agent local secrets — DO NOT COMMIT.\n# Move to a vault in production.\n")
        for k, v in env.items():
            fh.write(f"{k}={v}\n")
    os.chmod(ENV_FILE, 0o600)


def _get_secret(name: str, generator) -> str:
    """Return secret from env/.env, generating and persisting if absent."""
    value = os.environ.get(name) or _read_env().get(name)
    if value:
        return value
    with _lock:
        value = os.environ.get(name) or _read_env().get(name)
        if not value:
            value = generator()
            try:
                _write_env(name, value)
                logger.info("Generated secret %s -> %s", name, ENV_FILE)
            except OSError as exc:
                logger.warning("Could not persist %s to %s: %s. Using ephemeral in-memory secret.", name, ENV_FILE, exc)
            os.environ[name] = value
    return value


# ── keys ───────────────────────────────────────────────────────────
def get_encryption_key() -> str:
    return _get_secret("KYC_ENCRYPTION_KEY", lambda: base64.urlsafe_b64encode(os.urandom(32)).decode())


def get_tokenization_key() -> str:
    return _get_secret("KYC_TOKENIZATION_KEY", lambda: base64.urlsafe_b64encode(os.urandom(32)).decode())


def get_chain_salt() -> str:
    return _get_secret("KYC_HASH_CHAIN_SALT", lambda: uuid.uuid4().hex)


def _fernet():
    from cryptography.fernet import Fernet  # lazy import keeps CLI fast

    try:
        return Fernet(get_encryption_key())
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Invalid KYC_ENCRYPTION_KEY (must be a valid Fernet key).") from exc


# ── encryption at rest ─────────────────────────────────────────────
def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns 'enc:v1:<fernet_token>'."""
    if plaintext is None:
        return ""
    return "enc:v1:" + _fernet().encrypt(plaintext.encode("utf-8")).decode()


def decrypt(token: str) -> str:
    """Decrypt a string produced by `encrypt`. Returns '' for empty input."""
    if not token:
        return ""
    if not token.startswith("enc:v1:"):
        raise ValueError("Not an encrypted blob (missing enc:v1: prefix)")
    return _fernet().decrypt(token[len("enc:v1:"):].encode("utf-8")).decode("utf-8")


def is_encrypted(value: str) -> bool:
    return isinstance(value, str) and value.startswith("enc:v1:")


# ── deterministic tokenization (indexable, non-reversible) ────────
def tokenize(value: str, length: int = 24) -> str:
    """HMAC-SHA256 pseudonym for an identifier (e.g. document number)."""
    digest = hmac.new(get_tokenization_key().encode("utf-8"), str(value).encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:length]


# ── tamper-evident audit chain ─────────────────────────────────────
def chain_hash(prev_hash: str, payload: str) -> str:
    """Hash linking an audit entry to its predecessor."""
    salt = get_chain_salt()
    material = f"{salt}|{prev_hash}|{payload}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


# ── PII masking for logs ───────────────────────────────────────────
_PII_KEYS = ("name", "full_name", "customer", "customer_name", "dob", "date_of_birth",
             "id_number", "phone", "mobile", "email", "address", "passport",
             "national_id", "vatin", "registered_address", "household_head")


def mask(value: str, keep: int = 4) -> str:
    """Mask a string keeping the first `keep` characters: 'Sok C****'."""
    if not value:
        return value
    if len(value) <= keep:
        return "*" * len(value)
    return value[:keep] + "*" * min(6, len(value) - keep)


def redact_pii(data) -> object:
    """Recursively mask values whose keys look like PII (for audit detail)."""
    if isinstance(data, dict):
        return {k: (mask(v) if isinstance(v, str) and k.lower() in _PII_KEYS else redact_pii(v)) for k, v in data.items()}
    if isinstance(data, list):
        return [redact_pii(v) for v in data]
    return data


def looks_like_sec_number(value: str) -> bool:
    normalized = re.sub(r"[\s-]", "", value)
    return len(normalized) >= 9 and normalized.isdigit()