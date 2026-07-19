"""Registro de módulos (cards) do painel do hóspede.

Para criar um novo módulo:
1. Crie um arquivo em app/modules/ definindo MODULE = {...} (veja os existentes);
2. Crie o template em app/templates/cards/<tipo>.html;
3. Importe o arquivo aqui embaixo. Nada mais no núcleo precisa mudar —
   o card aparece automaticamente na dashboard do anfitrião.

Estrutura de MODULE:
  type      – identificador único (também é o nome do template)
  label     – nome exibido na dashboard do anfitrião
  fields    – campos de configuração [(chave, rótulo, tipo html: text|textarea)]
  template  – caminho do template do card
  context   – corrotina async (card, reservation) -> dict com dados do template
"""
from . import hospede, energia, automacoes, conteudo  # noqa: F401

REGISTRY: dict[str, dict] = {}
for module in (hospede.MODULE, energia.MODULE, automacoes.MODULE, conteudo.MODULE):
    REGISTRY[module["type"]] = module
