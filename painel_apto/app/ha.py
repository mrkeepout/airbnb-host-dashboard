"""Cliente da API do Home Assistant (REST + WebSocket).

Dentro do add-on usa http://supervisor/core + SUPERVISOR_TOKEN (automático).
Para desenvolvimento local, defina as variáveis HA_URL e HA_TOKEN.
"""
import os
from datetime import datetime

import aiohttp

BASE_URL = os.environ.get("HA_URL", "http://supervisor/core").rstrip("/")
ACCESS_TOKEN = os.environ.get("SUPERVISOR_TOKEN") or os.environ.get("HA_TOKEN", "")
WEBSOCKET_URL = (
    "ws" + BASE_URL[4:] if BASE_URL.startswith("http") else BASE_URL
) + "/websocket"
HEADERS = {"Authorization": f"Bearer {ACCESS_TOKEN}",
           "Content-Type": "application/json"}


async def get_states(domain_prefix: str | None = None) -> list[dict]:
    """Lista os estados de todas as entidades (opcionalmente por domínio)."""
    async with aiohttp.ClientSession(headers=HEADERS) as http:
        async with http.get(f"{BASE_URL}/api/states") as response:
            response.raise_for_status()
            states = await response.json()
    if domain_prefix:
        states = [s for s in states if s["entity_id"].startswith(domain_prefix)]
    return states


async def get_state(entity_id: str) -> dict | None:
    async with aiohttp.ClientSession(headers=HEADERS) as http:
        async with http.get(f"{BASE_URL}/api/states/{entity_id}") as response:
            if response.status != 200:
                return None
            return await response.json()


async def call_service(domain: str, service: str, entity_id: str):
    """Ex.: call_service('automation', 'turn_on', 'automation.modo_eco')."""
    async with aiohttp.ClientSession(headers=HEADERS) as http:
        async with http.post(
            f"{BASE_URL}/api/services/{domain}/{service}",
            json={"entity_id": entity_id},
        ) as response:
            response.raise_for_status()
            return await response.json()


async def energy_between(entity_id: str, start: datetime, end: datetime) -> float:
    """Consumo (kWh) entre duas datas, via estatísticas de longo prazo.

    Usa o comando WebSocket `recorder/statistics_during_period` com o tipo
    "change" (variação por dia) e soma os valores do período.
    """
    request_message = {
        "id": 1,
        "type": "recorder/statistics_during_period",
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "statistic_ids": [entity_id],
        "period": "day",
        "types": ["change"],
    }
    async with aiohttp.ClientSession() as http:
        async with http.ws_connect(WEBSOCKET_URL) as websocket:
            first_message = await websocket.receive_json()
            if first_message.get("type") == "auth_required":
                await websocket.send_json(
                    {"type": "auth", "access_token": ACCESS_TOKEN}
                )
                auth_reply = await websocket.receive_json()
                if auth_reply.get("type") != "auth_ok":
                    raise RuntimeError("Falha de autenticação no WebSocket do HA")
            await websocket.send_json(request_message)
            while True:
                reply = await websocket.receive_json()
                if reply.get("id") == 1 and reply.get("type") == "result":
                    if not reply.get("success"):
                        raise RuntimeError(f"Erro do HA: {reply.get('error')}")
                    daily_changes = reply["result"].get(entity_id, [])
                    total_kwh = sum(day.get("change") or 0 for day in daily_changes)
                    return round(total_kwh, 3)
