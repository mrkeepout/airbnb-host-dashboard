"""Banco de dados SQLite: conexão, schema e configurações (settings)."""
import json
import os
import secrets
import sqlite3
import hashlib

DATABASE_PATH = os.environ.get(
    "DB_PATH",
    "/data/painel.db" if os.path.isdir("/data")
    else os.path.join(os.path.dirname(__file__), "..", "painel.db"),
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);

CREATE TABLE IF NOT EXISTS reservations(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT UNIQUE NOT NULL,            -- slug do link mágico (/r/<token>)
  guest_name TEXT NOT NULL,
  cpf TEXT DEFAULT '',
  phone TEXT DEFAULT '',
  phone_last4 TEXT NOT NULL,             -- usado como "senha" do hóspede
  checkin TEXT NOT NULL,                 -- ISO yyyy-mm-dd
  checkout TEXT NOT NULL,
  extended_until TEXT,                   -- liberação extraordinária (opcional)
  notes TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invoices(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reservation_id INTEGER NOT NULL REFERENCES reservations(id) ON DELETE CASCADE,
  cycle INTEGER NOT NULL,                -- nº do ciclo de 29 dias (0, 1, 2...)
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  kwh REAL NOT NULL,
  tariff REAL NOT NULL,                  -- R$/kWh na data da geração
  amount REAL NOT NULL,                  -- kwh * tariff
  status TEXT DEFAULT 'aberta',          -- aberta | paga | cancelada
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(reservation_id, cycle)
);

CREATE TABLE IF NOT EXISTS cards(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  type TEXT NOT NULL,                    -- tipo do módulo (app/modules/)
  title TEXT NOT NULL,
  config TEXT DEFAULT '{}',              -- JSON com a configuração do módulo
  position INTEGER DEFAULT 0,
  enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS login_attempts(
  token TEXT NOT NULL,
  ts TEXT DEFAULT (datetime('now'))
);
"""


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def get_setting(key: str, default=None):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT value FROM settings WHERE key=?", (key,)
        ).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )


def _read_addon_options() -> dict:
    """Opções definidas na aba Configuração do add-on (Home Assistant)."""
    if os.path.isfile("/data/options.json"):
        with open("/data/options.json") as options_file:
            return json.load(options_file)
    return {}


def _sync_host_password_from_addon_options(addon_options: dict):
    """Aplica a senha do add-on quando ela muda na configuração do Home Assistant."""
    from . import auth

    initial_password = str(
        addon_options.get("senha_anfitriao_inicial")
        or os.environ.get("HOST_PASSWORD", "admin")
    ).strip()
    if not initial_password:
        return

    source_fingerprint = hashlib.sha256(initial_password.encode()).hexdigest()
    if get_setting("host_password_source_hash") == source_fingerprint:
        return

    set_setting("host_password_hash", auth.hash_password(initial_password))
    set_setting("host_password_source_hash", source_fingerprint)


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DATABASE_PATH)), exist_ok=True)
    with get_connection() as connection:
        connection.executescript(SCHEMA)

    addon_options = _read_addon_options()

    # segredo usado para assinar os cookies de sessão
    if not get_setting("secret"):
        set_setting("secret", secrets.token_hex(32))

    # senha do anfitrião: sincroniza com a opção do add-on quando ela muda
    _sync_host_password_from_addon_options(addon_options)

    if addon_options.get("fuso_horario"):
        set_setting("timezone", addon_options["fuso_horario"])

    # cards padrão do painel do hóspede (apenas na primeira inicialização)
    with get_connection() as connection:
        total_cards = connection.execute(
            "SELECT COUNT(*) AS total FROM cards"
        ).fetchone()["total"]
        if total_cards == 0:
            default_cards = [
                ("hospede", "Sua reserva", "{}"),
                ("energia", "Consumo de energia", "{}"),
                ("automacoes", "Automações", json.dumps({"entities": ""})),
            ]
            for position, (card_type, title, config) in enumerate(default_cards):
                connection.execute(
                    "INSERT INTO cards(type,title,config,position) VALUES(?,?,?,?)",
                    (card_type, title, config, position),
                )
