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

const estimate = (lot) => `${money(lot.low)} to ${money(lot.high)}`;
const lotHref = (lot) => 'collection.html?lot=' + lot.id;

function wall(lots) {
  const plot = document.getElementById('plot');
  const help = document.getElementById('wall-help');
  const toggle = document.getElementById('wall-toggle');
  const detail = document.getElementById('wall-detail');
  const link = document.getElementById('wall-link');
  const narrow = matchMedia('(max-width: 699px)');
  let chart = false;

  // Both scales are logarithmic. Positions are percentages of the plot.
  const scale = (v, min, max) => (Math.log10(v) - Math.log10(min)) / (Math.log10(max) - Math.log10(min));
  const X = (v) => 7 + scale(v, 50, 20000) * 90;
  const Y = (v) => 92 - scale(v, 500, 300000) * 88;
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

  const guides = el('div', { className: 'guides', hidden: true });
  guides.setAttribute('aria-hidden', 'true');
  const svgNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(svgNS, 'svg');
  svg.setAttribute('viewBox', '0 0 100 100');
  svg.setAttribute('preserveAspectRatio', 'none');
  guides.append(svg);
  for (const [factor, label] of [[1, 'Sold at estimate'], [10, '10×'], [100, '100×']]) {
    const m0 = Math.max(50, 500 / factor);
    const m1 = Math.min(20000, 300000 / factor);
    const line = document.createElementNS(svgNS, 'line');
    const attrs = { x1: X(m0), y1: Y(m0 * factor), x2: X(m1), y2: Y(m1 * factor), stroke: '#5E564C', 'stroke-width': 1, 'stroke-dasharray': '5 5', 'vector-effect': 'non-scaling-stroke' };
    for (const [name, value] of Object.entries(attrs)) line.setAttribute(name, value);
    svg.append(line);
    const text = el('span', { className: 'guide-label', textContent: label });
    text.style.left = X(m1) + '%';
    text.style.top = Y(m1 * factor) + '%';
    guides.append(text);
  }
  for (const value of [100, 1000, 10000]) {
    const tick = el('span', { className: 'tick-x', textContent: money(value) });
    tick.style.left = X(value) + '%';
    guides.append(tick);
  }
  for (const value of [1000, 10000, 100000]) {
    const tick = el('span', { className: 'tick-y', textContent: money(value) });
    tick.style.top = Y(value) + '%';
    guides.append(tick);
  }
  plot.append(guides);

  let picked;
  function pick(lot, tile) {
    picked?.classList.remove('picked');
    picked = tile;
    tile.classList.add('picked');
    detail.textContent = `${pretty(lot.title)}. Estimate ${estimate(lot)}. Sold for ${money(lot.sold)}. ${times(lot.multiple)} estimate.`;
    link.href = lotHref(lot);
    link.hidden = false;
  }

  const tiles = lots.map((lot) => {
    const tile = el('button', { className: 'tile', type: 'button', tabIndex: -1, onclick: () => pick(lot, tile) });
    tile.setAttribute('aria-label', pretty(lot.title));
    const column = lot.sheet % 21;
    const row = Math.floor(lot.sheet / 21);
    tile.style.backgroundPosition = `${column * 5}% ${row * 5}%`;
    plot.append(tile);
    return tile;
  });

  function layout() {
    const columns = narrow.matches ? 21 : 32;
    const rows = narrow.matches ? 21 : 14;
    lots.forEach((lot, i) => {
      const { style } = tiles[i];
      const jitter = (((i * 37) % 9) - 4) * 0.14;
      style.left = (chart ? clamp(X((lot.low + lot.high) / 2) + jitter, 5, 97) : (i % columns) * (100 / columns)) + '%';
      style.top = (chart ? clamp(Y(lot.sold), 1, 92) : Math.floor(i / columns) * (100 / rows)) + '%';
      style.width = (chart ? (narrow.matches ? 2.6 : 1.5) : 100 / columns) + '%';
      style.height = (chart ? (narrow.matches ? 2.6 : 3.43) : 100 / rows) + '%';
      style.transitionDelay = (i % columns) * 8 + 'ms';
    });
    guides.hidden = !chart;
    toggle.textContent = chart ? 'Back to the wall' : 'Turn the wall into a chart';
    help.textContent = chart
      ? 'Across: estimate midpoint. Up: sold price. Both scales are logarithmic.'
      : 'Most expensive first. Select any object.';
  }

  toggle.addEventListener('click', () => {
    chart = !chart;
    layout();
  });
  narrow.addEventListener('change', layout);
  layout();
  pick(lots[0], tiles[0]);
}

const ROUNDS = [
  { id: '01', alt: 'Speckled white mug with a gold handle and a painting of the Log Lady', note: '78 times its estimate.' },
  { id: '416', alt: 'EcoloBlue atmospheric water generator', note: 'The lowest price in the sale.' },
  { id: '228', alt: 'Large round dreamcatcher made of pale cord and wood', note: '260 times its estimate.' },
  { id: '129', alt: 'Long grey-green sofa with a curved back, on metal legs', note: 'The only lot of 441 to sell below its estimate.' },
  { id: '290', alt: 'Carved terracotta incense holder in the shape of a small building', note: '130 times its estimate.' },
];
const GUESS_BANDS = [[1000, '$1,000 or less'], [10000, '$1,001 to $10,000'], [50000, '$10,001 to $50,000'], [Infinity, 'Over $50,000']];

function guess(lots) {
  const $ = (id) => document.getElementById('guess-' + id);
  const byId = new Map(lots.map((lot) => [lot.id, lot]));
  let round = 0;
  let score = 0;
  let answered = false;

  const buttons = GUESS_BANDS.map(([, label], i) => choiceButton(label, () => answer(i)));
  $('bands').append(...buttons);

  function show() {
    const { id, alt } = ROUNDS[round];
    const lot = byId.get(id);
    answered = false;
    $('round').hidden = false;
    $('done').hidden = true;
    $('image').src = `img/lots/${id}.webp`;
    $('image').alt = alt;
    $('count').textContent = `Lot ${round + 1} of ${ROUNDS.length}`;
    $('title').textContent = pretty(lot.title);
    $('estimate').textContent = 'Estimate ' + estimate(lot);
    $('reveal').textContent = '';
    $('next').hidden = true;
    for (const button of buttons) button.classList.remove('right');
  }

  function answer(choice) {
    if (answered) return;
    answered = true;
    const lot = byId.get(ROUNDS[round].id);
    const right = GUESS_BANDS.findIndex(([max]) => lot.sold <= max);
    if (choice === right) score += 1;
    buttons[right].classList.add('right');
    $('reveal').textContent = `${choice === right ? 'Correct.' : 'Not quite.'} Sold for ${money(lot.sold)}. ${ROUNDS[round].note}`;
    $('next').textContent = round === ROUNDS.length - 1 ? 'See your score' : 'Next lot';
    $('next').hidden = false;
    $('next').focus({ preventScroll: true });
  }

  $('next').addEventListener('click', () => {
    if (round === ROUNDS.length - 1) {
      $('round').hidden = true;
      $('done').hidden = false;
      $('score').textContent = `${score} of ${ROUNDS.length}`;
      $('shared').textContent = '';
      $('again').focus({ preventScroll: true });
      return;
    }
    round += 1;
    show();
    buttons[0].focus({ preventScroll: true });
  });

  $('again').addEventListener('click', () => {
    round = 0;
    score = 0;
    show();
    buttons[0].focus({ preventScroll: true });
  });

  $('share').addEventListener('click', async () => {
    const text = `I scored ${score} of ${ROUNDS.length} guessing what David Lynch’s belongings sold for.`;
    const url = location.origin + location.pathname + '#guess';
    try {
      if (navigator.share) {
        await navigator.share({ text, url });
      } else {
        await navigator.clipboard.writeText(`${text} ${url}`);
        $('shared').textContent = 'Copied to the clipboard.';
      }
    } catch (error) {
      if (error.name !== 'AbortError') $('shared').textContent = 'Sharing did not work here. Copy the page address instead.';
    }
  });

  show();
}

async function overview() {
  try {
    const lots = await loadJSON('data/lots.json');
    wall(lots);
    guess(lots);
  } catch {
    document.getElementById('wall-detail').textContent = 'The lots could not be loaded. Reload the page to try again.';
  }
}

const pages = { overview, collection };
pages[document.body.dataset.page]?.();
