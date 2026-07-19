// Interações do painel do hóspede
const T = window.I18N || {};
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
      out.innerHTML = `<strong>${d.kwh.toFixed(1)} kWh</strong> — R$ ${d.value.toFixed(2).replace('.', ',')}`;
    } else {
      const e = await r.json().catch(() => ({}));
      out.textContent = e.detail || T.error || 'Erro';
    }
  }
});

const endInput = document.getElementById('en-end');
if (endInput && !endInput.value) {
  endInput.value = new Date().toISOString().slice(0, 10);
}
