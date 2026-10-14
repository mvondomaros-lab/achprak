const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function launchPage(query = '', supported = true) {
  const nodes = {};
  const connections = [];
  const redirects = [];
  const windowEvents = {};
  let history;
  function node(selector) {
    return nodes[selector] = {
      hidden: selector === '.binder-progress' || selector === '[data-binder-retry]',
      textContent: '', dataset: {}, attrs: {}, listeners: {},
      addEventListener(name, callback) { this.listeners[name] = callback; },
      setAttribute(name, value) { this.attrs[name] = value; },
      removeAttribute(name) { delete this.attrs[name]; },
      focus() {},
    };
  }
  for (const selector of ['[data-binder-start]', '.binder-progress', '.binder-status', '.binder-elapsed', '[data-binder-retry]']) node(selector);
  nodes['[data-binder-start]'].href = `https://mybinder.org/v2/gh/mvondomaros-lab/photoswitchlab/${'a'.repeat(40)}?urlpath=photoswitchlab%2F`;
  const stages = Array.from({length: 4}, (_, i) => node(`stage-${i}`));
  const panel = {
    querySelector: selector => nodes[selector],
    querySelectorAll: () => stages,
    scrollIntoView() {},
  };
  class Source {
    constructor(url) { this.url = url; this.closed = false; connections.push(this); }
    close() { this.closed = true; }
    emit(data) { this.onmessage({data: JSON.stringify(data)}); }
  }
  const window = {
    EventSource: supported ? Source : null,
    location: {href: `https://example.org/photoswitchlab/installation/${query}`, assign: url => redirects.push(url)},
    history: {replaceState: (_, __, url) => { history = url; }},
    addEventListener: (event, callback) => { windowEvents[event] = callback; },
  };
  vm.runInNewContext(fs.readFileSync('site/assets/binder-launch.js', 'utf8'), {
    document: {querySelector: () => panel}, window, URL,
    setInterval: () => 1, clearInterval() {}, Date,
  });
  const messages = [];
  let text = nodes['.binder-status'].textContent;
  Object.defineProperty(nodes['.binder-status'], 'textContent', {
    get: () => text,
    set: value => { text = value; messages.push(value); },
  });
  const click = () => nodes['[data-binder-start]'].listeners.click({preventDefault() {}});
  return {nodes, stages, connections, redirects, messages, click, retry: () => nodes['[data-binder-retry]'].listeners.click(), windowEvents, history: () => history};
}

test('cached launch opens the app directly, encodes its token and closes the stream', () => {
  const p = launchPage();
  p.click(); p.click();
  assert.equal(p.connections.length, 1);
  const source = p.connections[0];
  assert.match(source.url, /\/build\/gh\/.+\/a{40}$/);
  source.emit({phase: 'built'});
  source.emit({phase: 'launching'});
  source.emit({phase: 'READY', url: 'https://hub.example.org/user/binder-abc/', token: 'a+b&c'});
  assert.equal(source.closed, true);
  assert.equal(p.redirects[0], 'https://hub.example.org/user/binder-abc/photoswitchlab/?token=a%2Bb%26c');
  assert.equal(p.stages[3].attrs['aria-current'], 'step');
  assert.ok(Object.values(p.nodes).every(node => !node.textContent.includes('a+b&c')));
});

test('build failure allows one explicit retry and ignores late events from the old stream', () => {
  const p = launchPage(); p.click();
  const old = p.connections[0];
  for (const phase of ['waiting', 'fetching', 'building', 'building', 'pushing']) old.emit({phase});
  assert.equal(p.messages.filter(message => message.includes('eingerichtet')).length, 1);
  assert.equal(p.stages[1].attrs['aria-current'], 'step');
  old.emit({phase: 'failed', message: '<script>unsafe developer log</script>'});
  assert.equal(old.closed, true);
  assert.equal(p.nodes['[data-binder-retry]'].hidden, false);
  assert.ok(!p.nodes['.binder-status'].textContent.includes('script'));
  p.retry();
  assert.equal(p.connections.length, 2);
  old.emit({phase: 'ready', url: 'https://wrong.example/', token: 'old'});
  assert.equal(p.redirects.length, 0);
  p.windowEvents.pagehide();
  assert.equal(p.connections[1].closed, true);
});

test('connection loss and malformed events close the stream instead of reconnecting', () => {
  const p = launchPage(); p.click();
  p.connections[0].onerror();
  assert.equal(p.connections[0].closed, true);
  assert.equal(p.connections.length, 1);
  assert.match(p.nodes['.binder-status'].textContent, /unterbrochen/);
  p.retry();
  p.connections[1].onmessage({data: 'not JSON'});
  assert.equal(p.connections[1].closed, true);
  assert.equal(p.redirects.length, 0);
});

test('an invalid ready URL or missing token cannot navigate away', () => {
  for (const data of [{url: 'javascript:alert(1)', token: 'x'}, {url: 'https://hub.example.org/user/test/'}]) {
    const p = launchPage(); p.click();
    p.connections[0].emit({phase: 'ready', ...data});
    assert.equal(p.redirects.length, 0);
    assert.equal(p.nodes['[data-binder-retry]'].hidden, false);
  }
});

test('badge auto-launch is consumed once; returning restores a usable start link', () => {
  const p = launchPage('?binder=1#uber-binder-starten');
  assert.equal(p.connections.length, 1);
  assert.equal(p.history(), 'https://example.org/photoswitchlab/installation/#uber-binder-starten');
  p.windowEvents.pagehide();
  p.windowEvents.pageshow({persisted: true});
  assert.equal(p.nodes['[data-binder-start]'].hidden, false);
  assert.equal(p.nodes['.binder-progress'].hidden, true);
  assert.equal(p.connections.length, 1);
});

test('browsers without EventSource use the original Binder launch page', () => {
  const p = launchPage('?binder=1', false);
  assert.equal(p.connections.length, 0);
  assert.equal(p.redirects[0], p.nodes['[data-binder-start]'].href);
});
