"""Segurança: IP real atrás da Cloudflare, rate-limit e 2FA (TOTP).

O TOTP é o mesmo padrão do Google Authenticator / Authy (RFC 6238),
implementado só com a biblioteca padrão do Python.
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time

from fastapi import Request

from . import db

# ---------------- IP real do visitante ----------------

def client_ip(request: Request) -> str:
    """IP real do visitante.

    Atrás do Cloudflare Tunnel, o IP de conexão é sempre o do túnel;
    o IP verdadeiro vem no header CF-Connecting-IP.
    """
    return (
        request.headers.get("cf-connecting-ip")
        or (request.client.host if request.client else "?")
    )


# ---------------- rate-limit do login do anfitrião ----------------

MAX_ADMIN_ATTEMPTS_PER_IP = 5
MAX_ADMIN_ATTEMPTS_GLOBAL = 30          # trava geral contra ataques distribuídos
ADMIN_ATTEMPT_WINDOW_MINUTES = 15


def register_failed_admin_login(ip: str):
    with db.get_connection() as connection:
        connection.execute(
            "INSERT INTO admin_login_attempts(ip) VALUES(?)", (ip,))


def admin_login_blocked(ip: str) -> bool:
    window = f"-{ADMIN_ATTEMPT_WINDOW_MINUTES} minutes"
    with db.get_connection() as connection:
        by_ip = connection.execute(
            "SELECT COUNT(*) AS total FROM admin_login_attempts "
            "WHERE ip=? AND ts > datetime('now', ?)", (ip, window),
        ).fetchone()["total"]
        overall = connection.execute(
            "SELECT COUNT(*) AS total FROM admin_login_attempts "
            "WHERE ts > datetime('now', ?)", (window,),
        ).fetchone()["total"]
    return by_ip >= MAX_ADMIN_ATTEMPTS_PER_IP or overall >= MAX_ADMIN_ATTEMPTS_GLOBAL


# ---------------- 2FA — TOTP (RFC 6238) ----------------

TOTP_STEP_SECONDS = 30
TOTP_DIGITS = 6


def new_totp_secret() -> str:
    """Segredo base32 para cadastrar no app autenticador."""
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def totp_uri(secret: str, account: str = "anfitriao",
             issuer: str = "Painel do Apartamento") -> str:
    """URI otpauth:// que vira o QR Code lido pelo app autenticador."""
    from urllib.parse import quote
    return (
        f"otpauth://totp/{quote(issuer)}:{quote(account)}"
        f"?secret={secret}&issuer={quote(issuer)}&digits={TOTP_DIGITS}"
        f"&period={TOTP_STEP_SECONDS}"
    )


def totp_code(secret: str, at_time: float | None = None) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    counter = int((at_time if at_time is not None else time.time())
                  // TOTP_STEP_SECONDS)
    message = struct.pack(">Q", counter)
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{number % (10 ** TOTP_DIGITS):0{TOTP_DIGITS}d}"


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    """Aceita o código atual e ±1 janela de 30s (relógios levemente fora)."""
    code = (code or "").strip().replace(" ", "")
    if not secret or not code:
        return False
    now = time.time()
    return any(
        hmac.compare_digest(totp_code(secret, now + i * TOTP_STEP_SECONDS), code)
        for i in range(-window, window + 1)
    )


def totp_qr_data_uri(uri: str) -> str:
    """QR do otpauth:// como data URI SVG (mesma técnica do QR do PIX)."""
    import io
    import segno
    buffer = io.BytesIO()
    segno.make(uri, error="m").save(buffer, kind="svg", scale=4, border=2,
                                    dark="#1a1a2e", xmldecl=False)
    return ("data:image/svg+xml;base64,"
            + base64.b64encode(buffer.getvalue()).decode())
