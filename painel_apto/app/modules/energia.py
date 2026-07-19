"""Card de consumo de energia: ciclo atual, valor estimado e faturas."""
from datetime import date, timedelta

from .. import billing, db


def _find_current_cycle(checkin: date, checkout: date, reference_date: date):
    """Ciclo de 29 dias que contém a data de referência (ou o último)."""
    current = None
    for cycle in billing.billing_cycles(checkin, checkout):
        _number, start, end = cycle
        if start <= reference_date < end:
            current = cycle
        elif reference_date >= checkout and end == checkout:
            current = cycle
    return current


async def build_context(card: dict, reservation: dict) -> dict:
    checkin = date.fromisoformat(reservation["checkin"])
    checkout = date.fromisoformat(reservation["checkout"])
    reference_date = billing.today()
    tariff = float(db.get_setting("tariff", "0") or 0)

    current_cycle = _find_current_cycle(checkin, checkout, reference_date)
    consumed_kwh = None
    error_message = None

    try:
        if current_cycle:
            _number, cycle_start, cycle_end = current_cycle
            measure_until = min(reference_date + timedelta(days=1), cycle_end)
            consumed_kwh = await billing.measure_kwh(cycle_start, measure_until)
    except Exception as error:
        error_message = str(error)

    # garante que faturas de ciclos encerrados existam
    try:
        await billing.ensure_invoices(reservation)
    except Exception as error:
        error_message = error_message or str(error)

    with db.get_connection() as connection:
        invoices = [
            dict(row) for row in connection.execute(
                "SELECT * FROM invoices WHERE reservation_id=? ORDER BY cycle",
                (reservation["id"],),
            )
        ]

    # progresso do ciclo (para o anel do gauge)
    day_number = total_days = 0
    if current_cycle:
        _number, cycle_start, cycle_end = current_cycle
        total_days = (cycle_end - cycle_start).days
        day_number = min(max((reference_date - cycle_start).days + 1, 1), total_days)

    return {
        "kwh": consumed_kwh,
        "estimated_value": round(consumed_kwh * tariff, 2)
        if consumed_kwh is not None else None,
        "tariff": tariff,
        "cycle": current_cycle,
        "day_number": day_number,
        "total_days": total_days,
        "invoices": invoices,
        "error": error_message,
        "checkin": reservation["checkin"],
    }


MODULE = {
    "type": "energia",
    "label": "Consumo de energia",
    "fields": [],
    "template": "cards/energia.html",
    "context": build_context,
}
