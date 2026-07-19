"""Faturamento: ciclos de 29 dias, tarifa e PIX estático (BR Code)."""
import base64
import io
import unicodedata
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import segno

from . import db, ha

CYCLE_LENGTH_DAYS = 29


# ---------------- datas / fuso horário ----------------

def get_timezone() -> ZoneInfo:
    return ZoneInfo(db.get_setting("timezone", "America/Fortaleza"))


def today() -> date:
    return datetime.now(get_timezone()).date()


def local_midnight(day: date) -> datetime:
    """Meia-noite local da data (usada como limite nas consultas ao HA)."""
    return datetime.combine(day, time.min, tzinfo=get_timezone())


# ---------------- ciclos de faturamento ----------------

def billing_cycles(checkin: date, checkout: date):
    """Gera os ciclos de 29 dias da estadia, limitados ao check-out.

    Retorna tuplas (numero, inicio, fim); o consumo é medido em [inicio, fim).
    A fatura de um ciclo é gerada quando ele termina (30º dia).
    """
    cycle_number = 0
    cycle_start = checkin
    while cycle_start < checkout:
        cycle_end = min(cycle_start + timedelta(days=CYCLE_LENGTH_DAYS), checkout)
        yield cycle_number, cycle_start, cycle_end
        cycle_start = cycle_end
        cycle_number += 1


def finished_cycles(checkin: date, checkout: date, reference_date: date):
    """Ciclos já encerrados na data de referência (fatura deve existir)."""
    return [
        (number, start, end)
        for number, start, end in billing_cycles(checkin, checkout)
        if reference_date >= end
    ]


async def measure_kwh(start: date, end: date) -> float:
    """Consumo em kWh no período, lido do sensor configurado."""
    sensor_entity_id = db.get_setting("energy_sensor")
    if not sensor_entity_id:
        raise RuntimeError("Sensor de energia não configurado")
    return await ha.energy_between(
        sensor_entity_id, local_midnight(start), local_midnight(end)
    )


async def ensure_invoices(reservation: dict) -> None:
    """Gera as faturas de ciclos encerrados que ainda não existem no banco."""
    checkin = date.fromisoformat(reservation["checkin"])
    checkout = date.fromisoformat(reservation["checkout"])
    tariff = float(db.get_setting("tariff", "0") or 0)

    with db.get_connection() as connection:
        existing_cycles = {
            row["cycle"]
            for row in connection.execute(
                "SELECT cycle FROM invoices WHERE reservation_id=?",
                (reservation["id"],),
            )
        }

    for cycle_number, start, end in finished_cycles(checkin, checkout, today()):
        if cycle_number in existing_cycles:
            continue
        consumed_kwh = await measure_kwh(start, end)
        with db.get_connection() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO invoices"
                "(reservation_id,cycle,period_start,period_end,kwh,tariff,amount)"
                " VALUES(?,?,?,?,?,?,?)",
                (reservation["id"], cycle_number, start.isoformat(),
                 end.isoformat(), consumed_kwh, tariff,
                 round(consumed_kwh * tariff, 2)),
            )


# ---------------- PIX estático (BR Code / EMVCo) ----------------

def emv_field(tag: str, value: str) -> str:
    """Campo EMV: tag + tamanho (2 dígitos) + valor."""
    return f"{tag}{len(value):02d}{value}"


def crc16_ccitt(payload: str) -> str:
    """CRC16-CCITT-FALSE exigido pelo padrão BR Code (campo 63)."""
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if (crc & 0x8000) else (crc << 1)
            crc &= 0xFFFF
    return f"{crc:04X}"


def sanitize_text(text: str, max_length: int) -> str:
    """Remove acentos e caracteres inválidos (exigência do BR Code)."""
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = "".join(ch for ch in text if ch.isalnum() or ch in " .-")
    return text.strip()[:max_length] or "N"


def pix_payload(pix_key: str, receiver_name: str, receiver_city: str,
                amount: float, transaction_id: str = "***") -> str:
    """Gera o payload 'copia e cola' do PIX estático com valor."""
    merchant_account_info = (
        emv_field("00", "br.gov.bcb.pix") + emv_field("01", pix_key.strip())
    )
    payload = (
        emv_field("00", "01")                       # formato
        + emv_field("26", merchant_account_info)    # chave PIX
        + emv_field("52", "0000")                   # categoria do lojista
        + emv_field("53", "986")                    # moeda: BRL
        + emv_field("54", f"{amount:.2f}")          # valor
        + emv_field("58", "BR")
        + emv_field("59", sanitize_text(receiver_name, 25))
        + emv_field("60", sanitize_text(receiver_city, 15))
        + emv_field("62", emv_field("05", transaction_id[:25]))  # txid
        + "6304"                                    # tag+tamanho do CRC
    )
    return payload + crc16_ccitt(payload)


def pix_qr_svg_data_uri(payload: str) -> str:
    """QR Code do payload como data URI SVG (leve, sem Pillow)."""
    buffer = io.BytesIO()
    segno.make(payload, error="m").save(
        buffer, kind="svg", scale=5, border=2, dark="#1a1a2e", xmldecl=False
    )
    return "data:image/svg+xml;base64," + base64.b64encode(buffer.getvalue()).decode()


def invoice_pix(invoice: dict) -> tuple[str, str]:
    """Retorna (payload copia-e-cola, QR em data URI) para uma fatura."""
    pix_key = db.get_setting("pix_key", "")
    receiver_name = db.get_setting("pix_name", "Anfitriao")
    receiver_city = db.get_setting("pix_city", "Natal")
    payload = pix_payload(
        pix_key, receiver_name, receiver_city, float(invoice["amount"]),
        transaction_id=f"FAT{invoice['id']:06d}",
    )
    return payload, pix_qr_svg_data_uri(payload)
