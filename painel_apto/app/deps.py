"""Dependências de autenticação (FastAPI Depends) e regras de acesso."""
from datetime import date

from fastapi import HTTPException, Request

from . import auth, db


def _session_secret() -> str:
    return db.get_setting("secret")


def access_limit(reservation: dict) -> date:
    """Último dia com acesso liberado.

    Regra: o hóspede acessa até o dia do check-out (inclusive); no dia
    seguinte o acesso é bloqueado — a não ser que exista uma liberação
    extraordinária (extended_until) com data maior.
    """
    limit = date.fromisoformat(reservation["checkout"])
    if reservation["extended_until"]:
        limit = max(limit, date.fromisoformat(reservation["extended_until"]))
    return limit


def guest_has_access(reservation: dict, reference_date: date) -> bool:
    checkin = date.fromisoformat(reservation["checkin"])
    return checkin <= reference_date <= access_limit(reservation)


def current_guest(request: Request) -> dict:
    """Retorna a reserva do hóspede logado, ou redireciona para a home."""
    cookie_value = request.cookies.get("guest_session")
    session = auth.verify_session(cookie_value, _session_secret()) if cookie_value else None
    if not session or "rid" not in session:
        raise HTTPException(303, headers={"Location": "/"})

    with db.get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM reservations WHERE id=?", (session["rid"],)
        ).fetchone()

    from . import billing
    if not row or not guest_has_access(dict(row), billing.today()):
        raise HTTPException(303, headers={"Location": "/?expirado=1"})
    return dict(row)


def current_host(request: Request) -> bool:
    """Garante que há um anfitrião logado, ou redireciona para o login."""
    cookie_value = request.cookies.get("host_session")
    session = auth.verify_session(cookie_value, _session_secret()) if cookie_value else None
    if not session or session.get("role") != "host":
        raise HTTPException(303, headers={"Location": "/admin/login"})
    return True
