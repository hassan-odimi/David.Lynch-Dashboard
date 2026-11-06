const money = (n) => '$' + n.toLocaleString('en-US');
const times = (m) => (m < 10 ? m.toFixed(1) : Math.round(m)) + '×';
// Source titles use straight quotes; show typographic ones.
const pretty = (s) => s.replace(/"([^"]*)"/g, '“$1”').replace(/'/g, '’');
const loadJSON = (path) => fetch(path).then((r) => {
  if (!r.ok) throw new Error(path + ': ' + r.status);
  return r.json();
});

function el(tag, props = {}, ...children) {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
}

function choiceButton(label, onClick) {
  return el('button', { className: 'choice', type: 'button', textContent: label, onclick: onClick });
}

const BANDS = [
  { key: 'under-2500', label: 'Under $2,500', min: 0, max: 2500 },
  { key: '2500-5000', label: '$2,500 to $5,000', min: 2500, max: 5000 },
  { key: '5000-10000', label: '$5,000 to $10,000', min: 5000, max: 10000 },
  { key: '10000-25000', label: '$10,000 to $25,000', min: 10000, max: 25000 },
  { key: 'over-25000', label: 'Over $25,000', min: 25000, max: Infinity },
];
const inBand = (lot, band) => lot.sold >= band.min && lot.sold < band.max;
const collator = new Intl.Collator('en', { ignorePunctuation: true, numeric: true });
const SORTS = {
  price: (a, b) => b.sold - a.sold,
  multiple: (a, b) => b.multiple - a.multiple || b.sold - a.sold,
  low: (a, b) => a.sold - b.sold,
  title: (a, b) => collator.compare(a.title, b.title),
};

function lotCard(lot) {
  const title = pretty(lot.title);
  return el('li', {}, el('a', { className: 'lot', href: '?lot=' + lot.id },
    el('img', { className: 'object', src: `img/thumbs/${lot.id}.webp`, alt: title, loading: 'lazy', width: 400, height: 400 }),
    el('span', { className: 'lot-title', textContent: title }),
    el('span', { className: 'lot-result' },
      el('span', { className: 'price', textContent: money(lot.sold) }),
      el('span', { className: 'lot-multiple', textContent: times(lot.multiple) + ' estimate' }))));
}

async function collection() {
  const summary = document.getElementById('summary');
  let lots;
  try {
    lots = await loadJSON('data/lots.json');
  } catch {
    summary.textContent = 'The lots could not be loaded. Reload the page to try again.';
    return;
  }
  const search = document.getElementById('search');
  const sort = document.getElementById('sort');
  const grid = document.getElementById('lots');
  const empty = document.getElementById('empty');
  const cards = new Map(lots.map((lot) => [lot.id, lotCard(lot)]));

  const counts = {};
  for (const lot of lots) counts[lot.category] = (counts[lot.category] || 0) + 1;
  const categories = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  const state = { q: '', cat: '', price: '', sort: 'price' };

  function readURL() {
    const params = new URLSearchParams(location.search);
    const known = (value, allowed) => (allowed.includes(value) ? value : '');
    state.q = params.get('q') || '';
    state.cat = known(params.get('cat'), categories);
    state.price = known(params.get('price'), BANDS.map((b) => b.key));
    state.sort = known(params.get('sort'), Object.keys(SORTS)) || 'price';
  }

  function writeURL() {
    const params = new URLSearchParams();
    if (state.q) params.set('q', state.q);
    if (state.cat) params.set('cat', state.cat);
    if (state.price) params.set('price', state.price);
    if (state.sort !== 'price') params.set('sort', state.sort);
    const query = params.toString();
    history.replaceState(null, '', query ? '?' + query : location.pathname);
  }

  const filterButtons = [];
  function addFilter(box, key, value, label) {
    const button = choiceButton(label, () => {
      state[key] = value;
      update();
    });
    filterButtons.push({ button, key, value });
    box.append(button);
  }
  const categoryBox = document.getElementById('categories');
  addFilter(categoryBox, 'cat', '', `All (${lots.length})`);
  for (const name of categories) addFilter(categoryBox, 'cat', name, `${name} (${counts[name]})`);
  const bandBox = document.getElementById('bands');
  addFilter(bandBox, 'price', '', 'All prices');
  for (const band of BANDS) {
    addFilter(bandBox, 'price', band.key, `${band.label} (${lots.filter((l) => inBand(l, band)).length})`);
  }

  function render() {
    search.value = state.q;
    sort.value = state.sort;
    for (const { button, key, value } of filterButtons) button.setAttribute('aria-pressed', state[key] === value);

    const words = state.q.toLowerCase().trim();
    const band = BANDS.find((b) => b.key === state.price);
    const shown = lots
      .filter((lot) => (!state.cat || lot.category === state.cat)
        && (!band || inBand(lot, band))
        && (lot.title.toLowerCase().includes(words) || pretty(lot.title).toLowerCase().includes(words)))
      .sort(SORTS[state.sort]);
    grid.replaceChildren(...shown.map((lot) => cards.get(lot.id)));
    grid.hidden = !shown.length;
    empty.hidden = !!shown.length;
    summary.textContent = `${shown.length} of ${lots.length} lots`;
  }

  function update() {
    writeURL();
    render();
  }

  search.addEventListener('input', () => {
    state.q = search.value;
    update();
  });
  sort.addEventListener('change', () => {
    state.sort = sort.value;
    update();
  });
  document.getElementById('controls').addEventListener('submit', (event) => event.preventDefault());
  document.getElementById('reset').addEventListener('click', () => {
    Object.assign(state, { q: '', cat: '', price: '', sort: 'price' });
    update();
  });

  readURL();
  render();
}

if (document.body.dataset.page === 'collection') collection();
