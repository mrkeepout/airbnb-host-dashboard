"""Card com os dados da reserva (nome, check-in, check-out, noites)."""
from datetime import date


async def build_context(card: dict, reservation: dict) -> dict:
    checkin = date.fromisoformat(reservation["checkin"])
    checkout = date.fromisoformat(reservation["checkout"])
    return {"nights": (checkout - checkin).days}


MODULE = {
    "type": "hospede",
    "label": "Dados do hóspede (nome, check-in, check-out)",
    "fields": [],
    "template": "cards/hospede.html",
    "context": build_context,
}
