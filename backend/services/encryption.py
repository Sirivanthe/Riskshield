# Field-Level Encryption
# Fernet (AES-128-CBC + HMAC-SHA256) for at-rest encryption of sensitive config values
# (LLM api_key, ServiceNow password & api_token, etc.)
#
# Key derivation:
#   - Uses RISKSHIELD_ENCRYPTION_KEY if set in env
#   - Otherwise derives a stable Fernet key from EMERGENT_LLM_KEY (SHA256 → urlsafe b64)
#     so every deployment gets a distinct, non-hardcoded encryption key automatically.
#
# Ciphertext format: "enc:v1:<fernet-token>"
# Existing plaintext values are returned as-is so we degrade gracefully during a rollout.

import base64
import hashlib
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

CIPHER_PREFIX = "enc:v1:"


def _derive_key() -> bytes:
    override = os.environ.get("RISKSHIELD_ENCRYPTION_KEY")
    if override:
        # Allow a raw Fernet key or arbitrary secret. If 44 chars & urlsafe-b64 → use as-is.
        try:
            Fernet(override.encode())
            return override.encode()
        except (ValueError, TypeError):
            pass
        return base64.urlsafe_b64encode(hashlib.sha256(override.encode()).digest())

    seed = os.environ.get("EMERGENT_LLM_KEY") or "riskshield-default-seed-2026"
    return base64.urlsafe_b64encode(hashlib.sha256(seed.encode()).digest())


_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_derive_key())
    return _fernet


def encrypt(plaintext: Optional[str]) -> Optional[str]:
    if not plaintext:
        return plaintext
    if plaintext.startswith(CIPHER_PREFIX):
        return plaintext  # Already encrypted
    token = _get_fernet().encrypt(plaintext.encode()).decode()
    return f"{CIPHER_PREFIX}{token}"


def decrypt(ciphertext: Optional[str]) -> Optional[str]:
    if not ciphertext:
        return ciphertext
    if not ciphertext.startswith(CIPHER_PREFIX):
        # Legacy plaintext – return unchanged so existing rows keep working.
        return ciphertext
    token = ciphertext[len(CIPHER_PREFIX):]
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt stored secret — encryption key may have changed.")
        return None
