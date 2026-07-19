"""Senhas (PBKDF2) e sessões via cookie assinado (HMAC-SHA256)."""
import base64
import hashlib
import hmac
import json
import secrets
import time

PBKDF2_ITERATIONS = 200_000
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 45  # 45 dias


def hash_password(password: str) -> str:
    """Retorna 'salt$hash' em base64."""
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt, PBKDF2_ITERATIONS
    )
    return (
        base64.b64encode(salt).decode() + "$" + base64.b64encode(derived_key).decode()
    )


def check_password(password: str, stored_hash: str) -> bool:
    try:
        salt_b64, key_b64 = stored_hash.split("$")
        salt = base64.b64decode(salt_b64)
        derived_key = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(derived_key, base64.b64decode(key_b64))
    except Exception:
        return False


def sign_session(session_data: dict, secret: str) -> str:
    """Cria o valor do cookie: payload base64 + assinatura HMAC."""
    payload = dict(session_data, ts=int(time.time()))
    encoded_payload = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    signature = hmac.new(
        secret.encode(), encoded_payload.encode(), hashlib.sha256
    ).hexdigest()[:32]
    return f"{encoded_payload}.{signature}"


def verify_session(cookie_value: str, secret: str,
                   max_age: int = SESSION_MAX_AGE_SECONDS):
    """Valida assinatura e idade; retorna o dict da sessão ou None."""
    try:
        encoded_payload, signature = cookie_value.split(".")
        expected_signature = hmac.new(
            secret.encode(), encoded_payload.encode(), hashlib.sha256
        ).hexdigest()[:32]
        if not hmac.compare_digest(signature, expected_signature):
            return None
        padding = "=" * (-len(encoded_payload) % 4)
        session_data = json.loads(base64.urlsafe_b64decode(encoded_payload + padding))
        if int(time.time()) - session_data.get("ts", 0) > max_age:
            return None
        return session_data
    except Exception:
        return None
