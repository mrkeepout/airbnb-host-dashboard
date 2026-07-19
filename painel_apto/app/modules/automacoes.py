"""Card de automações: liga/desliga apenas as automações liberadas."""
import json

from .. import ha


def allowed_entities(card: dict) -> list[str]:
    """IDs de automação liberados na configuração do card."""
    config = json.loads(card.get("config") or "{}")
    raw_list = (config.get("entities") or "").replace("\n", ",")
    return [entity.strip() for entity in raw_list.split(",") if entity.strip()]


async def build_context(card: dict, reservation: dict) -> dict:
    entity_ids = allowed_entities(card)
    config = json.loads(card.get("config") or "{}")
    automations = []
    error_message = None

    if entity_ids:
        try:
            states_by_id = {
                state["entity_id"]: state
                for state in await ha.get_states("automation.")
            }
            for entity_id in entity_ids:
                state = states_by_id.get(entity_id)
                automations.append({
                    "entity_id": entity_id,
                    "name": (state or {}).get("attributes", {})
                            .get("friendly_name", entity_id),
                    "is_on": (state or {}).get("state") == "on",
                    "found": state is not None,
                })
        except Exception as error:
            error_message = str(error)

    return {
        "automations": automations,
        "error": error_message,
        "icon": (config.get("icon") or "⚡").strip() or "⚡",
        "description": (config.get("description") or "").strip(),
    }


MODULE = {
    "type": "automacoes",
    "label": "Grupo de automações",
    "fields": [
        ("icon", "Ícone do grupo (emoji ou texto curto)", "text"),
        ("description", "Descrição do grupo", "textarea"),
        ("entities",
         "IDs das automações permitidas (uma por linha ou separadas por vírgula)",
         "textarea"),
    ],
    "template": "cards/automacoes.html",
    "context": build_context,
}
