// Comportamentos compartilhados (hóspede + anfitrião), sem scripts inline
// para permitir uma Content-Security-Policy estrita (script-src 'self').

// Copiar para a área de transferência: <button data-copy-target="id-do-elemento"
// data-copied-label="Copiado"> — com fallback para HTTP (rede local).
function copyFromElement(sourceId, button, copiedLabel) {
  const source = document.getElementById(sourceId);
  if (!source) return;
  const text = source.value !== undefined ? source.value : source.textContent;
  const markAsCopied = () => { button.textContent = copiedLabel; };
  const fallback = () => {
    source.focus();
    source.select();
    try { document.execCommand('copy'); markAsCopied(); }
    catch (err) { alert(text); }
    window.getSelection().removeAllRanges();
    button.blur();
  };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(markAsCopied, fallback);
  } else {
    fallback();
  }
}

document.addEventListener('click', (event) => {
  const copyButton = event.target.closest('[data-copy-target]');
  if (copyButton) {
    copyFromElement(copyButton.dataset.copyTarget, copyButton,
                    copyButton.dataset.copiedLabel || 'Copiado ✓');
  }
});

// Confirmação antes de enviar: <form data-confirm="Tem certeza?">
document.addEventListener('submit', (event) => {
  const form = event.target;
  if (form.dataset && form.dataset.confirm && !confirm(form.dataset.confirm)) {
    event.preventDefault();
  }
});

// Select que envia o formulário ao mudar: <select data-autosubmit>
document.addEventListener('change', (event) => {
  if (event.target.matches('select[data-autosubmit]')) {
    event.target.form.submit();
  }
});
