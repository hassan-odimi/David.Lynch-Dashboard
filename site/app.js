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
  const state = { q: '', cat: '', price: '', sort: 'price', lot: '' };
  const byId = new Map(lots.map((lot) => [lot.id, lot]));

  function readURL() {
    const params = new URLSearchParams(location.search);
    const known = (value, allowed) => (allowed.includes(value) ? value : '');
    state.q = params.get('q') || '';
    state.cat = known(params.get('cat'), categories);
    state.price = known(params.get('price'), BANDS.map((b) => b.key));
    state.sort = known(params.get('sort'), Object.keys(SORTS)) || 'price';
    state.lot = byId.has(params.get('lot')) ? params.get('lot') : '';
  }

  function writeURL(method = 'replaceState') {
    const params = new URLSearchParams();
    if (state.q) params.set('q', state.q);
    if (state.cat) params.set('cat', state.cat);
    if (state.price) params.set('price', state.price);
    if (state.sort !== 'price') params.set('sort', state.sort);
    if (state.lot) params.set('lot', state.lot);
    const query = params.toString();
    history[method](null, '', query ? '?' + query : location.pathname);
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

  let shownKey;
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
    // Keep the same nodes when the list is unchanged, so focus returns to the card after the dialog.
    const key = shown.map((lot) => lot.id).join();
    if (key !== shownKey) grid.replaceChildren(...shown.map((lot) => cards.get(lot.id)));
    shownKey = key;
    grid.hidden = !shown.length;
    empty.hidden = !!shown.length;
    summary.textContent = `${shown.length} of ${lots.length} lots`;
  }

  function update() {
    writeURL();
    render();
  }

  const dialog = document.getElementById('lot-dialog');
  const part = (name) => document.getElementById('lot-dialog-' + name);
  function syncDialog() {
    const lot = byId.get(state.lot);
    if (!lot) {
      if (dialog.open) dialog.close();
      return;
    }
    part('image').src = `img/lots/${lot.id}.webp`;
    part('image').alt = pretty(lot.title);
    part('category').textContent = lot.category;
    part('title').textContent = pretty(lot.title);
    part('estimate').textContent = estimate(lot);
    part('sold').textContent = money(lot.sold);
    part('multiple').textContent = times(lot.multiple);
    part('source').href = lot.url;
    if (!dialog.open) dialog.showModal();
  }

  // Opening adds a history entry, so the back button closes the dialog.
  let pushed = false;
  grid.addEventListener('click', (event) => {
    const link = event.target.closest('a.lot');
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey) return;
    event.preventDefault();
    state.lot = new URLSearchParams(link.search).get('lot');
    writeURL('pushState');
    pushed = true;
    syncDialog();
  });
  dialog.addEventListener('close', () => {
    if (!state.lot) return;
    state.lot = '';
    if (pushed) history.back();
    else writeURL();
  });
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
  part('close').addEventListener('click', () => dialog.close());
  addEventListener('popstate', () => {
    pushed = false;
    readURL();
    render();
    syncDialog();
  });

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
    Object.assign(state, { q: '', cat: '', price: '', sort: 'price', lot: '' });
    update();
  });

  readURL();
  render();
  syncDialog();
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
    const attrs = { x1: X(m0), y1: Y(m0 * factor), x2: X(m1), y2: Y(m1 * factor), stroke: 'currentColor', 'stroke-width': 1, 'stroke-dasharray': '5 5', 'vector-effect': 'non-scaling-stroke' };
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
  const below = lots.find((lot) => lot.sold < lot.low);
  const note = el('span', { className: 'guide-note', textContent: 'Below estimate' });
  note.style.left = X((below.low + below.high) / 2) + '%';
  note.style.top = Y(below.sold) + '%';
  guides.append(note);
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
    const tile = el('button', {
      className: lot === below ? 'tile below' : 'tile',
      type: 'button',
      tabIndex: -1,
      onclick: () => pick(lot, tile),
      onpointerenter: (event) => event.pointerType === 'mouse' && pick(lot, tile),
    });
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
    plot.classList.toggle('charted', chart);
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
  // Set after the first pick, so the default lot is not announced on load.
  detail.parentElement.setAttribute('aria-live', 'polite');
}

const ROUNDS = [
  { id: '01', alt: 'Speckled white mug with a gold handle and a painting of the Log Lady', note: '78 times its estimate.' },
  { id: '416', alt: 'EcoloBlue atmospheric water generator', note: 'The lowest price in the sale.' },
  { id: '228', alt: 'Large round dreamcatcher made of pale cord and wood', note: '260 times its estimate.' },
  { id: '129', alt: 'Long grey-green sofa with a curved back, on metal legs', note: 'The only lot of 441 to sell below its estimate.' },
  { id: '290', alt: 'Carved terracotta incense holder in the shape of a small building', note: '130 times its estimate.' },
];
const BID_MIN = 50;
const BID_MAX = 300000;
const BID_STEPS = 400;
const MAX_POINTS = 100;
const calm = matchMedia('(prefers-reduced-motion: reduce)');
const bidShare = (price) => Math.log(price / BID_MIN) / Math.log(BID_MAX / BID_MIN);
const bidPlace = (price) => `calc(10px + (100% - 20px) * ${bidShare(price)})`; // 20px is the slider thumb
// Two significant figures: $4,300, not $4,287.
function roundPrice(value) {
  const unit = 10 ** (Math.floor(Math.log10(value)) - 1);
  return Math.round(value / unit) * unit;
}
const stepToBid = (step) => roundPrice(BID_MIN * (BID_MAX / BID_MIN) ** (step / BID_STEPS));
// Exact is 100 points. Ten times out, either way, is 0.
const bidPoints = (bid, sold) => Math.max(0, Math.round(MAX_POINTS * (1 - Math.abs(Math.log10(bid / sold)))));

function countUp(from, to, ms, frame, done) {
  if (calm.matches) {
    frame(to);
    done();
    return;
  }
  const start = performance.now();
  requestAnimationFrame(function step(now) {
    const t = Math.min(1, (now - start) / ms);
    frame(t === 1 ? to : from * (to / from) ** (1 - (1 - t) ** 3));
    if (t < 1) requestAnimationFrame(step);
    else done();
  });
}

function guess(lots) {
  const $ = (id) => document.getElementById('guess-' + id);
  const byId = new Map(lots.map((lot) => [lot.id, lot]));
  const slider = $('slider');
  const steps = ROUNDS.map(() => el('li'));
  let round = 0;
  let results = [];

  $('steps').append(...steps);
  $('ticks').append(...[100, 1000, 10000, 100000].map((value) => {
    const tick = el('span', { textContent: money(value) });
    tick.style.left = bidPlace(value);
    return tick;
  }));

  const enter = (node, keyframes) => {
    if (!calm.matches) node.animate(keyframes, { duration: 350, easing: 'cubic-bezier(.2,.7,.2,1)' });
  };

  function showBid() {
    const bid = stepToBid(+slider.value);
    $('bid').textContent = money(bid);
    slider.setAttribute('aria-valuetext', money(bid));
  }

  function show() {
    const { id, alt } = ROUNDS[round];
    const lot = byId.get(id);
    $('round').hidden = false;
    $('done').hidden = true;
    $('image').src = `img/lots/${id}.webp`;
    $('image').alt = alt;
    if (ROUNDS[round + 1]) new Image().src = `img/lots/${ROUNDS[round + 1].id}.webp`;
    $('count').textContent = `Lot ${round + 1} of ${ROUNDS.length}`;
    $('title').textContent = pretty(lot.title);
    $('estimate').textContent = 'Estimate ' + estimate(lot);
    steps.forEach((step, i) => step.classList.toggle('reached', i <= round));
    $('band').style.left = bidPlace(lot.low);
    $('band').style.width = `calc((100% - 20px) * ${bidShare(lot.high) - bidShare(lot.low)})`;
    slider.disabled = false;
    slider.value = Math.round(bidShare(lot.high) * BID_STEPS);
    showBid();
    $('place').hidden = false;
    $('marker').hidden = true;
    $('sold').hidden = true;
    $('reveal').textContent = '';
    $('next').hidden = true;
  }

  function next() {
    show();
    enter($('image'), [{ opacity: 0, transform: 'translateX(32px)' }, { opacity: 1, transform: 'none' }]);
    enter($('copy'), [{ opacity: 0 }, { opacity: 1 }]);
    slider.focus({ preventScroll: true });
  }

  function placeBid() {
    const { id, note } = ROUNDS[round];
    const lot = byId.get(id);
    const bid = stepToBid(+slider.value);
    const points = bidPoints(bid, lot.sold);
    results.push({ id, lot, bid, points });
    slider.disabled = true;
    $('place').hidden = true;
    $('marker').hidden = false;
    $('sold').hidden = false;
    countUp((lot.low + lot.high) / 2, lot.sold, 1100, (price) => {
      $('sold').textContent = money(price === lot.sold ? price : roundPrice(price));
      $('marker').style.left = bidPlace(price);
    }, () => {
      const off = Math.max(bid, lot.sold) / Math.min(bid, lot.sold);
      const verdict = off <= 1.1 ? 'within 10%' : `${times(off)} too ${bid < lot.sold ? 'low' : 'high'}`;
      $('reveal').textContent = `Sold for ${money(lot.sold)}. You bid ${money(bid)}, ${verdict}: ${points} points. ${note}`;
      $('next').textContent = round === ROUNDS.length - 1 ? 'See your results' : 'Next lot';
      $('next').hidden = false;
      $('next').focus({ preventScroll: true });
    });
  }

  function finish() {
    const total = results.reduce((sum, result) => sum + result.points, 0);
    const out = `of ${ROUNDS.length * MAX_POINTS}`;
    $('round').hidden = true;
    $('done').hidden = false;
    $('shared').textContent = '';
    const rows = results.map(({ id, lot, bid, points }) => el('tr', {},
      el('td', {}, el('a', { className: 'sheet-lot', href: lotHref(lot) },
        el('img', { className: 'object', src: `img/thumbs/${id}.webp`, alt: '' }),
        el('span', { textContent: pretty(lot.title) }))),
      el('td', { textContent: money(bid) }),
      el('td', { className: 'price', textContent: money(lot.sold) }),
      el('td', { textContent: points })));
    $('sheet').tBodies[0].replaceChildren(...rows);
    if (!calm.matches) {
      rows.forEach((row, i) => row.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, delay: i * 90, fill: 'backwards' }));
    }
    countUp(1, total, 900, (value) => {
      $('score').textContent = `${Math.round(value)} ${out}`;
    }, () => {});
    $('again').focus({ preventScroll: true });
  }

  $('place').addEventListener('click', placeBid);
  slider.addEventListener('input', showBid);
  $('next').addEventListener('click', () => {
    if (round === ROUNDS.length - 1) {
      finish();
      return;
    }
    round += 1;
    next();
  });

  $('again').addEventListener('click', () => {
    round = 0;
    results = [];
    next();
  });

  $('share').addEventListener('click', async () => {
    const total = results.reduce((sum, result) => sum + result.points, 0);
    const worst = results.reduce((a, b) => (b.points < a.points ? b : a));
    const text = `I scored ${total} of ${ROUNDS.length * MAX_POINTS} bidding on David Lynch’s belongings. The one that got away: ${pretty(worst.lot.title)}, ${money(worst.lot.sold)}.`;
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

function median(values) {
  const sorted = [...values].sort((a, b) => a - b);
  const half = sorted.length >> 1;
  return sorted.length % 2 ? sorted[half] : (sorted[half - 1] + sorted[half]) / 2;
}

function barRows(id, rows) {
  const table = document.getElementById(id);
  const largest = Math.max(...rows.map((row) => row.size));
  table.tBodies[0].append(...rows.map((row, i) => {
    const bar = el('span', { className: 'bar' });
    bar.style.setProperty('--size', row.size / largest * 100 + '%');
    bar.style.setProperty('--order', i);
    return el('tr', {},
      el('th', { scope: 'row' }, row.href ? el('a', { href: row.href, textContent: row.label }) : row.label),
      el('td', { textContent: row.lots }),
      el('td', { className: 'bar-cell' }, el('span', { className: 'price', textContent: row.value }), bar),
      ...(row.extra ? [el('td', { textContent: row.extra })] : []));
  }));
  new IntersectionObserver(([entry], observer) => {
    if (!entry.isIntersecting) return;
    table.classList.add('shown');
    observer.disconnect();
  }, { threshold: 0.2 }).observe(table);
}

const ESTIMATE_BANDS = [
  [0, 300, 'Under $300'],
  [300, 600, '$300 to $599'],
  [600, 1000, '$600 to $999'],
  [1000, 2000, '$1,000 to $1,999'],
  [2000, 5000, '$2,000 to $4,999'],
  [5000, Infinity, '$5,000 and over'],
];

function findings(lots) {
  const groups = new Map();
  for (const lot of lots) groups.set(lot.category, [...(groups.get(lot.category) || []), lot]);
  const total = (group) => group.reduce((sum, lot) => sum + lot.sold, 0);
  barRows('category-bars', [...groups]
    .sort(([, a], [, b]) => total(b) - total(a))
    .map(([name, group]) => ({
      label: name,
      href: 'collection.html?cat=' + encodeURIComponent(name),
      lots: group.length,
      size: total(group),
      value: money(total(group)),
      extra: times(median(group.map((lot) => lot.multiple))),
    })));
  barRows('estimate-bars', ESTIMATE_BANDS.map(([min, max, label]) => {
    const group = lots.filter((lot) => (lot.low + lot.high) / 2 >= min && (lot.low + lot.high) / 2 < max);
    const multiple = median(group.map((lot) => lot.multiple));
    return { label, lots: group.length, size: multiple, value: times(multiple) };
  }));
}

async function overview() {
  try {
    const lots = await loadJSON('data/lots.json');
    wall(lots);
    findings(lots);
    guess(lots);
  } catch {
    document.getElementById('wall-detail').textContent = 'The lots could not be loaded. Reload the page to try again.';
    document.getElementById('wall-toggle').hidden = true;
    document.getElementById('guess').hidden = true;
    document.getElementById('findings').hidden = true;
  }
}

// Many titles are descriptions, so this searches and does not claim an exact match.
function searchLink(book, title) {
  const author = ['Unknown', 'Various'].includes(book.author) ? '' : book.author;
  const words = /^(work by|collection from)\b/i.test(book.title) ? author : `${book.title} ${author}`;
  const link = el('a', { className: 'book-lot', href: 'https://openlibrary.org/search?q=' + encodeURIComponent(words.trim()), textContent: 'Search Open Library' });
  link.setAttribute('aria-label', `Search Open Library for ${title}`);
  return link;
}

async function library() {
  const summary = document.getElementById('summary');
  let lots;
  try {
    lots = await loadJSON('data/books.json');
  } catch {
    summary.textContent = 'The books could not be loaded. Reload the page to try again.';
    return;
  }
  const search = document.getElementById('search');
  const list = document.getElementById('books');
  const empty = document.getElementById('empty');
  const authorLabel = { Unknown: 'Author unknown', Various: 'Various authors' };
  const books = lots.flatMap((lot) => lot.books.map((book) => {
    const title = pretty(book.title);
    const author = pretty(authorLabel[book.author] || book.author);
    return {
      ...book,
      lot,
      text: `${book.title} ${title} ${book.author} ${author}`.toLowerCase(),
      row: el('li', {},
        el('span', { className: 'book-title', textContent: title }),
        el('span', { className: 'book-author', textContent: author }),
        el('a', { className: 'book-lot', href: 'collection.html?lot=' + lot.lot, textContent: pretty(lot.title) }),
        searchLink(book, title)),
    };
  }));

  const unknown = books.filter((book) => book.author === 'Unknown').length;
  const various = books.filter((book) => book.author === 'Various').length;
  document.getElementById('library-intro').textContent = `${books.length} books in ${lots.length} lots. `
    + `${unknown + various} have no named author: ${unknown} are listed as unknown and ${various} as various. `
    + 'Search links go to Open Library, an independent catalogue, and may not find the exact edition.';

  const counts = {};
  for (const book of books) counts[book.lot.category] = (counts[book.lot.category] || 0) + 1;
  const categories = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  const params = new URLSearchParams(location.search);
  const state = { q: params.get('q') || '', cat: categories.includes(params.get('cat')) ? params.get('cat') : '' };

  const buttons = [['', `All (${books.length})`], ...categories.map((name) => [name, `${name} (${counts[name]})`])]
    .map(([value, label]) => ({
      value,
      button: choiceButton(label, () => {
        state.cat = value;
        render();
      }),
    }));
  document.getElementById('categories').append(...buttons.map((b) => b.button));

  function render() {
    search.value = state.q;
    for (const { button, value } of buttons) button.setAttribute('aria-pressed', state.cat === value);
    const words = state.q.toLowerCase().trim();
    const shown = books.filter((book) => (!state.cat || book.lot.category === state.cat)
      && book.text.includes(words));
    list.replaceChildren(...shown.map((book) => book.row));
    list.hidden = !shown.length;
    empty.hidden = !!shown.length;
    summary.textContent = `${shown.length} of ${books.length} books`;
    const query = new URLSearchParams(Object.entries(state).filter(([, value]) => value)).toString();
    history.replaceState(null, '', query ? '?' + query : location.pathname);
  }

  search.addEventListener('input', () => {
    state.q = search.value;
    render();
  });
  document.getElementById('controls').addEventListener('submit', (event) => event.preventDefault());
  document.getElementById('reset').addEventListener('click', () => {
    Object.assign(state, { q: '', cat: '' });
    render();
  });
  render();
}

const pages = { overview, collection, library };
pages[document.body.dataset.page]?.();
