# Painel do Apartamento — Add-on para Home Assistant OS

Painel web para hóspedes com consumo de energia, fatura com QR PIX,
controle de automações liberadas e cards de conteúdo — mais uma dashboard de
anfitrião para gerenciar reservas, faturas e módulos.

**Roda como add-on no Raspberry Pi 4 com Home Assistant OS.** Sem custo de
servidor; o acesso externo é feito via Cloudflare Tunnel.

---

## 1. Instalar o add-on no Home Assistant

Opção mais simples (add-on local, sem GitHub):

1. Instale o add-on oficial **Samba share** (ou **Studio Code Server**) para acessar as pastas do Pi.
2. Copie a pasta `painel_apto/` deste projeto para a pasta `addons/` do Home Assistant
   (via Samba: `\\homeassistant\addons`).
3. Em **Configurações → Add-ons → Loja de add-ons**, menu ⋮ → **Verificar atualizações**.
4. O add-on "Painel do Apartamento" aparece em **Add-ons locais** → instale.
   *(A primeira compilação no Pi 4 leva alguns minutos.)*
5. Na aba **Configuração** do add-on, defina a senha inicial do anfitrião e inicie.

Alternativa: suba este projeto num repositório GitHub e adicione a URL em
**Loja de add-ons → ⋮ → Repositórios**.

O painel fica em `http://IP_DO_PI:8234` na rede local.

## 2. Primeira configuração (dashboard do anfitrião)

Acesse `http://IP_DO_PI:8234/admin` e entre com a senha configurada no add-on. Em **Configurações**:

- **Sensor de energia**: escolha o sensor de kWh (classe `energy`, total crescente —
  o mesmo tipo usado no painel Energia do HA). É dele que o consumo é lido, via
  estatísticas de longo prazo.
- **Tarifa**: preço do kWh em R$ (ex.: `1.10`). Atualize quando a concessionária reajustar.
- **PIX**: sua chave, nome do recebedor (igual ao banco) e cidade. O QR gerado é o
  **PIX estático padrão BR Code** — funciona em qualquer banco, sem API. Você confirma
  o pagamento no seu extrato e marca a fatura como paga.
- **Domínio**: por enquanto use o placeholder `painel.SEU-DOMINIO.com.br`; troque
  quando comprar o domínio. (Usado só para montar o link mágico exibido.)
- Troque a senha do anfitrião. Se quiser mudar pelo Home Assistant, ajuste
  `senha_anfitriao_inicial` e reinicie o add-on.

## 3. Fluxo de reserva

1. **Reservas → Nova reserva**: nome, CPF, celular, check-in e check-out.
2. O sistema gera o **link mágico** (`https://seu-dominio/r/abc123`) — envie ao hóspede.
3. O hóspede abre o link e confirma com os **4 últimos dígitos do celular**
   (5 tentativas a cada 15 min, contra adivinhação).
4. O acesso é bloqueado automaticamente **1 dia após o check-out**. Para estender,
   use **Liberação extraordinária** na tela da reserva.

## 4. Energia e faturas

- O hóspede vê o consumo do ciclo atual desde o check-in e pode consultar
  qualquer período (somente controle).
- **Ciclo de faturamento**: do check-in até o 29º dia; no 30º dia a fatura dos
  29 dias anteriores é gerada (kWh × tarifa) com QR PIX e copia-e-cola.
  Estadias longas geram um ciclo a cada 29 dias; o último ciclo fecha no check-out.
- As faturas são geradas quando o painel é aberto, ou manualmente em
  **Reserva → Gerar faturas pendentes**. Marque como paga/cancelada na mesma tela.

## 5. Cards modulares

Em **Cards**, você monta o painel do hóspede: ativa/desativa, reordena e configura.
Módulos incluídos: **Consumo de energia**, **Automações** (informe os IDs liberados,
ex.: `automation.ar_condicionado_agenda`; a lista de IDs aparece em Configurações) e
**Conteúdo livre** (Wi-Fi, regras, instruções...).

Para criar um novo tipo de módulo: adicione um arquivo em `app/modules/` e um
template em `app/templates/cards/` — instruções em `app/modules/__init__.py`.
Nenhuma alteração no núcleo é necessária.

## 6. Acesso externo (Cloudflare Tunnel)

Quando tiver o domínio:

1. Crie uma conta gratuita na Cloudflare e aponte os nameservers do domínio para ela.
2. Instale o add-on **Cloudflared** (repositório de add-ons da comunidade) no HA.
3. Configure um tunnel com hostname adicional: `painel.SEU-DOMINIO.com.br` →
   `http://localhost:8234`.
4. Pronto: HTTPS automático, sem abrir portas no roteador.
5. Atualize o campo **Domínio** nas configurações do painel.

> Enquanto isso, tudo funciona na rede local via `http://IP_DO_PI:8234`.

## 7. Desenvolvimento / teste fora do add-on

```bash
pip install -r painel_apto/requirements.txt
export HA_URL=http://IP_DO_HA:8123   # e HA_TOKEN=token-de-longa-duracao
export DB_PATH=./painel.db HOST_PASSWORD=admin
cd painel_apto && uvicorn app.main:app --reload --port 8234
```

## Segurança

- Sessões assinadas (HMAC) em cookies httponly; senhas com PBKDF2.
- Hóspede só alcança automações explicitamente liberadas nos cards.
- Rate-limit no login do hóspede; acesso expira sozinho após o check-out.
- Recomendado usar sempre HTTPS (automático com Cloudflare Tunnel).
