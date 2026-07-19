"""Dashboard do anfitrião: reservas, faturas, configurações e cards."""
import json
import re
import secrets
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import auth, billing, db, deps
from .. import ha as home_assistant
from ..modules import REGISTRY as MODULE_REGISTRY

router = APIRouter(prefix="/admin")

HOST_SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 dias

# chaves de configuração editáveis na tela de Configurações
SETTING_KEYS = ("tariff", "pix_key", "pix_name", "pix_city",
                "energy_sensor", "domain")


def get_templates(request: Request):
    return request.app.state.templates


# ---------------- login ----------------

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return get_templates(request).TemplateResponse(
        request, "admin/login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
def login(request: Request, password: str = Form(...)):
    stored_hash = db.get_setting("host_password_hash", "")
    if auth.check_password(password, stored_hash):
        session_cookie = auth.sign_session({"role": "host"},
                                           db.get_setting("secret"))
        response = RedirectResponse("/admin", status_code=303)
        response.set_cookie("host_session", session_cookie, httponly=True,
                            samesite="lax", max_age=HOST_SESSION_MAX_AGE)
        return response
    return get_templates(request).TemplateResponse(
        request, "admin/login.html", {"error": "Senha incorreta"})


@router.get("/sair")
def logout():
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("host_session")
    return response


# ---------------- dashboard / reservas ----------------

@router.get("", response_class=HTMLResponse)
def dashboard(request: Request, _: bool = Depends(deps.current_host)):
    reference_date = billing.today()
    with db.get_connection() as connection:
        reservations = [
            dict(row) for row in connection.execute(
                "SELECT * FROM reservations ORDER BY checkin DESC")
        ]
    for reservation in reservations:
        reservation["active"] = deps.guest_has_access(reservation, reference_date)

    return get_templates(request).TemplateResponse(
        request, "admin/dashboard.html",
        {"reservations": reservations,
         "domain": db.get_setting("domain", ""),
         "today": reference_date.isoformat()},
    )


@router.get("/reservas/nova", response_class=HTMLResponse)
def reservation_new_page(request: Request, _: bool = Depends(deps.current_host)):
    return get_templates(request).TemplateResponse(
        request, "admin/reserva_form.html", {"reservation": None})


@router.get("/reservas/{reservation_id}", response_class=HTMLResponse)
def reservation_edit_page(request: Request, reservation_id: int,
                          _: bool = Depends(deps.current_host)):
    with db.get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM reservations WHERE id=?", (reservation_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404)
        invoices = [
            dict(invoice) for invoice in connection.execute(
                "SELECT * FROM invoices WHERE reservation_id=? ORDER BY cycle",
                (reservation_id,))
        ]
    return get_templates(request).TemplateResponse(
        request, "admin/reserva_form.html",
        {"reservation": dict(row), "invoices": invoices,
         "domain": db.get_setting("domain", "")},
    )


@router.post("/reservas/salvar")
def reservation_save(
    _: bool = Depends(deps.current_host),
    rid: int = Form(0),
    guest_name: str = Form(...),
    cpf: str = Form(""),
    phone: str = Form(...),
    checkin: str = Form(...),
    checkout: str = Form(...),
    notes: str = Form(""),
):
    phone_digits = re.sub(r"\D", "", phone)
    if len(phone_digits) < 4:
        raise HTTPException(400, "Telefone inválido")
    date.fromisoformat(checkin)
    date.fromisoformat(checkout)
    if checkout <= checkin:
        raise HTTPException(400, "Check-out deve ser depois do check-in")

    with db.get_connection() as connection:
        if rid:  # edição
            connection.execute(
                "UPDATE reservations SET guest_name=?, cpf=?, phone=?, "
                "phone_last4=?, checkin=?, checkout=?, notes=? WHERE id=?",
                (guest_name, cpf, phone, phone_digits[-4:],
                 checkin, checkout, notes, rid))
            reservation_id = rid
        else:  # nova reserva
            magic_token = secrets.token_urlsafe(6)
            connection.execute(
                "INSERT INTO reservations"
                "(token,guest_name,cpf,phone,phone_last4,checkin,checkout,notes)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (magic_token, guest_name, cpf, phone, phone_digits[-4:],
                 checkin, checkout, notes))
            reservation_id = connection.execute(
                "SELECT last_insert_rowid() AS id").fetchone()["id"]

    return RedirectResponse(f"/admin/reservas/{reservation_id}", status_code=303)


@router.post("/reservas/{reservation_id}/excluir")
def reservation_delete(reservation_id: int, _: bool = Depends(deps.current_host)):
    with db.get_connection() as connection:
        connection.execute("DELETE FROM reservations WHERE id=?", (reservation_id,))
    return RedirectResponse("/admin", status_code=303)


@router.post("/reservas/{reservation_id}/liberar")
def reservation_extend_access(reservation_id: int,
                              extended_until: str = Form(""),
                              _: bool = Depends(deps.current_host)):
    """Liberação extraordinária: acesso além do check-out (vazio = remover)."""
    new_limit = extended_until or None
    if new_limit:
        date.fromisoformat(new_limit)
    with db.get_connection() as connection:
        connection.execute(
            "UPDATE reservations SET extended_until=? WHERE id=?",
            (new_limit, reservation_id))
    return RedirectResponse(f"/admin/reservas/{reservation_id}", status_code=303)


# ---------------- faturas ----------------

@router.post("/reservas/{reservation_id}/gerar-faturas")
async def generate_pending_invoices(reservation_id: int,
                                    _: bool = Depends(deps.current_host)):
    with db.get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM reservations WHERE id=?", (reservation_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404)
    await billing.ensure_invoices(dict(row))
    return RedirectResponse(f"/admin/reservas/{reservation_id}", status_code=303)


@router.post("/faturas/{invoice_id}/status")
def invoice_change_status(invoice_id: int, status: str = Form(...),
                          _: bool = Depends(deps.current_host)):
    if status not in ("aberta", "paga", "cancelada"):
        raise HTTPException(400)
    with db.get_connection() as connection:
        connection.execute(
            "UPDATE invoices SET status=? WHERE id=?", (status, invoice_id))
        row = connection.execute(
            "SELECT reservation_id FROM invoices WHERE id=?", (invoice_id,)
        ).fetchone()
    reservation_id = row["reservation_id"] if row else ""
    return RedirectResponse(f"/admin/reservas/{reservation_id}", status_code=303)


# ---------------- configurações ----------------

@router.get("/config", response_class=HTMLResponse)
async def settings_page(request: Request, _: bool = Depends(deps.current_host)):
    settings = {key: db.get_setting(key, "") for key in SETTING_KEYS}

    energy_sensors, automations, ha_error = [], [], None
    try:
        states = await home_assistant.get_states()
        energy_sensors = sorted(
            state["entity_id"] for state in states
            if state["entity_id"].startswith("sensor.")
            and state.get("attributes", {}).get("device_class") == "energy")
        automations = sorted(
            (state["entity_id"],
             state.get("attributes", {}).get("friendly_name", ""))
            for state in states if state["entity_id"].startswith("automation."))
    except Exception as error:
        ha_error = str(error)

    return get_templates(request).TemplateResponse(
        request, "admin/config.html",
        {"settings": settings, "sensors": energy_sensors,
         "automations": automations, "ha_error": ha_error},
    )


@router.post("/config")
async def settings_save(request: Request, _: bool = Depends(deps.current_host)):
    form = await request.form()
    for key in SETTING_KEYS:
        if key in form:
            db.set_setting(key, str(form[key]).strip())

    new_password = str(form.get("new_password") or "").strip()
    if new_password:
        db.set_setting("host_password_hash", auth.hash_password(new_password))

    return RedirectResponse("/admin/config", status_code=303)


# ---------------- cards (módulos do painel) ----------------

@router.get("/cards", response_class=HTMLResponse)
def cards_page(request: Request, _: bool = Depends(deps.current_host)):
    with db.get_connection() as connection:
        cards = [
            dict(row) for row in connection.execute(
                "SELECT * FROM cards ORDER BY position, id")
        ]
    for card in cards:
        card["cfg"] = json.loads(card["config"] or "{}")
        card["module"] = MODULE_REGISTRY.get(card["type"])

    return get_templates(request).TemplateResponse(
        request, "admin/cards.html",
        {"cards": cards, "registry": MODULE_REGISTRY})


@router.post("/cards/salvar")
async def card_save(request: Request, _: bool = Depends(deps.current_host)):
    form = await request.form()
    card_id = int(form.get("cid") or 0)
    card_type = str(form.get("type"))

    module = MODULE_REGISTRY.get(card_type)
    if not module:
        raise HTTPException(400, "Tipo de card desconhecido")

    title = str(form.get("title") or module["label"])
    config = {
        field_key: str(form.get(f"cfg_{field_key}") or "")
        for field_key, _label, _input_type in module["fields"]
    }
    enabled = 1 if form.get("enabled") else 0

    with db.get_connection() as connection:
        if card_id:  # edição
            connection.execute(
                "UPDATE cards SET title=?, config=?, enabled=? WHERE id=?",
                (title, json.dumps(config), enabled, card_id))
        else:  # novo card, vai para o fim da lista
            next_position = connection.execute(
                "SELECT COALESCE(MAX(position),-1)+1 AS next FROM cards"
            ).fetchone()["next"]
            connection.execute(
                "INSERT INTO cards(type,title,config,position,enabled)"
                " VALUES(?,?,?,?,?)",
                (card_type, title, json.dumps(config), next_position, enabled))

    return RedirectResponse("/admin/cards", status_code=303)


@router.post("/cards/{card_id}/excluir")
def card_delete(card_id: int, _: bool = Depends(deps.current_host)):
    with db.get_connection() as connection:
        connection.execute("DELETE FROM cards WHERE id=?", (card_id,))
    return RedirectResponse("/admin/cards", status_code=303)


@router.post("/cards/{card_id}/mover")
def card_move(card_id: int, direction: str = Form(...),
              _: bool = Depends(deps.current_host)):
    """Move o card uma posição para cima ('up') ou para baixo ('down')."""
    with db.get_connection() as connection:
        ordered_ids = [
            row["id"] for row in connection.execute(
                "SELECT id FROM cards ORDER BY position, id")
        ]
        if card_id in ordered_ids:
            index = ordered_ids.index(card_id)
            target = index - 1 if direction == "up" else index + 1
            if 0 <= target < len(ordered_ids):
                ordered_ids[index], ordered_ids[target] = (
                    ordered_ids[target], ordered_ids[index])
        for position, each_id in enumerate(ordered_ids):
            connection.execute(
                "UPDATE cards SET position=? WHERE id=?", (position, each_id))
    return RedirectResponse("/admin/cards", status_code=303)
