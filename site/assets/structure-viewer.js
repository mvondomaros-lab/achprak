/* Progressive 3D structure viewer for the structures chapter. */
(() => {
  const assetRoot = new URL('../', document.currentScript.src);
  const nglUrl = new URL('assets/vendor/ngl.js', assetRoot);
  const structureUrl = new URL('assets/structures/azobenzene-trans.sdf', assetRoot);
  let nglPromise;

  function loadNgl() {
    if (globalThis.NGL) return Promise.resolve(globalThis.NGL);
    if (nglPromise) return nglPromise;
    nglPromise = new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = nglUrl;
      script.onload = () => globalThis.NGL ? resolve(globalThis.NGL) : reject(new Error('NGL fehlt'));
      script.onerror = () => reject(new Error('NGL konnte nicht geladen werden'));
      document.head.append(script);
    });
    return nglPromise;
  }

  function showFallback(viewer, error) {
    viewer.dataset.viewerState = 'failed';
    const status = viewer.querySelector('[data-viewer-status]');
    status.textContent = 'Das interaktive 3D-Modell ist nicht verfügbar. Die statische Darstellung bleibt sichtbar.';
    console.error(error);
  }

  async function initialize(viewer) {
    if (viewer.dataset.viewerState) return;
    viewer.dataset.viewerState = 'loading';
    const status = viewer.querySelector('[data-viewer-status]');
    const figure = viewer.closest('figure');
    try {
      const NGL = await loadNgl();
      const stage = new NGL.Stage(viewer, {
        backgroundColor: '#fafcff',
        quality: 'medium',
        clipDist: 0.1,
        fogNear: 100,
        fogFar: 200,
      });
      const resizeObserver = new ResizeObserver(() => stage.handleResize());
      resizeObserver.observe(viewer);
      const component = await stage.loadFile(structureUrl.href, {ext: 'sdf'});
      component.addRepresentation('ball+stick', {
        aspectRatio: 1.8,
        bondScale: 0.35,
        multipleBond: 'symmetric',
      });
      component.autoView(0);
      stage.handleResize();
      requestAnimationFrame(() => {
        stage.handleResize();
        component.autoView(0);
      });
      figure.querySelector('[data-viewer-fallback]').hidden = true;
      figure.querySelector('[data-viewer-instruction]').hidden = false;
      status.hidden = true;
      viewer.dataset.viewerState = 'ready';
      viewer._nglStage = stage;
      viewer._nglResizeObserver = resizeObserver;
    } catch (error) {
      showFallback(viewer, error);
    }
  }

  for (const viewer of document.querySelectorAll('[data-ngl-viewer]')) {
    const disclosure = viewer.closest('details');
    const initializeWhenOpen = () => {
      if (!disclosure || disclosure.open) initialize(viewer);
    };
    disclosure?.addEventListener('toggle', initializeWhenOpen);
    initializeWhenOpen();
  }
})();
