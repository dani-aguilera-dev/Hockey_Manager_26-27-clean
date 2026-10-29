(() => {
  const layer = document.getElementById('game-menu');
  const trigger = document.getElementById('game-menu-trigger');
  if (!layer || !trigger) return;

  const panel = layer.querySelector('.game-menu-panel');
  let previousFocus = null;

  const focusables = () => Array.from(panel.querySelectorAll(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )).filter((el) => el.offsetParent !== null);

  const open = () => {
    previousFocus = document.activeElement;
    layer.hidden = false;
    trigger.setAttribute('aria-expanded', 'true');
    document.body.classList.add('menu-open');
    const first = focusables()[0];
    if (first) first.focus();
  };

  const close = () => {
    layer.hidden = true;
    trigger.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('menu-open');
    if (previousFocus && typeof previousFocus.focus === 'function') previousFocus.focus();
  };

  trigger.addEventListener('click', open);
  layer.querySelectorAll('[data-menu-close]').forEach((el) => el.addEventListener('click', close));

  document.addEventListener('keydown', (event) => {
    if (layer.hidden) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      close();
      return;
    }
    if (event.key !== 'Tab') return;
    const items = focusables();
    if (!items.length) return;
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  document.querySelectorAll('[data-menu-back]').forEach((link) => {
    link.addEventListener('click', (event) => {
      if (history.length > 1) {
        event.preventDefault();
        history.back();
      }
    });
  });

  document.querySelectorAll('form[data-confirm-exit]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (form.dataset.confirmExit !== 'true') return;
      if (!window.confirm('¿Salir de la partida y volver al menú principal? Se guardará el progreso actual.')) {
        event.preventDefault();
      }
    });
  });
})();
