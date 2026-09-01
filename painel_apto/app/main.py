"""Aplicação FastAPI: montagem, filtros de template e página inicial."""
import os
from datetime import date, timedelta

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

from . import db, i18n
from .routers import guest, host

BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def format_currency_brl(value):
    """1234.5 -> 'R$ 1.234,50'"""
    try:
        return (
            f"R$ {float(value):,.2f}"
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )
    except (TypeError, ValueError):
        return "-"


def _parse_date(value):
    """Aceita ISO simples com '-' ou '/' e retorna date."""
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    # Exemplos esperados: 2026-07-19, 2026/07/19, 2026-07-19T12:00:00
    normalized = text[:10].replace("/", "-")
    try:
        return date.fromisoformat(normalized)
    except ValueError:
        return None


@pass_context
def format_date_br(context, iso_date):
    """Formata data conforme região do navegador (Accept-Language)."""
    parsed = _parse_date(iso_date)
    if not parsed:
        return iso_date

    request = context.get("request") if context else None
    accept_language = ""
    if request:
        accept_language = request.headers.get("accept-language", "")

    # Primeiro idioma/região informado pelo navegador, ex: en-US,en;q=0.9
    locale_tag = accept_language.split(",")[0].split(";")[0].strip().lower()
    region = ""
    if "-" in locale_tag:
        _language, region = locale_tag.split("-", 1)

    if region.upper() == "US":
        return f"{parsed.month:02d}/{parsed.day:02d}/{parsed.year}"
    return f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year}"


@pass_context
def format_date_br_end(context, iso_date):
    """Fim de período exclusivo -> último dia realmente incluído."""
    parsed = _parse_date(iso_date)
    if not parsed:
        return iso_date
    return format_date_br(context, (parsed - timedelta(days=1)).isoformat())


templates.env.filters["brl"] = format_currency_brl
templates.env.filters["dbr"] = format_date_br
templates.env.filters["dbr_end"] = format_date_br_end

app = FastAPI(title="Painel do Apartamento", docs_url=None, redoc_url=None)
app.state.templates = templates
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static",
)
app.include_router(guest.router)
app.include_router(host.router)


@app.on_event("startup")
def initialize_database():
    db.init_db()


# Cabeçalhos de segurança em todas as respostas.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "script-src 'self'; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; form-action 'self'"
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()")
    response.headers["Content-Security-Policy"] = CONTENT_SECURITY_POLICY
    # HSTS só faz sentido quando o acesso chega por HTTPS (Cloudflare)
    if request.headers.get("x-forwarded-proto") == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains")
    return response


@app.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    """Pede aos buscadores/crawlers para não indexar nada."""
    return "User-agent: *\nDisallow: /\n"


@app.get("/", response_class=HTMLResponse)
def home_page(request: Request, expirado: int = 0):
    language = i18n.detect_language(request)
    return templates.TemplateResponse(
        request, "guest/inicio.html",
        {"expirado": expirado, "t": i18n.get_texts(language), "lang": language},
    )
