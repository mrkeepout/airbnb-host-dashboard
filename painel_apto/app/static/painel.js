// Interações do painel do hóspede
// Textos traduzidos vêm dos atributos data-* do elemento #i18n (CSP estrita,
// sem script inline).
const i18nElement = document.getElementById('i18n');
const T = i18nElement ? {
  choose: i18nElement.dataset.choose,
  query: i18nElement.dataset.query,
  error: i18nElement.dataset.error,
  toggle_error: i18nElement.dataset.toggleError,
} : {};
document.addEventListener('click', async (ev) => {
  const sw = ev.target.closest('.switch[data-entity]');
  if (sw && !sw.disabled) {
    sw.disabled = true;
    try {
      const r = await fetch('/api/automacao/' + encodeURIComponent(sw.dataset.entity),
                            { method: 'POST' });
      if (r.ok) {
        const data = await r.json();
        sw.classList.toggle('on', data.on);
      } else {
        alert(T.toggle_error || 'Erro');
      }
    } finally { sw.disabled = false; }
  }

  if (ev.target.id === 'en-go') {
    const start = document.getElementById('en-start').value;
    const end = document.getElementById('en-end').value;
    const out = document.getElementById('en-result');
    if (!start || !end) { out.textContent = T.choose || 'Escolha as duas datas.'; return; }
    out.textContent = T.query || '...';
    const r = await fetch(`/api/energia?start=${start}&end=${end}`);
    if (r.ok) {
      const d = await r.json();
      if (typeof d.kwh !== 'number') { out.textContent = T.error || 'Erro'; return; }
      // o servidor pode ter encurtado a faixa (limite da estadia / hoje)
      const range = `${brDate(d.start)} – ${brDate(d.end)}`;
      const strong = document.createElement('strong');
      strong.textContent = `${d.kwh.toFixed(1)} kWh`;
      const small = document.createElement('small');
      small.textContent = range;
      out.replaceChildren(strong, ` — R$ ${d.value.toFixed(2).replace('.', ',')}`, document.createElement('br'), small);
    } else {
      const e = await r.json().catch(() => ({}));
      out.textContent = e.detail || T.error || 'Erro';
    }
  }
});

// '2026-08-30' -> '30/08/2026'
function brDate(iso) {
  const p = String(iso || '').split('-');
  return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : iso;
}

// o último dia consultável vem do template (fim da estadia ou hoje, o que
// vier primeiro), então não usamos a data do dispositivo
const endInput = document.getElementById('en-end');
if (endInput && !endInput.value) {
  endInput.value = endInput.max || new Date().toISOString().slice(0, 10);
}
