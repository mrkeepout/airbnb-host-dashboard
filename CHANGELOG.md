# Changelog

## 1.1.0

- Segurança: 2FA opcional no login do anfitrião (TOTP — Google Authenticator).
- Segurança: bloqueio por IP após 5 tentativas de senha erradas (15 min).
- Segurança: cabeçalhos HTTP de proteção (CSP, HSTS, X-Frame-Options etc.),
  cookie do admin em modo strict/secure e robots.txt bloqueando indexação.
- Segurança: CSP estrita — `script-src 'self'`, sem scripts/handlers inline
  (movidos para `static/comum.js` com data-attributes).
- Novo guia SEGURANCA.md com as proteções recomendadas na Cloudflare.

## 1.0.4

- Correção da barra de navegação.

## 1.0.3

- Correção da senha inicial. 
- Melhoria na barra de navegação.

## 1.0.2

- Novo card: instruções de check-out.

## 1.0.1

- Correções gerais de bugs.

## 1.0.0

- Versão inicial: painel do hóspede, dashboard do anfitrião, PIX, idiomas.