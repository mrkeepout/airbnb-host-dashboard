"""Card de conteúdo livre (Wi-Fi, regras da casa, avisos...)."""
import json


async def build_context(card: dict, reservation: dict) -> dict:
    config = json.loads(card.get("config") or "{}")
    return {"body": config.get("body", "")}


MODULE = {
    "type": "conteudo",
    "label": "Conteúdo livre (Wi-Fi, regras, avisos...)",
    "fields": [("body", "Texto do card (quebras de linha são mantidas)", "textarea")],
    "template": "cards/conteudo.html",
    "context": build_context,
}
