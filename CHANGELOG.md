# Changelog

## 1.1.1

- Correção do consumo de energia: o reset do contador do medidor (comum em
  medidores Tuya ao reiniciar) deixava a leitura negativa. Agora só as
  variações positivas são somadas, e a medição passou a ser por hora.
- Faturas com leitura ruim deixaram de ficar congeladas: enquanto estiverem
  abertas, são recalculadas sozinhas. Faturas pagas ou canceladas não mudam.
- Sensor sem leitura no período não gera mais fatura de 0,00 kWh.
- "Consultar outro período": a data "Até" agora inclui o dia informado, a
  faixa é limitada ao check-out e o período medido é exibido no resultado.
- Datas das faturas passam a mostrar o último dia realmente incluído, então
  faturas seguidas não aparecem mais compartilhando a mesma data.
- Novo diagnóstico do anfitrião em `/admin/energia/diagnostico` com as
  leituras brutas do sensor e as horas descartadas por reset.

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