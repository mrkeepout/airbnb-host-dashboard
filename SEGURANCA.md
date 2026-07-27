# Segurança do Painel

Nenhum sistema é "imune" — a estratégia é defesa em camadas: cada camada
segura o que escapou da anterior.

## Por que o Home Assistant está protegido

- A porta 8123 do HA **não está exposta** no tunnel — só o painel (8234).
- O token do HA (`SUPERVISOR_TOKEN`) vive apenas dentro do container;
  nunca vai ao navegador de ninguém.
- O hóspede não fala com o HA: ele fala com o painel, que só repassa três
  operações (ler estatísticas de energia, ler estado e ligar/desligar
  automações **explicitamente liberadas** por você em um card).
- Mesmo um invasor com sessão de hóspede válida não consegue: ver outras
  reservas, chamar outros serviços do HA, ler sensores não configurados.

## Camadas no código (já ativas)

| Proteção | Onde |
|---|---|
| Rate-limit login hóspede (5/15min por reserva) | `routers/guest.py` |
| Rate-limit login admin (5/15min por IP + trava global) | `security.py` + `routers/host.py` |
| 2FA TOTP opcional no admin | Configurações → Segurança |
| Senha com PBKDF2 (200k iterações), comparação em tempo constante | `auth.py` |
| Sessões em cookie httponly assinado (HMAC), admin em SameSite=Strict + Secure | `auth.py`, `routers/host.py` |
| Cabeçalhos: CSP, X-Frame-Options, nosniff, Referrer-Policy, HSTS | `main.py` |
| SQL 100% parametrizado; templates com autoescape (Jinja2) | todo o projeto |
| Acesso do hóspede expira sozinho (checkout + 1 dia) | `deps.py` |
| robots.txt bloqueando indexação | `main.py` |

## Camadas na Cloudflare (configure uma vez — 10 min)

No dashboard da Cloudflare, com o site selecionado:

1. **Security → Settings → Bot Fight Mode: ON.** Bloqueia a maior parte dos
   bots/scanners automatizados antes de chegarem ao Pi.
2. **SSL/TLS → Edge Certificates → Always Use HTTPS: ON.**
3. **Security → WAF → Rate limiting rules** (plano free inclui 1 regra):
   caminho `contém /admin` → 10 requisições/minuto por IP → Block.
   Isso torna força-bruta inviável mesmo sem o rate-limit do app.
4. **(Recomendação forte) Zero Trust → Access:** crie uma aplicação
   protegendo `www.SEUDOMINIO.com.br/admin*`, com política permitindo só o
   seu e-mail (código de verificação por e-mail a cada login). Com isso,
   bots e pentesters **nem enxergam** a tela de login do admin — a Cloudflare
   exige identidade antes. Grátis até 50 usuários. O painel do hóspede
   (`/r/...`, `/painel`) fica de fora, funcionando normal.
5. Mantenha o registro DNS com **proxy ativado** (nuvem laranja): seu IP
   residencial nunca aparece.

## Boas práticas de operação

- Senha do anfitrião longa e única (é ela que protege tudo); ative o 2FA.
- Atualize o add-on e o Home Assistant OS regularmente.
- O banco `/data/painel.db` contém dados pessoais de hóspedes — está fora do
  Git (`.gitignore`) e deve ficar fora de qualquer lugar público.
- Ao pedir ajuda em fóruns, nunca cole logs sem revisar (tokens, nomes, IPs).
- Backups do HA incluem o add-on e o banco: mantenha o backup automático do
  HAOS ativo.

## O que fazer se suspeitar de invasão

1. Pare o add-on Cloudflared (derruba o acesso externo na hora).
2. Troque a senha do anfitrião e gere novo segredo de sessão
   (apague a linha `secret` da tabela `settings` e reinicie o add-on —
   isso desloga todas as sessões).
3. Revise as reservas/liberações extraordinárias criadas.
4. Verifique o log do HA em Configurações → Logs.
