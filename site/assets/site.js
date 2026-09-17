/* Optional enhancements; navigation, disclosures and equations work without JS. */
const root = new URL('../', document.currentScript.src);
if (matchMedia('(max-width: 1150px)').matches) document.querySelector('.outline details').open = false;

const dialog = document.querySelector('#search-dialog');
const input = document.querySelector('#search-input');
const results = document.querySelector('#search-results');
const status = document.querySelector('#search-status');
const searchButton = document.querySelector('#search-toggle');
let entries;
searchButton.hidden = false;
searchButton.addEventListener('click', async () => {
  dialog.showModal(); input.focus();
  if (!entries) {
    status.textContent = 'Suche wird geladen …';
    try {
      const response = await fetch(new URL('assets/search.json', root));
      if (!response.ok) throw new Error(response.status);
      entries = await response.json(); search();
    } catch (_) { status.textContent = 'Die Suche konnte nicht geladen werden. Bitte versuchen Sie es erneut.'; }
  }
});
function search() {
  results.replaceChildren();
  if (!entries) return;
  const terms = input.value.trim().toLocaleLowerCase('de').split(/\s+/).filter(Boolean);
  if (!terms.length) { status.textContent = 'Geben Sie einen Suchbegriff ein.'; return; }
  const matches = entries.filter(entry => terms.every(term => (entry.title + ' ' + entry.text).toLocaleLowerCase('de').includes(term)));
  status.textContent = `${matches.length} Treffer`;
  for (const entry of matches) {
    const item = document.createElement('li');
    const link = document.createElement('a'); link.href = new URL(entry.url, root); link.textContent = entry.title;
    link.addEventListener('click', () => dialog.close());
    const snippet = document.createElement('p');
    const start = Math.max(0, entry.text.toLocaleLowerCase('de').indexOf(terms[0]) - 50);
    snippet.textContent = (start ? '… ' : '') + entry.text.slice(start, start + 200) + ' …';
    item.append(link, snippet); results.append(item);
  }
}
input.addEventListener('input', search);
// Open enclosing explanations when following a deep link into a disclosure.
function revealAnchor() {
  let target;
  try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (_) { return; }
  if (!target) return;
  for (let parent = target.parentElement; parent; parent = parent.parentElement) {
    if (parent.tagName === 'DETAILS') parent.open = true;
  }
}
addEventListener('hashchange', revealAnchor); revealAnchor();
