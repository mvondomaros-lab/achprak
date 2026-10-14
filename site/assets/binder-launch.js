/* German status display for Binder's public event stream; the link works without JS. */
(() => {
  const panel = document.querySelector('[data-binder-launch]');
  if (!panel) return;
  const start = panel.querySelector('[data-binder-start]');
  const progress = panel.querySelector('.binder-progress');
  const status = panel.querySelector('.binder-status');
  const elapsed = panel.querySelector('.binder-elapsed');
  const retry = panel.querySelector('[data-binder-retry]');
  const stages = [...panel.querySelectorAll('.binder-stages li')];
  const launch = new URL(start.href);
  const endpoint = new URL(launch.pathname.replace('/v2/', '/build/'), launch.origin);
  const phases = {
    waiting: [0, 'Binder wartet auf einen freien Startplatz.'],
    fetching: [0, 'Die Dateien für PhotoSwitchLab werden geladen.'],
    building: [1, 'Die benötigten Programme werden eingerichtet.'],
    pushing: [1, 'Die vorbereiteten Programme werden gespeichert.'],
    built: [1, 'Die Programme sind bereit.'],
    launching: [2, 'Ihre eigene Sitzung wird gestartet.'],
    ready: [3, 'PhotoSwitchLab wird geöffnet.'],
  };
  let stream = null;
  let clock = null;
  let activeStage = 0;

  function stop() {
    if (stream) stream.close();
    stream = null;
    clearInterval(clock);
    clock = null;
  }

  function fail(message) {
    stop();
    if (status.textContent !== message) status.textContent = message;
    retry.hidden = false;
  }

  function showStage(stage, message) {
    activeStage = Math.max(activeStage, stage);
    for (const [index, item] of stages.entries()) {
      item.dataset.state = index < activeStage ? 'done' : index === activeStage ? 'current' : 'pending';
      if (index === activeStage) item.setAttribute('aria-current', 'step');
      else item.removeAttribute('aria-current');
    }
    if (status.textContent !== message) status.textContent = message;
  }

  function run() {
    if (stream) return;
    if (!window.EventSource) {
      window.location.assign(launch.href);
      return;
    }
    start.hidden = true;
    progress.hidden = false;
    retry.hidden = true;
    activeStage = 0;
    showStage(0, 'Die Verbindung zu Binder wird hergestellt.');
    status.focus();
    panel.scrollIntoView({block: 'start'});
    const began = Date.now();
    const tick = () => {
      const seconds = Math.floor((Date.now() - began) / 1000);
      elapsed.textContent = `Wartezeit: ${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')} min`;
    };
    tick();
    clock = setInterval(tick, 1000);
    try {
      stream = new window.EventSource(endpoint.href);
    } catch (_) {
      fail('Die Verbindung zu Binder konnte nicht hergestellt werden. Öffnen Sie die Binder-Startseite oder versuchen Sie es erneut.');
      return;
    }
    const connection = stream;
    connection.onmessage = event => {
      if (stream !== connection) return;
      let data;
      try { data = JSON.parse(event.data); }
      catch (_) { fail('Die Startanzeige konnte nicht gelesen werden. Öffnen Sie die Binder-Startseite.'); return; }
      const phase = typeof data?.phase === 'string' ? data.phase.toLowerCase() : '';
      if (phase === 'failed') {
        fail('Binder konnte Ihre Sitzung nicht starten. Versuchen Sie es erneut oder öffnen Sie die Binder-Startseite.');
        return;
      }
      if (phases[phase]) showStage(...phases[phase]);
      if (phase === 'ready') {
        try {
          const base = new URL(data.url);
          if (base.protocol !== 'https:' || typeof data.token !== 'string' || !data.token) throw new Error();
          if (!base.pathname.endsWith('/')) base.pathname += '/';
          const app = new URL('photoswitchlab/', base);
          app.searchParams.set('token', data.token);
          stop();
          window.location.assign(app.href);
        } catch (_) {
          fail('Die Adresse Ihrer Sitzung konnte nicht geöffnet werden. Öffnen Sie die Binder-Startseite.');
        }
      }
    };
    // Close on interruption: an automatic reconnect could start a second session.
    connection.onerror = () => {
      if (stream === connection) fail('Die Verbindung zu Binder wurde unterbrochen. Öffnen Sie die Binder-Startseite oder versuchen Sie den Start erneut.');
    };
  }

  start.addEventListener('click', event => { event.preventDefault(); run(); });
  retry.addEventListener('click', run);
  const page = new URL(window.location.href);
  if (page.searchParams.get('binder') === '1') {
    page.searchParams.delete('binder');
    window.history.replaceState(null, '', page.href);
    run();
  }
  window.addEventListener('pagehide', stop);
  window.addEventListener('pageshow', event => {
    if (event.persisted) {
      stop();
      start.hidden = false;
      progress.hidden = true;
    }
  });
})();
