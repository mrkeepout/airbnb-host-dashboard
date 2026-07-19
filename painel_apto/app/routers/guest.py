"""Rotas do hóspede: link mágico, painel de cards, energia, automações e fatura."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import auth, billing, db, deps, i18n
from .. import ha as home_assistant
from ..modules import REGISTRY as MODULE_REGISTRY
from ..modules.automacoes import allowed_entities

router = APIRouter()

MAX_LOGIN_ATTEMPTS = 5
ATTEMPT_WINDOW_MINUTES = 15
LANG_COOKIE_MAX_AGE = 60 * 60 * 24 * 90   # 90 dias
SESSION_COOKIE_MAX_AGE = 60 * 60 * 24 * 45  # 45 dias


def get_templates(request: Request):
    return request.app.state.templates


def find_reservation_by_token(token: str) -> dict:
    with db.get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM reservations WHERE token=?", (token,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Reserva não encontrada")
    return dict(row)


def too_many_login_attempts(token: str) -> bool:
    with db.get_connection() as connection:
        attempts = connection.execute(
            "SELECT COUNT(*) AS total FROM login_attempts "
            "WHERE token=? AND ts > datetime('now', ?)",
            (token, f"-{ATTEMPT_WINDOW_MINUTES} minutes"),
        ).fetchone()["total"]
    return attempts >= MAX_LOGIN_ATTEMPTS


def render_login_page(request: Request, reservation: dict, token: str,
                      error_message: str | None, is_expired: bool):
    language = i18n.detect_language(request)
    response = get_templates(request).TemplateResponse(
        request, "guest/login.html",
        {"reservation": reservation, "token": token, "error": error_message,
         "expired": is_expired, "t": i18n.get_texts(language), "lang": language},
    )
    response.set_cookie("lang", language, max_age=LANG_COOKIE_MAX_AGE)
    return response


# ---------------- login pelo link mágico ----------------

@router.get("/r/{token}", response_class=HTMLResponse)
def magic_link_page(request: Request, token: str):
    reservation = find_reservation_by_token(token)
    is_expired = not deps.guest_has_access(reservation, billing.today())
    return render_login_page(request, reservation, token, None, is_expired)


@router.post("/r/{token}", response_class=HTMLResponse)
def magic_link_authenticate(request: Request, token: str, last4: str = Form(...)):
    reservation = find_reservation_by_token(token)
    texts = i18n.get_texts(i18n.detect_language(request))

    if not deps.guest_has_access(reservation, billing.today()):
        return render_login_page(request, reservation, token, None, True)

    if too_many_login_attempts(token):
        return render_login_page(
            request, reservation, token, texts["too_many"], False)

    if last4.strip() == reservation["phone_last4"]:
        session_cookie = auth.sign_session(
            {"rid": reservation["id"]}, db.get_setting("secret"))
        response = RedirectResponse("/painel", status_code=303)
        response.set_cookie("guest_session", session_cookie, httponly=True,
                            samesite="lax", max_age=SESSION_COOKIE_MAX_AGE)
        return response

    with db.get_connection() as connection:
        connection.execute("INSERT INTO login_attempts(token) VALUES(?)", (token,))
    return render_login_page(
        request, reservation, token, texts["wrong_digits"], False)


# ---------------- painel ----------------

@router.get("/painel", response_class=HTMLResponse)
async def guest_panel(request: Request,
                      reservation: dict = Depends(deps.current_guest)):
    with db.get_connection() as connection:
        cards = [
            dict(row) for row in connection.execute(
                "SELECT * FROM cards WHERE enabled=1 ORDER BY position, id")
        ]

    # monta cada card ativo com o contexto do seu módulo
    card_views = []
    for card in cards:
        module = MODULE_REGISTRY.get(card["type"])
        if not module:
            continue
        context = await module["context"](card, reservation)
        card_views.append(
            {"card": card, "template": module["template"], "data": context})

    language = i18n.detect_language(request)
    response = get_templates(request).TemplateResponse(
        request, "guest/painel.html",
        {"reservation": reservation, "cards": card_views,
         "limit": deps.access_limit(reservation).isoformat(),
         "t": i18n.get_texts(language), "lang": language},
    )
    response.set_cookie("lang", language, max_age=LANG_COOKIE_MAX_AGE)
    return response


@router.get("/sair")
def guest_logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("guest_session")
    return response


# ---------------- APIs usadas pelo painel ----------------

@router.get("/api/energia")
async def energy_by_period(start: str, end: str,
                           reservation: dict = Depends(deps.current_guest)):
    """Consulta livre de consumo entre datas (apenas para controle)."""
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError:
        raise HTTPException(400, "Datas inválidas")

    # limita ao período da estadia até hoje
    start_date = max(start_date, date.fromisoformat(reservation["checkin"]))
    end_date = min(end_date, billing.today() + timedelta(days=1))
    if start_date >= end_date:
        raise HTTPException(400, "Período inválido")

    try:
        consumed_kwh = await billing.measure_kwh(start_date, end_date)
    except Exception as error:
        raise HTTPException(502, f"Erro ao consultar o sistema: {error}")

    tariff = float(db.get_setting("tariff", "0") or 0)
    return {"start": start_date.isoformat(), "end": end_date.isoformat(),
            "kwh": consumed_kwh, "value": round(consumed_kwh * tariff, 2)}


@router.post("/api/automacao/{entity_id}")
async def toggle_automation(entity_id: str,
                            reservation: dict = Depends(deps.current_guest)):
    """Alterna uma automação — somente as liberadas em algum card ativo."""
    with db.get_connection() as connection:
        automation_cards = [
            dict(row) for row in connection.execute(
                "SELECT * FROM cards WHERE enabled=1 AND type='automacoes'")
        ]
    allowed = {
        entity for card in automation_cards for entity in allowed_entities(card)
    }
    if entity_id not in allowed:
        raise HTTPException(403, "Automação não liberada")

    state = await home_assistant.get_state(entity_id)
    if not state:
        raise HTTPException(404, "Automação não encontrada no Home Assistant")

    service = "turn_off" if state["state"] == "on" else "turn_on"
    await home_assistant.call_service("automation", service, entity_id)
    return {"entity_id": entity_id, "on": service == "turn_on"}


# ---------------- fatura ----------------

@router.get("/fatura/{invoice_id}", response_class=HTMLResponse)
def invoice_page(request: Request, invoice_id: int,
                 reservation: dict = Depends(deps.current_guest)):
    with db.get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM invoices WHERE id=? AND reservation_id=?",
            (invoice_id, reservation["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Fatura não encontrada")

    invoice = dict(row)
    pix_code, pix_qr = billing.invoice_pix(invoice)
    language = i18n.detect_language(request)
    return get_templates(request).TemplateResponse(
        request, "guest/fatura.html",
        {"reservation": reservation, "invoice": invoice,
         "payload": pix_code, "qr": pix_qr,
         "pix_ok": bool(db.get_setting("pix_key")),
         "t": i18n.get_texts(language), "lang": language},
    )
