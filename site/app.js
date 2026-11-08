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

function fillLotDialog(lot) {
  const part = (name) => document.getElementById('lot-dialog-' + name);
  part('image').src = `img/lots/${lot.id}.webp`;
  part('image').alt = pretty(lot.title);
  part('category').textContent = lot.category;
  part('title').textContent = pretty(lot.title);
  part('estimate').textContent = estimate(lot);
  part('sold').textContent = money(lot.sold);
  part('multiple').textContent = times(lot.multiple);
  part('source').href = lot.url;
}

// The story hands its lots over, so the cards exist before the first paint and objects can land on them.
function handedLots() {
  try {
    const lots = JSON.parse(sessionStorage.getItem('lynch-lots'));
    sessionStorage.removeItem('lynch-lots');
    return lots;
  } catch {
    return null;
  }
}

async function collection() {
  const summary = document.getElementById('summary');
  let lots;
  try {
    lots = handedLots() || await loadJSON('data/lots.json');
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
    fillLotDialog(lot);
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

function wall(lots, openLot) {
  const plot = document.getElementById('plot');
  const help = document.getElementById('wall-help');
  const views = [...document.querySelectorAll('#wall-views [data-view]')];
  const detail = document.getElementById('wall-detail');
  const link = document.getElementById('wall-link');
  const narrow = matchMedia('(max-width: 699px)');
  let view = 'wall';
  let rank, colour, portrait;
  const melt = document.getElementById('colour-melt');
  const veil = el('div', { className: 'portrait-veil' });
  veil.setAttribute('aria-hidden', 'true');

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
      onclick: () => {
        if (tile === picked) openLot(lot);
        else pick(lot, tile);
      },
      onpointerenter: (event) => event.pointerType === 'mouse' && pick(lot, tile),
    });
    tile.setAttribute('aria-label', pretty(lot.title));
    tile.dataset.lot = lot.id;
    tile.dataset.peek = lot.id;
    const column = lot.sheet % 21;
    const row = Math.floor(lot.sheet / 21);
    tile.style.backgroundPosition = `${column * 5}% ${row * 5}%`;
    tile.append(el('i', { className: 'swatch' }));
    plot.append(tile);
    return tile;
  });

  function layout() {
    const columns = narrow.matches ? 21 : 32;
    const rows = narrow.matches ? 21 : 14;
    const chart = view === 'chart';
    // The portrait is square, so its tiles keep the plot's height and centre across.
    const across = view === 'portrait' ? (100 / 21) * (plot.clientHeight / plot.clientWidth) : 100 / columns;
    const inset = view === 'portrait' ? (100 - across * 21) / 2 : 0;
    const wave = view === 'colour' || view === 'portrait';
    lots.forEach((lot, i) => {
      const { style } = tiles[i];
      const jitter = (((i * 37) % 9) - 4) * 0.14;
      // By colour runs down the columns, so the spectrum reads from left to right.
      const place = view === 'colour' ? [Math.floor(rank[i] / rows), rank[i] % rows]
        : view === 'portrait' ? [portrait[i] % 21, Math.floor(portrait[i] / 21)]
        : [i % columns, Math.floor(i / columns)];
      style.left = (chart ? clamp(X((lot.low + lot.high) / 2) + jitter, 5, 97) : inset + place[0] * across) + '%';
      style.top = (chart ? clamp(Y(lot.sold), 1, 92) : place[1] * (100 / (view === 'portrait' ? 21 : rows))) + '%';
      style.width = (chart ? (narrow.matches ? 2.6 : 1.5) : across) + '%';
      style.height = (chart ? (narrow.matches ? 2.6 : 3.43) : 100 / (view === 'portrait' ? 21 : rows)) + '%';
      // Colour and portrait arrive as a wave from the left, by where each tile lands.
      style.transitionDelay = (wave ? place[0] * 34 + place[1] * 8 : (i % columns) * 8) + 'ms';
      if (colour) tiles[i].firstChild.style.transitionDelay = place[0] * 30 + place[1] * 6 + 'ms';
    });
    guides.hidden = !chart;
    plot.classList.toggle('charted', chart);
    plot.classList.toggle('portrait', view === 'portrait');
    if (view === 'portrait') {
      veil.style.left = inset + '%';
      veil.style.width = across * 21 + '%';
    }
    melt.classList.toggle('off', view !== 'colour');
    melt.disabled = view !== 'colour';
    if (view !== 'colour') setMelt(false);
    for (const button of views) button.setAttribute('aria-pressed', button.dataset.view === view);
    help.textContent = {
      wall: 'Most expensive first. Hover or tap an object to read it, then select it to open it.',
      chart: 'Across: estimate midpoint. Up: sold price. Both scales are logarithmic.',
      colour: 'Sorted by each object’s main colour, with the plainest objects last.',
      portrait: 'The 441 lots, darkest to lightest, laid out as a portrait of David Lynch. Hover over it to see the objects more clearly.',
    }[view];
  }

  function setMelt(on) {
    melt.setAttribute('aria-pressed', on);
    melt.textContent = on ? 'Show the objects' : 'Melt into colour';
    plot.classList.toggle('melted', on);
  }
  melt.addEventListener('click', () => setMelt(melt.getAttribute('aria-pressed') !== 'true'));

  let moved = false;
  for (const button of views) {
    button.addEventListener('click', async () => {
      moved = true;
      if (button.dataset.view === 'colour' && !rank) {
        ({ rank, colour } = await colourRank(lots));
        tiles.forEach((tile, i) => { tile.firstChild.style.background = colour[i]; });
      }
      if (button.dataset.view === 'portrait' && !portrait) {
        portrait = await portraitRank(lots);
        const { width, height, crop: [x, y, side] } = PORTRAIT;
        veil.style.backgroundSize = `${(width / side) * 100}% auto`;
        veil.style.backgroundPosition = `${(x / (width - side)) * 100}% ${(y / (height - side)) * 100}%`;
        plot.append(veil);
      }
      view = button.dataset.view;
      layout();
    });
  }
  narrow.addEventListener('change', layout);
  addEventListener('resize', () => { if (view === 'portrait') layout(); });
  layout();
  pick(lots[0], tiles[0]);
  // Set after the first pick, so the default lot is not announced on load.
  detail.parentElement.setAttribute('aria-live', 'polite');
  return new Map(lots.map((lot, i) => [lot.id, tiles[i]]));
}

// Reads the wall's own contact sheet, so colours need no extra data file.
async function colourRank(lots) {
  const image = new Image();
  image.src = 'img/wall.webp';
  await image.decode();
  const cell = 16;
  const canvas = el('canvas', { width: 21 * cell, height: 21 * cell });
  const context = canvas.getContext('2d', { willReadFrequently: true });
  context.drawImage(image, 0, 0, canvas.width, canvas.height);
  const colour = [];
  const keys = lots.map((lot, index) => {
    const { data } = context.getImageData((lot.sheet % 21) * cell, Math.floor(lot.sheet / 21) * cell, cell, cell);
    const hues = new Array(24).fill(0);
    const mix = hues.map(() => [0, 0, 0]);
    let light = 0, count = 0, sum = [0, 0, 0];
    for (let i = 0; i < data.length; i += 4) {
      const [r, g, b] = [data[i], data[i + 1], data[i + 2]];
      const top = Math.max(r, g, b);
      const chroma = top - Math.min(r, g, b);
      if (Math.min(r, g, b) > 235) continue; // The white photo background.
      count += 1;
      light += top;
      sum = [sum[0] + r, sum[1] + g, sum[2] + b];
      if (chroma < 30) continue;
      const hue = (top === r ? (g - b) / chroma : top === g ? 2 + (b - r) / chroma : 4 + (r - g) / chroma) / 6;
      const bin = Math.floor((hue + 1) % 1 * 24);
      hues[bin] += chroma;
      mix[bin] = [mix[bin][0] + r * chroma, mix[bin][1] + g * chroma, mix[bin][2] + b * chroma];
    }
    const strongest = Math.max(...hues);
    const hue = hues.indexOf(strongest);
    const plain = strongest / (count || 1) < 12;
    const [r, g, b] = plain || !strongest ? sum.map((v) => v / (count || 1)) : mix[hue].map((v) => v / strongest);
    colour[index] = count ? `rgb(${r | 0},${g | 0},${b | 0})` : '#FFFFFF';
    return { index, plain, light: light / (count || 1), hue };
  });
  keys.sort((a, b) => a.plain - b.plain || (a.plain ? b.light - a.light : a.hue - b.hue));
  const rank = [];
  keys.forEach((key, place) => { rank[key.index] = place; });
  return { rank, colour };
}

// Places each lot, darkest to lightest, on the matching cell of a 21 by 21 portrait.
const PORTRAIT = { src: 'img/portrait-2016.webp', width: 1200, height: 1685, crop: [120, 160, 980] }; // crop is a square on the face: x, y, side.
async function portraitRank(lots) {
  const n = 21;
  const read = async (src, draw) => {
    const image = new Image();
    image.src = src;
    await image.decode();
    const canvas = el('canvas', { width: n * 8, height: n * 8 });
    const context = canvas.getContext('2d', { willReadFrequently: true });
    draw(context, image, canvas.width);
    return context;
  };
  const tone = (d) => {
    let t = 0;
    for (let i = 0; i < d.length; i += 4) t += 0.3 * d[i] + 0.59 * d[i + 1] + 0.11 * d[i + 2];
    return t;
  };
  const [x, y, side] = PORTRAIT.crop;
  const face = await read(PORTRAIT.src, (c, image, w) => c.drawImage(image, x, y, side, side, 0, 0, w, w));
  const sheet = await read('img/wall.webp', (c, image, w) => c.drawImage(image, 0, 0, w, w));
  const cells = Array.from({ length: n * n }, (_, i) => ({ i, t: tone(face.getImageData((i % n) * 8, Math.floor(i / n) * 8, 8, 8).data) }));
  const objects = lots.map((lot, index) => ({ index, t: tone(sheet.getImageData((lot.sheet % n) * 8, Math.floor(lot.sheet / n) * 8, 8, 8).data) }));
  cells.sort((a, b) => a.t - b.t);
  objects.sort((a, b) => a.t - b.t);
  const place = [];
  objects.forEach((object, i) => { place[object.index] = cells[i].i; });
  return place;
}

// Highest first: each bar ends in the object's picture.
function picBars(id, top) {
  document.getElementById(id).replaceChildren(...top.map((lot) => {
    const bar = el('span', { className: 'pic-fill' }, lotTile(lot, 'pic-end'));
    bar.style.width = lot.sold / top[0].sold * 100 + '%';
    return el('div', { className: 'pic-bar' },
      el('a', { href: lotHref(lot), textContent: pretty(lot.title) }),
      el('span', { className: 'pic-track' }, bar),
      el('span', { className: 'price', textContent: money(lot.sold) }));
  }));
}

function lotTile(lot, className) {
  const link = el('a', { className, href: lotHref(lot) }, el('img', { className: 'object', src: `img/thumbs/${lot.id}.webp`, alt: '', loading: 'lazy' }));
  link.dataset.peek = lot.id;
  link.setAttribute('aria-label', `${pretty(lot.title)}. Sold for ${money(lot.sold)}.`);
  return link;
}

// Lots stacked in bands on a log scale, so the chart is made of the objects themselves.
function pictureChart(host, lots, value, { edges, across, marks = [], label }) {
  const bands = edges.length - 1;
  const bandOf = (v) => Math.max(0, Math.min(bands - 1, edges.findIndex((edge, i) => v < edges[i + 1])));
  const place = (v) => {
    if (v >= edges[bands]) return 100;
    const i = bandOf(v);
    return (i + Math.log(v / edges[i]) / Math.log(edges[i + 1] / edges[i])) / bands * 100;
  };
  const columns = Array.from({ length: bands }, () => el('div', { className: 'chart-band' }));
  const inOrder = [...lots].sort((a, b) => value(a) - value(b));
  for (const lot of inOrder) {
    const v = value(lot);
    const i = v >= edges[bands] ? bands - 1 : bandOf(v);
    const tile = lotTile(lot, 'chart-tile');
    tile.style.width = 100 / across + '%';
    columns[i].append(tile);
  }
  const plot = el('div', { className: 'chart-plot' }, ...columns);
  [...marks].sort((a, b) => a.value - b.value).forEach((mark, i) => {
    const line = el('div', { className: i === 0 && marks.length > 1 ? 'chart-mark flip' : 'chart-mark' },
      el('span', { className: mark.strong ? 'price' : '', textContent: mark.text }));
    line.style.left = place(mark.value) + '%';
    plot.append(line);
  });
  const axis = el('div', { className: 'chart-axis' }, ...edges.map((edge) => {
    const tick = el('span', { textContent: label(edge) });
    tick.style.left = place(edge) + '%';
    return tick;
  }));
  axis.setAttribute('aria-hidden', 'true');
  host.append(plot, axis);
}

// Squarified treemap: rows run along the shorter side, so tiles stay close to square.
function squarify(items, box) {
  let { x, y, w, h } = box;
  const scale = w * h / items.reduce((sum, item) => sum + item.size, 0);
  const rest = items.map((item) => ({ ...item, area: item.size * scale })).sort((a, b) => b.area - a.area);
  const worst = (row, side) => {
    const total = row.reduce((sum, item) => sum + item.area, 0);
    return Math.max(...row.map((item) => Math.max(side * side * item.area / (total * total), total * total / (side * side * item.area))));
  };
  const out = [];
  while (rest.length) {
    const side = Math.min(w, h);
    const row = [rest.shift()];
    while (rest.length && worst([...row, rest[0]], side) <= worst(row, side)) row.push(rest.shift());
    const thick = row.reduce((sum, item) => sum + item.area, 0) / side;
    let along = 0;
    for (const item of row) {
      const length = item.area / thick;
      out.push(w >= h ? { ...item, x, y: y + along, w: thick, h: length } : { ...item, x: x + along, y, w: length, h: thick });
      along += length;
    }
    if (w >= h) { x += thick; w -= thick; } else { y += thick; h -= thick; }
  }
  return out;
}

// Each lot's area is what it sold for, grouped into labelled boxes.
function moneyMap(host, groups) {
  const sum = (lots) => lots.reduce((total, lot) => total + lot.sold, 0);
  const all = groups.flatMap((group) => group.lots);
  // Out of the tab order: hundreds of tiles would bury the rest of the page. The lots stay reachable through the Collection.
  const leaves = new Map(all.map((lot) => [lot, Object.assign(lotTile(lot, 'leaf'), { tabIndex: -1 })]));
  host.append(...leaves.values());
  const labels = new Map(groups.filter((group) => group.name).map((group) => [group, el('span', { className: 'map-label' })]));
  host.append(...labels.values());
  const put = (node, x, y, w, h) => Object.assign(node.style, { left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px' });

  function layout() {
    const width = host.clientWidth;
    const height = host.clientHeight;
    if (!width || !height) return;
    const boxes = squarify(groups.map((group) => ({ group, size: sum(group.lots) })), { x: 0, y: 0, w: width, h: height });
    for (const box of boxes) {
      for (const item of squarify(box.group.lots.map((lot) => ({ lot, size: lot.sold })), box)) put(leaves.get(item.lot), item.x, item.y, item.w, item.h);
      const label = labels.get(box.group);
      if (!label) continue;
      Object.assign(label.style, { left: box.x + 'px', top: box.y + 'px', maxWidth: box.w + 'px' });
      // Roomy boxes carry the total too; narrow ones just the name; the smallest none. The category chips name every group.
      label.textContent = box.w >= 160 ? `${box.group.name} ${money(sum(box.group.lots))}` : box.group.name;
      label.hidden = box.w < 64 || box.h < 28;
    }
  }

  new ResizeObserver(layout).observe(host);
}

// A bigger look at any small picture. Touch shows it on the first tap and follows the link on the second.
function lotPeek(byId) {
  const image = el('img', { alt: '' });
  const title = el('p');
  const price = el('p', { className: 'price' });
  const card = el('div', { className: 'peek', hidden: true }, image, title, price);
  card.setAttribute('aria-hidden', 'true');
  document.body.append(card);
  let current;
  let touch = false;

  function move(x, y) {
    const { offsetWidth: w, offsetHeight: h } = card;
    card.style.left = (x + 24 + w < innerWidth ? x + 24 : Math.max(8, x - w - 24)) + 'px';
    card.style.top = Math.max(8, Math.min(y - h / 2, innerHeight - h - 8)) + 'px';
  }
  function show(node, x, y) {
    if (node !== current) {
      const lot = byId.get(node.dataset.peek);
      current = node;
      image.style.backgroundImage = `url(img/thumbs/${lot.id}.webp)`;
      image.src = `img/lots/${lot.id}.webp`;
      title.textContent = node.dataset.caption || pretty(lot.title);
      price.textContent = (node.dataset.caption ? `In lot ${lot.id}, which sold for ` : 'Sold for ') + money(lot.sold);
      card.hidden = false;
    }
    move(x, y);
  }
  function hide() {
    current = undefined;
    card.hidden = true;
  }
  const peekable = (event) => event.target.closest?.('[data-peek]');

  addEventListener('pointerdown', (event) => { touch = event.pointerType !== 'mouse'; }, true);
  document.addEventListener('pointermove', (event) => {
    if (event.pointerType !== 'mouse') return;
    const node = peekable(event);
    if (node) show(node, event.clientX, event.clientY);
    else if (current) hide();
  });
  document.addEventListener('focusin', (event) => {
    const node = peekable(event);
    if (!node?.matches(':focus-visible')) return;
    const box = node.getBoundingClientRect();
    show(node, box.right, box.top + box.height / 2);
  });
  document.addEventListener('focusout', hide);
  addEventListener('scroll', () => { if (touch) hide(); }, { passive: true });
  document.addEventListener('click', (event) => {
    const node = peekable(event);
    if (!touch) {
      hide();
      return;
    }
    if (!node) {
      hide();
    } else if (node !== current) {
      const box = node.getBoundingClientRect();
      show(node, box.right, box.top + box.height / 2);
      // Wall tiles already treat the first tap as a look.
      if (!node.matches('.tile')) {
        event.preventDefault();
        event.stopPropagation();
      }
    } else {
      hide();
    }
  }, true);
}

const BID_MIN = 50;
const BID_MAX = 300000;
const BID_STEPS = 400;
const calm = matchMedia('(prefers-reduced-motion: reduce)');
const bidShare = (price) => Math.log(price / BID_MIN) / Math.log(BID_MAX / BID_MIN);
const bidPlace = (price) => `calc(10px + (100% - 20px) * ${bidShare(price)})`; // 20px is the slider thumb
// Two significant figures: $4,300, not $4,287.
function roundPrice(value) {
  const unit = 10 ** (Math.floor(Math.log10(value)) - 1);
  return Math.round(value / unit) * unit;
}
const stepToBid = (step) => roundPrice(BID_MIN * (BID_MAX / BID_MIN) ** (step / BID_STEPS));

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
      el('th', { scope: 'row' }, row.href ? el('a', { href: row.href }, ...(row.media ? [row.media] : []), el('span', { textContent: row.label })) : row.label),
      el('td', { textContent: row.lots }),
      el('td', { className: 'bar-cell' }, el('span', { className: row.plain ? '' : 'price', textContent: row.value }), bar),
      ...(row.extra ? [el('td', {}, row.extra)] : []));
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

// Many titles are descriptions, so this searches and does not claim an exact match.
function searchLink(book, title) {
  const author = ['Unknown', 'Various'].includes(book.author) ? '' : book.author;
  const words = /^(work by|collection from)\b/i.test(book.title) ? author : `${book.title} ${author}`;
  const link = el('a', { className: 'book-lot ol-link', href: 'https://openlibrary.org/search?q=' + encodeURIComponent(words.trim()), textContent: 'Search Open Library' });
  link.setAttribute('aria-label', `Search Open Library for ${title}`);
  return link;
}

async function library() {
  const summary = document.getElementById('summary');
  let lots;
  try {
    lots = await loadJSON('data/books.json');
    // Lot links open the lot panel here, so the reader keeps their place in the Library.
    loadJSON('data/lots.json').then((all) => lotPanel(new Map(all.map((lot) => [lot.id, lot])))).catch(() => {});
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

  const stacks = lots.map((lot) => {
    const button = el('button', { className: 'stack', type: 'button' },
      el('img', { className: 'object', src: `img/thumbs/${lot.lot}.webp`, alt: '', loading: 'lazy' }),
      el('span', { className: 'stack-subject', textContent: lot.category }),
      el('span', {}, pretty(lot.title) + ' ', el('span', { className: 'stack-count', textContent: `(${lot.books.length})` })));
    button.setAttribute('aria-expanded', 'false');
    button.addEventListener('click', () => openStack(lot, button));
    return { lot, button };
  });
  let opened;

  function closeStack() {
    opened?.panel.remove();
    opened?.button.setAttribute('aria-expanded', 'false');
    opened = undefined;
  }
  function openStack(lot, button) {
    const same = opened?.button === button;
    closeStack();
    if (same) return;
    const panel = el('div', { className: 'stack-open' },
      el('h3', { textContent: pretty(lot.title) }),
      el('ul', { className: 'books' }, ...books.filter((book) => book.lot === lot).map((book) => book.row)),
      el('a', { className: 'link-block', href: 'collection.html?lot=' + lot.lot, textContent: 'Open the lot' }));
    panel.querySelectorAll('h3, li, .link-block').forEach((node, i) => node.style.setProperty('--i', Math.min(i, 24)));
    const grid = button.parentElement;
    // The panel opens under the row that holds the stack.
    [...grid.children].filter((node) => node.offsetTop === button.offsetTop).at(-1).after(panel);
    button.setAttribute('aria-expanded', 'true');
    opened = { panel, button };
    // Bring the opened books into view only when they start below the screen.
    if (panel.getBoundingClientRect().top > innerHeight - 120) panel.scrollIntoView({ block: 'nearest', behavior: calm.matches ? 'auto' : 'smooth' });
  }
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape' || !opened || document.querySelector('dialog[open]')) return;
    const { button } = opened;
    closeStack();
    button.focus();
  });

  const shelf = (title, list, className) => [
    el('h2', { className: 'book-subject', textContent: title }),
    el('div', { className }, ...list.map((stack) => stack.button)),
  ];
  function shelves() {
    const bySubject = categories.filter((name) => !state.cat || name === state.cat)
      .map((name) => [name, stacks.filter((stack) => stack.lot.category === name)]);
    const small = bySubject.filter(([, list]) => list.length === 1 && !state.cat);
    return [
      ...bySubject.filter((entry) => !small.includes(entry)).flatMap(([name, list]) => shelf(name, list, 'stacks')),
      ...(small.length ? shelf('Smaller subjects', small.flatMap(([, list]) => list), 'stacks shared') : []),
    ];
  }

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
    closeStack();
    list.replaceChildren(...(words ? categories.flatMap((name) => {
      const rows = shown.filter((book) => book.lot.category === name).map((book) => book.row);
      return rows.length ? [el('h2', { className: 'book-subject', textContent: `${name} (${rows.length})` }), el('ul', { className: 'books' }, ...rows)] : [];
    }) : shelves()));
    // Restart the settle animation so each new set of results arrives.
    list.classList.remove('settle');
    [...list.children].forEach((node, i) => node.style.setProperty('--i', Math.min(i, 12)));
    void list.offsetWidth;
    list.classList.add('settle');
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

function lotBid(stage, lot, saved, onBid) {
  const chapter = stage.closest('.chapter');
  const after = chapter.querySelector('.after');
  const controls = document.getElementById('bid-controls').content.cloneNode(true);
  const part = (selector) => controls.querySelector(selector);
  const label = part('label');
  const slider = part('input');
  const bidText = part('.bid-value');
  const marker = part('.bid-marker');
  const sold = part('.bid-sold');
  const reveal = part('.bid-reveal');
  const actions = part('.bid-actions');

  stage.querySelector('.lot-estimate').textContent = 'Estimate ' + estimate(lot);
  slider.id = label.htmlFor = 'bid-' + lot.id;
  part('.bid-band').style.left = bidPlace(lot.low);
  part('.bid-band').style.width = `calc((100% - 20px) * ${bidShare(lot.high) - bidShare(lot.low)})`;
  part('.bid-ticks').append(...[100, 1000, 10000, 100000].map((value) => {
    const tick = el('span', { textContent: money(value) });
    tick.style.left = bidPlace(value);
    return tick;
  }));

  const showBid = () => {
    const bid = stepToBid(+slider.value);
    bidText.textContent = money(bid);
    slider.setAttribute('aria-valuetext', money(bid));
  };

  function finish(bid) {
    if (bid) {
      const off = Math.max(bid, lot.sold) / Math.min(bid, lot.sold);
      reveal.textContent = bid >= lot.sold
        ? `Your bid of ${money(bid)} would have taken it, ${times(off)} what the room paid.`
        : `The room outbid you. It paid ${times(off)} your bid of ${money(bid)}.`;
    } else {
      reveal.textContent = `Sold for ${money(lot.sold)}.`;
    }
    after.hidden = false;
  }

  function lock() {
    slider.disabled = true;
    actions.hidden = true;
    marker.hidden = false;
    sold.hidden = false;
  }

  function settle(bid) {
    lock();
    countUp((lot.low + lot.high) / 2, lot.sold, 1600, (price) => {
      sold.textContent = money(price === lot.sold ? price : roundPrice(price));
      marker.style.left = bidPlace(price);
    }, () => {
      finish(bid);
      onBid(bid);
      if (!calm.matches) after.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 500 });
      after.focus({ preventScroll: true });
    });
  }

  slider.value = Math.round(bidShare(lot.high) * BID_STEPS);
  slider.addEventListener('input', showBid);
  part('[data-place]').addEventListener('click', () => settle(stepToBid(+slider.value)));
  part('[data-skip]').addEventListener('click', () => settle(null));
  showBid();
  stage.querySelector('.bid-controls').append(controls);
  if (saved !== undefined) {
    if (saved) slider.value = Math.round(bidShare(saved) * BID_STEPS);
    showBid();
    lock();
    sold.textContent = money(lot.sold);
    marker.style.left = bidPlace(lot.sold);
    finish(saved);
  }
}

function findingCharts(lots) {
  const inCategory = (...names) => lots.filter((lot) => names.includes(lot.category));
  const typical = (list) => median(list.map((lot) => lot.multiple));
  const split = (group, pattern) => [group.filter((lot) => pattern.test(lot.title)), group.filter((lot) => !pattern.test(lot.title))];
  const [handmade, otherBuilt] = split(inCategory('Workshop & Tools', 'Furniture & Rugs', 'Lamps & Lighting'), /homemade|handmade|made by lynch/i);
  const [signed, unsigned] = split(inCategory('Books & Magazines'), /signed|inscribed/i);
  const [guitars] = split(inCategory('Music & Audio'), /guitar|bass/i);
  const mark = (name, group, strong) => ({ value: typical(group), text: `${name} ${Math.round(typical(group))}×`, strong });
  const charts = {
    filmed: [inCategory('Cameras & Film Gear', 'Memorabilia'), 2, 'This chapter', lots, 'The sale'],
    painted: [inCategory('Art & Prints'), 2, 'Art', lots, 'The sale'],
    built: [handmade, 1, 'Homemade', otherBuilt, 'The rest'],
    played: [guitars, 2, 'Guitars', lots, 'The sale'],
    read: [signed, 1, 'Signed', unsigned, 'The rest'],
  };
  document.querySelectorAll('.finding-chart').forEach((node) => {
    const chart = charts[node.dataset.finding];
    if (!chart) {
      moneyMap(node, [{ lots: inCategory('Scripts & Papers') }]);
      return;
    }
    const [group, across, name, others, otherName] = chart;
    pictureChart(node, group, (lot) => lot.multiple, {
      edges: [1, 5, 10, 20, 40, 80, 160],
      across,
      label: (edge) => edge + '×',
      marks: [mark(name, group, true), mark(otherName, others)],
    });
  });
}

const FILMS = [
  { name: 'Eraserhead', year: 1977, match: /eraserhead/i, imdb: 'tt0074486', letterboxd: 'eraserhead', tomatoes: 'm/eraserhead' },
  { name: 'Ronnie Rocket', year: 'Never made', match: /ronnie rocket/i, never: true, wiki: 'https://en.wikipedia.org/wiki/Ronnie_Rocket' },
  { name: 'The Elephant Man', year: 1980, match: /elephant man/i, imdb: 'tt0080678', letterboxd: 'the-elephant-man', tomatoes: 'm/elephant_man' },
  { name: 'Dune', year: 1984, match: /"dune"/i, imdb: 'tt0087182', letterboxd: 'dune', tomatoes: 'm/dune_1984' },
  { name: 'Blue Velvet', year: 1986, match: /blue velvet/i, imdb: 'tt0090756', letterboxd: 'blue-velvet', tomatoes: 'm/blue_velvet' },
  { name: 'Twin Peaks', year: 1990, match: /twin peaks(?!: (fire walk|the return))/i, imdb: 'tt0098936', letterboxd: 'twin-peaks', tomatoes: 'tv/twin_peaks' },
  { name: 'Wild at Heart', year: 1990, match: /wild at heart/i, imdb: 'tt0100935', letterboxd: 'wild-at-heart', tomatoes: 'm/wild_at_heart' },
  { name: 'Twin Peaks: Fire Walk with Me', year: 1992, match: /fire walk with me/i, imdb: 'tt0105665', letterboxd: 'twin-peaks-fire-walk-with-me', tomatoes: 'm/twin-peaks-fire-walk-with-me' },
  { name: 'Lost Highway', year: 1997, match: /lost highway/i, imdb: 'tt0116922', letterboxd: 'lost-highway', tomatoes: 'm/lost_highway' },
  { name: 'The Straight Story', year: 1999, match: /straight story/i, imdb: 'tt0166896', letterboxd: 'the-straight-story', tomatoes: 'm/straight_story' },
  { name: 'Mulholland Drive', year: 2001, match: /mulholland/i, imdb: 'tt0166924', letterboxd: 'mulholland-drive', tomatoes: 'm/mulholland_dr' },
  { name: 'Inland Empire', year: 2006, match: /inland empire/i, imdb: 'tt0460829', letterboxd: 'inland-empire', tomatoes: 'm/inland_empire' },
  { name: 'Twin Peaks: The Return', year: 2017, match: /twin peaks: the return/i, imdb: 'tt4093826', letterboxd: 'twin-peaks-the-return', tomatoes: 'tv/twin_peaks_the_return' },
];

function career(lots) {
  const host = document.getElementById('career');
  const detail = document.getElementById('film-detail');
  const total = (list) => list.reduce((sum, lot) => sum + lot.sold, 0);
  const films = FILMS.map((film) => ({ ...film, lots: lots.filter((lot) => film.match.test(lot.title)) }));
  const tallest = Math.max(...films.map((film) => total(film.lots)));
  const external = (href, text) => el('a', { className: 'link-block', href, textContent: text });
  let chosen;

  function choose(film, button) {
    chosen?.setAttribute('aria-pressed', 'false');
    chosen = button;
    button.setAttribute('aria-pressed', 'true');
    const count = film.lots.length === 1 ? 'One lot' : `${film.lots.length} lots`;
    const links = film.never
      ? [external(film.wiki, 'Wikipedia')]
      : [external('https://www.imdb.com/title/' + film.imdb + '/', 'IMDb'), external(`https://letterboxd.com/film/${film.letterboxd}/`, 'Letterboxd'), external('https://www.rottentomatoes.com/' + film.tomatoes, 'Rotten Tomatoes')];
    detail.replaceChildren(
      el('h4', { textContent: film.never ? `${film.name}, never made` : `${film.name} (${film.year})` }),
      el('p', {}, `${count} sold for `, el('span', { className: 'price', textContent: money(total(film.lots)) }), '.'),
      el('div', { className: 'film-links' }, ...links, external('collection.html?q=' + encodeURIComponent(film.name.split(':').pop().trim()), 'See the lots')));
  }

  for (const film of films) {
    const bar = el('div', { className: 'money-map film-bar' });
    bar.style.height = Math.max(14, Math.round(total(film.lots) / tallest * 340)) + 'px';
    const button = el('button', { className: 'film-name', type: 'button', textContent: film.name });
    button.setAttribute('aria-pressed', 'false');
    button.addEventListener('click', () => choose(film, button));
    host.append(el('div', { className: film.never ? 'film never' : 'film' }, bar,
      el('p', { className: 'film-year', textContent: film.year }), button,
      el('p', { className: 'price', textContent: money(total(film.lots)) })));
    moneyMap(bar, [{ lots: film.lots }]);
    if (film.never) choose(film, button);
  }
}

function findings(lots, byId) {
  career(lots);

  const same = lots.filter((lot) => lot.low === 200 && lot.high === 300);
  const prices = same.map((lot) => lot.sold);
  document.getElementById('same-title').textContent = `${same.length} lots had the same estimate. They sold for anything from ${money(Math.min(...prices))} to ${money(Math.max(...prices))}.`;
  pictureChart(document.getElementById('same-estimate'), same, (lot) => lot.sold, {
    edges: [1000, 2000, 4000, 8000, 16000, 32000, 64000, 200000],
    across: 3,
    label: (edge) => '$' + edge / 1000 + 'k',
  });

  // One bracket holds exactly one pair, so the shared price reads at a glance.
  const card = (lot) => el('figure', { className: 'twin' }, lotTile(lot, 'twin-picture'), el('figcaption', { textContent: pretty(lot.title) }));
  document.getElementById('twins').append(...[['124', '290'], ['216', '106'], ['01', '420'], ['03', '114']].map(([a, b]) => el('div', { className: 'twin-pair' },
    el('p', { className: 'twin-price price', textContent: money(byId.get(a).sold) }), el('div', { className: 'twin-brace' }),
    el('div', { className: 'twin-two' }, card(byId.get(a)), card(byId.get(b))))));

  const risen = [...lots].sort((a, b) => b.multiple - a.multiple);
  const rose = (lot) => el('figure', { className: 'twin' }, lotTile(lot, 'twin-picture'), el('figcaption', {}, el('span', { className: 'price', textContent: times(lot.multiple) }), ' ' + pretty(lot.title)));
  document.getElementById('rose-most').append(...risen.slice(0, 6).map(rose));
  document.getElementById('rose-least').append(...risen.slice(-6).reverse().map(rose));
}

function saleResult(order, tiles) {
  const $ = (id) => document.getElementById('result-' + id);
  const yours = document.getElementById('wall-yours');
  let current;

  function show(bids, shared) {
    const placed = order.filter((lot) => bids.has(lot.id));
    if (!placed.length) return;
    current = bids;
    const lost = placed.filter((lot) => bids.get(lot.id) < lot.sold).length;
    const total = (values) => money(values.reduce((sum, value) => sum + value, 0));
    const miss = (lot) => Math.abs(Math.log(bids.get(lot.id) / lot.sold));
    const closest = placed.reduce((a, b) => (miss(b) < miss(a) ? b : a));
    const percent = Math.round(bids.get(closest.id) / closest.sold * 100);
    const count = placed.length === 1 ? 'one lot' : `${placed.length} lots`;
    const them = placed.length === 1 ? 'It' : 'They';
    $('label').textContent = shared ? 'A shared sale result' : 'Your sale result';
    $('title').textContent = `The room outbid ${shared ? 'this bidder' : 'you'} on ${lost} of ${placed.length}.`;
    $('text').textContent = `${shared ? 'This bidder' : 'You'} bid ${total(placed.map((lot) => bids.get(lot.id)))} across ${count}. `
      + `${them} sold for ${total(placed.map((lot) => lot.sold))}. `
      + `The closest bid was on ${pretty(closest.title)}, at ${percent}% of what it made.`;
    $('rows').replaceChildren(...placed.map((lot) => el('tr', {},
      el('td', {}, el('a', { href: lotHref(lot), textContent: pretty(lot.title) })),
      el('td', { textContent: money(bids.get(lot.id)) }),
      el('td', { className: 'price', textContent: money(lot.sold) }))));
    $('body').hidden = false;
    $('share').hidden = shared;
    $('reset').hidden = shared;
    tiles.forEach((tile, id) => tile.classList.toggle('yours', bids.has(id)));
    yours.textContent = `${shared ? 'The lots bid on' : 'Your lots'} are outlined in red.`;
  }

  $('share').addEventListener('click', async () => {
    const values = order.map((lot) => current.get(lot.id) || 0).join(',');
    const url = `${location.origin}${location.pathname}?bids=${values}#result`;
    const text = $('title').textContent.replace('outbid you', 'outbid me') + ' David Lynch’s things, sold in one sale.';
    try {
      if (navigator.share) {
        await navigator.share({ text, url });
      } else {
        await navigator.clipboard.writeText(`${text} ${url}`);
        $('shared').textContent = 'Copied to the clipboard.';
      }
    } catch (error) {
      if (error.name !== 'AbortError') $('shared').textContent = 'Sharing did not work here. Copy this link instead: ' + url;
    }
  });
  $('reset').addEventListener('click', () => {
    if (!confirm('Clear all your bids and start the story again?')) return;
    saveProgress({ bids: {}, at: '', y: 0 });
    location.href = location.pathname;
  });
  return show;
}

// A shared link holds one bid per chapter, in order. 0 means no bid.
function sharedBids(order) {
  const values = (new URLSearchParams(location.search).get('bids') || '').split(',');
  const bids = new Map();
  order.forEach((lot, i) => {
    const value = Number(values[i]);
    if (Number.isInteger(value) && value >= BID_MIN && value <= BID_MAX) bids.set(lot.id, value);
  });
  return bids;
}

const CHAPTERS = [['wrote', 'Wrote'], ['filmed', 'Filmed'], ['painted', 'Painted'], ['built', 'Built and furnished'], ['played', 'Played'], ['read', 'Read']];
const PROGRESS = 'lynch-story';

// Progress lasts for the browser tab. The story still works if storage is blocked.
function loadProgress() {
  try {
    return { bids: {}, at: '', y: 0, ...JSON.parse(sessionStorage.getItem(PROGRESS)) };
  } catch {
    return { bids: {}, at: '', y: 0 };
  }
}
function saveProgress(progress) {
  try {
    sessionStorage.setItem(PROGRESS, JSON.stringify(progress));
  } catch { /* Progress is a convenience, so the story carries on without it. */ }
}

// The chapter bar lives on the story page only; other pages get backLink().
function paddle() {
  const marks = CHAPTERS.map(([id, title], i) => ({ id, title, link: el('a', { href: 'index.html#' + id, textContent: i + 1 }) }));
  const total = el('span', { className: 'paddle-total' });
  const bar = el('nav', { className: 'paddle', hidden: true }, el('ol', {}, ...marks.map(({ link }) => el('li', {}, link))), total);
  bar.setAttribute('aria-label', 'Story progress');
  document.body.append(bar);

  function update(progress) {
    const index = CHAPTERS.findIndex(([id]) => id === progress.at);
    bar.hidden = index < 0;
    if (index < 0) return;
    for (const { id, title, link } of marks) {
      const bid = progress.bids[id];
      link.classList.toggle('done', bid !== undefined);
      link.setAttribute('aria-label', `${link.textContent}. ${title}, ${bid ? 'bid ' + money(bid) : bid === 0 ? 'skipped' : 'no bid yet'}`);
      if (id === progress.at) link.setAttribute('aria-current', 'step');
      else link.removeAttribute('aria-current');
    }
    const spent = Object.values(progress.bids).reduce((sum, bid) => sum + bid, 0);
    total.textContent = `Your bids ${money(spent)}`;
  }
  update(loadProgress());
  return { update };
}

function lotPanel(byId) {
  const dialog = document.getElementById('lot-dialog');
  const image = document.getElementById('lot-dialog-image');
  let source;
  let pushed = false;

  const urlFor = (id) => {
    const params = new URLSearchParams(location.search);
    if (id) params.set('lot', id);
    else params.delete('lot');
    const query = params.toString();
    return location.pathname + (query ? '?' + query : '');
  };

  // The picture morphs between the story and the panel where the browser can do it.
  function morph(change, from, to) {
    if (!document.startViewTransition || calm.matches || !from || !to) {
      change();
      return;
    }
    from.style.viewTransitionName = 'lot';
    document.startViewTransition(() => {
      from.style.viewTransitionName = '';
      change();
      to.style.viewTransitionName = 'lot';
    }).finished.finally(() => { to.style.viewTransitionName = ''; });
  }

  async function show(lot, from) {
    fillLotDialog(lot);
    source = from;
    await image.decode().catch(() => {});
    morph(() => dialog.showModal(), from, image);
  }

  function hide() {
    if (dialog.open) morph(() => dialog.close(), image, source);
  }

  function open(lot, from) {
    history.pushState(null, '', urlFor(lot.id));
    pushed = true;
    show(lot, from);
  }

  function dismiss() {
    if (pushed) {
      history.back();
      return;
    }
    history.replaceState(null, '', urlFor(''));
    hide();
  }

  document.addEventListener('click', (event) => {
    const link = event.target.closest?.('a[href*="?lot="]');
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey) return;
    const lot = byId.get(new URLSearchParams(link.search).get('lot'));
    if (!lot) return;
    event.preventDefault();
    open(lot, link.querySelector('img'));
  });
  dialog.addEventListener('cancel', (event) => {
    event.preventDefault();
    dismiss();
  });
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dismiss();
  });
  document.getElementById('lot-dialog-close').addEventListener('click', dismiss);
  addEventListener('popstate', () => {
    pushed = false;
    const lot = byId.get(new URLSearchParams(location.search).get('lot'));
    if (lot) show(lot);
    else hide();
  });

  const start = byId.get(new URLSearchParams(location.search).get('lot'));
  if (start) show(start);
  return open;
}

// Chapter opening: the title with objects set in the gaps between its words.
function spreads(byId) {
  document.querySelectorAll('.spread').forEach((spread) => {
    const ids = spread.dataset.lots.split(',');
    const lot = byId.get(ids[0]);
    spread.append(el('a', { className: 'spread-figure', href: lotHref(lot) },
      el('img', { className: 'object', src: `img/lots/${lot.id}.webp`, alt: '', loading: 'lazy' }),
      el('span', { className: 'spread-caption', textContent: pretty(lot.title) })));
    closingPlate(spread.closest('.chapter'), ids, byId);
  });
}

// Shown once the chapter's bid is placed, so its prices give nothing away.
function closingPlate(chapter, ids, byId) {
  const stage = chapter.querySelector('.stage');
  const number = CHAPTERS.findIndex(([id]) => id === chapter.id);
  const lots = [stage.dataset.lot, ...ids.slice(0, 5)].map((id) => byId.get(id));
  const figure = (lot, i) => el('a', { className: i ? 'closing-fig' : 'closing-fig lead', href: lotHref(lot) },
    el('img', { className: 'object', src: `img/${i ? 'thumbs' : 'lots'}/${lot.id}.webp`, alt: '', loading: 'lazy' }),
    el('span', { className: 'fig-name', textContent: pretty(lot.title) }),
    el('span', { className: 'price', textContent: money(lot.sold) }));
  const plate = el('section', { className: 'closing-plate' },
    el('div', {},
      el('h3', { className: 'overline', textContent: 'More from this chapter' }),
      el('p', { className: 'help', textContent: 'Six lots, with what each sold for. The first is the lot you bid on.' })),
    el('div', { className: 'closing-figs' }, ...lots.map(figure)));
  plate.setAttribute('aria-label', `More from ${CHAPTERS[number][1]}`);
  stage.after(plate);
}

function followChapters(onChapter) {
  const chapters = [...document.querySelectorAll('.chapter')];
  let queued = false;
  function update() {
    queued = false;
    const passed = chapters.filter((chapter) => chapter.getBoundingClientRect().top <= innerHeight / 2);
    onChapter(passed.length ? passed[passed.length - 1].id : '');
  }
  addEventListener('scroll', () => {
    if (queued) return;
    queued = true;
    requestAnimationFrame(update);
  }, { passive: true });
  update();
}

// Objects on screen fly to their own cards in the Collection, where the browser can do it.
function flyToCollection(lots) {
  addEventListener('pageswap', (event) => {
    if (!event.viewTransition || calm.matches || !/\/collection(\.html)?$/.test(new URL(event.activation?.entry?.url || '/', location.href).pathname)) return;
    const seen = new Map();
    const reach = innerHeight * 1.5; // Objects just off screen fly in too.
    for (const node of document.querySelectorAll('.plate img, .spread-figure img, .closing-fig img, .aside-lot img, .interlude-lot img, .chart-tile img, .machine img, .tile')) {
      const link = node.closest('a');
      const id = node.dataset.lot || (link ? new URLSearchParams(link.search).get('lot') : node.closest('.stage')?.dataset.lot);
      const box = node.getBoundingClientRect();
      if (id && !seen.has(id) && box.bottom > -reach && box.top < innerHeight + reach && seen.size < 12) seen.set(id, node);
    }
    seen.forEach((node, id) => { node.style.viewTransitionName = 'lot-' + id; });
    try {
      sessionStorage.setItem('lynch-flight', JSON.stringify([...seen.keys()]));
      sessionStorage.setItem('lynch-lots', JSON.stringify(lots));
    } catch { /* The pages cross-fade instead. */ }
  });
}

function landInCollection() {
  addEventListener('pagereveal', (event) => {
    if (!event.viewTransition) return;
    let ids = [];
    try {
      ids = JSON.parse(sessionStorage.getItem('lynch-flight')) || [];
      sessionStorage.removeItem('lynch-flight');
    } catch { /* The pages cross-fade instead. */ }
    const grid = document.getElementById('lots');
    const cards = ids.map((id) => [id, document.querySelector(`a.lot[href="?lot=${id}"] img`)])
      .filter(([, image]) => image && image.getBoundingClientRect().top < innerHeight);
    const delays = el('style', {
      textContent: cards.map(([id], i) => `::view-transition-group(lot-${id}) { animation-delay: ${i * 45}ms; }`).join(''),
    });
    document.head.append(delays);
    cards.forEach(([id, image]) => {
      image.loading = 'eager';
      image.style.viewTransitionName = 'lot-' + id;
    });
    event.viewTransition.finished.finally(() => {
      delays.remove();
      cards.forEach(([, image]) => { image.style.viewTransitionName = ''; });
    });
  });
}

const THEME_ICONS = '<span><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/></svg></span>'
  + '<span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/></svg></span>';

function themeToggle() {
  const root = document.documentElement;
  const button = el('button', { className: 'theme-toggle', type: 'button', innerHTML: THEME_ICONS });
  button.setAttribute('role', 'switch');
  button.setAttribute('aria-label', 'Dark theme');
  const apply = (theme) => {
    root.dataset.theme = theme;
    button.setAttribute('aria-checked', theme === 'dark');
  };
  const remembered = () => {
    try {
      return localStorage.getItem('theme');
    } catch {
      return null;
    }
  };
  const device = matchMedia('(prefers-color-scheme: dark)');
  button.addEventListener('click', () => {
    const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try {
      localStorage.setItem('theme', next);
    } catch { /* The choice lasts for this page only. */ }
    if (document.startViewTransition && !calm.matches) document.startViewTransition(() => apply(next));
    else apply(next);
  });
  device.addEventListener('change', () => {
    if (!remembered()) apply(device.matches ? 'dark' : 'light');
  });
  apply(root.dataset.theme || 'light');
  document.querySelector('.site-links').append(button);
}

async function story() {
  history.scrollRestoration = 'manual';
  const progress = loadProgress();
  const ready = () => saveProgress(progress);
  try {
    const lots = await loadJSON('data/lots.json');
    const byId = new Map(lots.map((lot) => [lot.id, lot]));
    const stages = [...document.querySelectorAll('.stage')];
    const order = stages.map((stage) => byId.get(stage.dataset.lot));
    const openLot = lotPanel(byId);
    flyToCollection(lots);
    const tiles = wall(lots, (lot) => openLot(lot));
    const showResult = saleResult(order, tiles);
    const bids = new Map();
    spreads(byId);
    findingCharts(lots);
    lotPeek(byId);
    stages.forEach((stage, i) => {
      const { id } = stage.closest('.chapter');
      const saved = progress.bids[id];
      if (saved) bids.set(order[i].id, saved);
      lotBid(stage, order[i], saved, (bid) => {
        progress.bids[id] = bid || 0;
        ready();
        paddleBar.update(progress);
        if (bid) {
          bids.set(order[i].id, bid);
          showResult(bids, false);
        }
      });
    });
    barRows('estimate-bars', ESTIMATE_BANDS.map(([min, max, label]) => {
      const group = lots.filter((lot) => (lot.low + lot.high) / 2 >= min && (lot.low + lot.high) / 2 < max);
      const multiple = median(group.map((lot) => lot.multiple));
      return { label, lots: group.length, size: multiple, value: times(multiple) };
    }));
    const shared = sharedBids(order);
    if (shared.size) showResult(shared, true);
    else showResult(bids, false);

    // A refresh starts the story from the top; Continue reading still offers the saved place.
    const how = performance.getEntriesByType('navigation')[0]?.type;
    if (how === 'reload' && location.hash) history.replaceState(null, '', location.pathname + location.search);
    const target = location.hash && document.querySelector(location.hash);
    if (shared.size) document.getElementById('result').scrollIntoView();
    else if (how === 'reload') scrollTo(0, 0);
    else if (target) target.scrollIntoView();
    else if (progress.y) {
      scrollTo(0, progress.y);
      // Pictures above may finish loading and push the page; land again if the reader has not moved.
      const first = scrollY;
      addEventListener('load', () => { if (Math.abs(scrollY - first) < 2) scrollTo(0, progress.y); }, { once: true });
    }
    if (progress.at) {
      const begin = document.getElementById('begin');
      begin.textContent = 'Continue reading';
      begin.href = '#' + progress.at;
    }
    followChapters((at) => {
      if (at === progress.at) return;
      progress.at = at;
      if (at) ready(); // Back at the opening, the saved chapter stays for Continue reading.
      paddleBar.update(progress);
    });
    // Reads storage again, so a reset just before leaving is not undone.
    addEventListener('pagehide', () => {
      const saved = loadProgress();
      if (saved.at) saveProgress({ ...saved, y: scrollY });
    });
  } catch {
    document.querySelectorAll('.bid-controls').forEach((node) => {
      node.textContent = 'The bid could not be loaded. Reload the page to try again.';
    });
    document.getElementById('wall-detail').textContent = 'The lots could not be loaded. Reload the page to try again.';
    document.getElementById('wall-views').hidden = true;
  }
}

// Dashboards: five tabs, each with its own address.
async function dashboards() {
  const tabs = [...document.querySelectorAll('.dash-tab')];
  const params = new URLSearchParams(location.search);
  const total = (list) => list.reduce((sum, lot) => sum + lot.sold, 0);
  const kpis = (id, rows) => document.getElementById(id).replaceChildren(...rows.map(([value, label, price]) =>
    el('div', { className: 'kpi' }, el('b', { className: price ? 'price' : '', textContent: value }), el('span', { textContent: label }))));
  const log = (v, min, max) => (Math.log10(v) - Math.log10(min)) / (Math.log10(max) - Math.log10(min));
  // Columns for plain ranges, count on each cap and the range under it, so no axis has to be decoded.
  const histogram = (host, list, bins, unit) => {
    const counts = bins.map(([min, max]) => list.filter((v) => v >= min && v < max).length);
    const top = Math.max(...counts, 1);
    host.replaceChildren(...bins.map(([, , label], i) => {
      const bar = el('span', { className: 'column-bar' });
      bar.style.height = (counts[i] / top) * 100 + '%';
      const column = el('span', { className: 'column', title: `${label}: ${counts[i]} lots` },
        el('span', { className: 'column-plot' }, el('span', { className: 'column-count', textContent: counts[i] }), bar),
        el('span', { className: 'column-label', textContent: label }));
      return column;
    }), el('p', { className: 'axis-title', textContent: unit }));
    host.setAttribute('role', 'img');
    host.style.setProperty('--bins', bins.length);
    host.setAttribute('aria-label', 'Number of lots. ' + bins.map(([, , label], i) => `${label}: ${counts[i]}`).join('. '));
  };

  function show(name, focus) {
    for (const tab of tabs) {
      const on = tab.dataset.tab === name;
      tab.setAttribute('aria-selected', on);
      tab.tabIndex = on ? 0 : -1;
      document.getElementById(tab.getAttribute('aria-controls')).hidden = !on;
      if (on && focus) tab.focus();
    }
    const next = new URLSearchParams(location.search);
    if (name === 'overview') next.delete('tab'); else next.set('tab', name);
    if (name !== 'overview') next.delete('cat');
    history.replaceState(null, '', next.size ? '?' + next : location.pathname);
  }
  tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => show(tab.dataset.tab));
    tab.addEventListener('keydown', (event) => {
      const next = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[event.key];
      if (next === undefined) return;
      event.preventDefault();
      show(tabs[(next + tabs.length) % tabs.length].dataset.tab, true);
    });
  });
  show(tabs.some((tab) => tab.dataset.tab === params.get('tab')) ? params.get('tab') : 'overview');

  let lots, books;
  try {
    [lots, books] = await Promise.all([loadJSON('data/lots.json'), loadJSON('data/books.json')]);
  } catch {
    document.querySelector('.page-head .help').textContent = 'The data could not be loaded. Reload the page to try again.';
    return;
  }
  const byId = new Map(lots.map((lot) => [lot.id, lot]));
  lotPeek(byId);
  lotPanel(byId);
  const names = [...new Set(lots.map((lot) => lot.category))];
  const groups = names.map((name) => {
    const list = lots.filter((lot) => lot.category === name);
    return { name, list, count: list.length, total: total(list), median: median(list.map((lot) => lot.sold)), multiple: median(list.map((lot) => lot.multiple)) };
  });
  const all = total(lots);
  groups.forEach((group) => { group.share = group.total / all; });

  // Overview
  let current = names.includes(params.get('cat')) ? params.get('cat') : null;
  const inCategory = (name) => lots.filter((lot) => lot.category === name);
  const scripts = inCategory('Scripts & Papers');
  const furniture = inCategory('Furniture & Rugs');
  document.getElementById('map-say').textContent = `Every lot is a picture, and its area is what it sold for. ${scripts.length} lots of scripts and papers made ${money(total(scripts))}. The ${furniture.length} lots of furniture and rugs made ${money(total(furniture))}.`;
  const map = document.getElementById('sale-map');
  const byTotal = [...groups].sort((a, b) => b.total - a.total);
  moneyMap(map, byTotal.map((group) => ({ name: group.name, lots: group.list })));
  const leaves = [...map.querySelectorAll('.leaf')];
  const chips = [[null, 'All'], ...byTotal.map((group) => [group.name, group.name])].map(([name, text]) => {
    const chip = choiceButton(text, () => { current = name; overview(); });
    chip.dataset.cat = name || '';
    return chip;
  });
  document.getElementById('d-chips').append(...chips);
  const dearest = new Set([...lots].sort((a, b) => b.sold - a.sold).slice(0, 20));
  const dots = lots.map((lot) => {
    const dot = el('span', { className: dearest.has(lot) ? 'dot pic' : 'dot' });
    if (dearest.has(lot)) dot.style.backgroundImage = `url(img/thumbs/${lot.id}.webp)`;
    dot.dataset.peek = lot.id;
    dot.style.left = log((lot.low + lot.high) / 2, 50, 20000) * 100 + '%';
    dot.style.top = (1 - log(lot.sold, 300, 300000)) * 100 + '%';
    return dot;
  });
  const scatter = document.getElementById('d-scatter');
  scatter.append(...dots);
  for (const [value, axis] of [[100, 'x'], [1000, 'x'], [10000, 'x'], [1000, 'y'], [10000, 'y'], [100000, 'y']]) {
    const tick = el('span', { className: 'tick-' + axis, textContent: money(value) });
    const grid = el('span', { className: 'grid-' + axis });
    if (axis === 'x') grid.style.left = tick.style.left = log(value, 50, 20000) * 100 + '%';
    else grid.style.top = tick.style.top = (1 - log(value, 300, 300000)) * 100 + '%';
    scatter.prepend(grid);
    scatter.append(tick);
  }
  // Lines where a lot sold at its estimate and at ten times it.
  const point = (estimate, factor) => `${log(estimate, 50, 20000) * 100},${(1 - log(estimate * factor, 300, 300000)) * 100}`;
  const guides = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  guides.setAttribute('class', 'guides');
  guides.setAttribute('viewBox', '0 0 100 100');
  guides.setAttribute('preserveAspectRatio', 'none');
  guides.innerHTML = [1, 10, 100].map((factor) => `<polyline points="${point(50, factor)} ${point(20000, factor)}" vector-effect="non-scaling-stroke"/>`).join('');
  scatter.prepend(guides);
  for (const [factor, text, estimate] of [[1, 'Sold at estimate', 3000], [10, '10×', 2500], [100, '100×', 600]]) {
    const label = el('span', { className: 'guide-label', textContent: text });
    label.style.left = log(estimate, 50, 20000) * 100 + '%';
    label.style.top = (1 - log(estimate * factor, 300, 300000)) * 100 + '%';
    scatter.append(label);
  }
  scatter.append(el('span', { className: 'axis-x', textContent: 'Estimate midpoint' }), el('span', { className: 'axis-y', textContent: 'Sold for' }));
  const multipleBins = [[0, 1, 'Under 1×'], [1, 5, '1–5×'], [5, 10, '5–10×'], [10, 20, '10–20×'], [20, 50, '20–50×'], [50, 100, '50–100×'], [100, Infinity, '100× and up']];

  function overview() {
    const list = current ? lots.filter((lot) => lot.category === current) : lots;
    document.getElementById('d-title').textContent = current ? `${current}: ${list.length} lots` : 'All 441 lots';
    kpis('d-kpis', [[money(total(list)), 'Sold for in total', true], [String(list.length), 'Lots'], [money(median(list.map((lot) => lot.sold))), 'Median price', true], [times(median(list.map((lot) => lot.multiple))), 'Typical multiple of the estimate']]);
    chips.forEach((chip) => chip.setAttribute('aria-pressed', chip.dataset.cat === (current || '')));
    leaves.forEach((leaf) => leaf.classList.toggle('dim', !!current && byId.get(leaf.dataset.peek).category !== current));
    picBars('d-top', [...list].sort((a, b) => b.sold - a.sold).slice(0, 10));
    document.getElementById('d-more').href = current ? 'collection.html?cat=' + encodeURIComponent(current) : 'collection.html';
    if (!document.getElementById('panel-overview').hidden) {
      const next = new URLSearchParams(location.search);
      if (current) next.set('cat', current); else next.delete('cat');
      history.replaceState(null, '', next.size ? '?' + next : location.pathname);
    }
  }
  overview();
  document.querySelectorAll('[data-tab-link]').forEach((link) => link.addEventListener('click', (event) => {
    if (event.metaKey || event.ctrlKey || event.shiftKey) return;
    event.preventDefault();
    show(link.dataset.tabLink, true);
    document.querySelector('.dash-tabs').scrollIntoView({ behavior: calm.matches ? 'auto' : 'smooth' });
  }));

  // Prices
  histogram(document.getElementById('d-multiples'), lots.map((lot) => lot.multiple), multipleBins, 'Sold price as a multiple of the estimate midpoint');
  findings(lots, byId);

  const prices = lots.map((lot) => lot.sold);
  kpis('p-kpis', [[money(Math.max(...prices)), 'Highest price', true], [money(median(prices)), 'Median price', true], [money(Math.min(...prices)), 'Lowest price', true], [String(lots.filter((lot) => lot.sold < lot.low).length), 'Lots below their estimate']]);
  histogram(document.getElementById('p-prices'), prices, [[0, 2000, 'Under $2k'], [2000, 5000, '$2k–5k'], [5000, 10000, '$5k–10k'], [10000, 20000, '$10k–20k'], [20000, 50000, '$20k–50k'], [50000, 100000, '$50k–100k'], [100000, Infinity, '$100k and up']], 'Sold for');

  // Categories
  const table = document.getElementById('c-table');
  let sort = 'total', down = true;
  function categories() {
    const rows = [...groups].sort((a, b) => (sort === 'name' ? a.name.localeCompare(b.name) : a[sort] - b[sort]) * (down ? -1 : 1));
    table.tBodies[0].replaceChildren(...rows.map((group) => {
      const top = [...group.list].sort((a, b) => b.sold - a.sold)[0];
      const share = el('span', { className: 'share-bar' });
      share.style.width = group.share * 250 + '%';
      return el('tr', {},
        el('th', { scope: 'row' }, el('a', { href: 'collection.html?cat=' + encodeURIComponent(group.name), textContent: group.name })),
        el('td', { textContent: group.count }),
        el('td', { className: 'price', textContent: money(group.total) }),
        el('td', {}, el('span', { textContent: Math.round(group.share * 100) + '%' }), share),
        el('td', { className: 'price', textContent: money(group.median) }),
        el('td', { textContent: times(group.multiple) }),
        el('td', {}, lotTile(top, 'row-picture')));
    }));
    table.querySelectorAll('th[scope="col"]').forEach((th) => {
      const key = th.querySelector('button')?.dataset.sort;
      if (key === sort) th.setAttribute('aria-sort', down ? 'descending' : 'ascending');
      else th.removeAttribute('aria-sort');
    });
  }
  table.querySelectorAll('[data-sort]').forEach((button) => button.addEventListener('click', () => {
    down = sort === button.dataset.sort ? !down : button.dataset.sort !== 'name';
    sort = button.dataset.sort;
    categories();
  }));
  categories();

  // Films as a poster grid, largest total first. Posters come from scripts/fetch_posters.py;
  // Ronnie Rocket was never made, so its own screenplay stands in.
  const posters = await loadJSON('data/posters.json').catch(() => ({}));
  const films = FILMS.map((film) => ({ film, list: lots.filter((lot) => film.match.test(lot.title)) }))
    .map((entry) => ({ ...entry, sum: total(entry.list) })).sort((a, b) => b.sum - a.sum);
  const most = films[0].sum;
  const external = (href, text) => el('a', { href, textContent: text });
  document.getElementById('f-films').append(...films.map(({ film, list, sum }) => {
    const search = 'collection.html?q=' + encodeURIComponent(film.name.split(':').pop().trim());
    const picture = film.never
      ? el('img', { className: 'object', src: 'img/thumbs/15.webp', alt: '', loading: 'lazy' })
      : posters[film.imdb]
        ? el('img', { src: 'https://image.tmdb.org/t/p/w342' + posters[film.imdb], alt: '', loading: 'lazy' })
        : el('span', { className: 'poster-card', textContent: film.name });
    const bar = el('span', { className: 'film-bar-fill' });
    bar.style.width = sum / most * 100 + '%';
    const links = film.never ? [external(film.wiki, 'Wikipedia')]
      : [external('https://www.imdb.com/title/' + film.imdb + '/', 'IMDb'), external(`https://letterboxd.com/film/${film.letterboxd}/`, 'Letterboxd'), external('https://www.rottentomatoes.com/' + film.tomatoes, 'Rotten Tomatoes')];
    return el('li', { className: 'film-card' },
      el('a', { className: film.never ? 'film-poster script' : 'film-poster', href: search }, picture),
      el('h3', {}, el('a', { href: search, textContent: film.name })),
      el('p', { className: 'film-year', textContent: film.never ? 'Never made, script only' : film.year }),
      el('p', { className: 'film-sum' }, el('span', { className: 'price', textContent: money(sum) }), ` from ${list.length === 1 ? 'one lot' : list.length + ' lots'}`),
      el('span', { className: 'film-bar' }, bar),
      el('p', { className: 'film-links' }, ...links));
  }));

  // Books
  const bookCount = books.reduce((sum, lot) => sum + lot.books.length, 0);
  const bookLots = books.map((lot) => byId.get(lot.lot)).filter(Boolean);
  kpis('b-kpis', [[String(bookCount), 'Books listed'], [String(books.length), 'Lots of books'], [money(total(bookLots)), 'Sold for in total', true], [money(median(bookLots.map((lot) => lot.sold))), 'Median price of a lot', true]]);
  // One spine per book, shelved by subject. The spines are for the pointer; the subject links carry the same facts.
  const shelves = [...new Set(books.map((lot) => lot.category))].map((name) => {
    const spines = books.filter((lot) => lot.category === name).flatMap((lot) => lot.books.map((book) => [book, byId.get(lot.lot)]));
    return [name, spines];
  }).sort((a, b) => b[1].length - a[1].length);
  document.getElementById('b-shelf').append(...shelves.map(([name, spines]) => el('li', { className: 'shelf-group' },
    el('div', { className: 'spines', ariaHidden: 'true' }, ...spines.map(([book, lot], i) => {
      const spine = el('a', { className: 'spine tone-' + (book.title.length + i) % 3, href: lotHref(lot), tabIndex: -1 });
      spine.style.height = 44 + (book.title.length * 7 + i * 13) % 40 + 'px';
      spine.dataset.peek = lot.id;
      spine.dataset.caption = book.author && !/unknown|various/i.test(book.author) ? `${book.title}, by ${book.author}` : book.title;
      return spine;
    })),
    el('a', { className: 'shelf-label', href: 'library.html?cat=' + encodeURIComponent(name) }, name + ' ', el('span', { textContent: `${spines.length} ${spines.length === 1 ? 'book' : 'books'}` })))));
  picBars('b-top', bookLots.sort((a, b) => b.sold - a.sold).slice(0, 8));
  const authors = new Map();
  for (const lot of books) {
    for (const book of lot.books) {
      if (!book.author || /unknown|various/i.test(book.author)) continue;
      const entry = authors.get(book.author) || { books: 0, lots: new Set() };
      entry.books += 1;
      entry.lots.add(lot.lot);
      authors.set(book.author, entry);
    }
  }
  // Portraits come from scripts/fetch_authors.py; an author with no free photo gets a name card.
  const photos = await loadJSON('data/authors.json').catch(() => ({}));
  const frequent = [...authors].filter(([, entry]) => entry.books > 1).sort((a, b) => b[1].books - a[1].books || a[0].localeCompare(b[0]));
  const mostBooks = frequent[0][1].books;
  document.getElementById('b-authors').append(...frequent.map(([name, entry]) => {
    const search = 'library.html?q=' + encodeURIComponent(name);
    const photo = photos[name];
    const bar = el('span', { className: 'film-bar-fill' });
    bar.style.width = entry.books / mostBooks * 100 + '%';
    return el('li', { className: 'film-card' },
      el('a', { className: 'film-poster', href: search }, photo
        ? el('img', { src: photo.src, alt: '', loading: 'lazy' })
        : el('span', { className: 'poster-card', textContent: name })),
      el('h4', {}, el('a', { href: search, textContent: name })),
      el('p', { className: 'film-sum', textContent: `${entry.books} books in ${entry.lots.size === 1 ? 'one lot' : entry.lots.size + ' lots'}` }),
      el('span', { className: 'film-bar' }, bar),
      photo ? el('p', { className: 'film-links' }, external(photo.page, 'Wikipedia'), external(photo.file, `Photo: ${photo.artist}, ${photo.licence}`)) : '');
  }));
}

function toTop() {
  const button = el('button', { className: 'to-top', type: 'button', textContent: '↑', hidden: true });
  button.setAttribute('aria-label', 'Back to top');
  button.addEventListener('click', () => {
    scrollTo({ top: 0, behavior: calm.matches ? 'auto' : 'smooth' });
    document.querySelector('header a')?.focus({ preventScroll: true });
  });
  addEventListener('scroll', () => { button.hidden = scrollY < innerHeight * 1.5; }, { passive: true });
  document.body.append(button);
}

// Links to other sites open in a new tab, including ones the page builds later.
document.addEventListener('click', (event) => {
  const link = event.target.closest?.('a[href]');
  if (link && link.origin !== location.origin) {
    link.target = '_blank';
    link.rel = 'noopener';
  }
}, true);

// One way back on every page but the story. The Collection and the Library return to the page the reader came from;
// otherwise a reader partway through the story gets their chapter back.
function backLink() {
  const names = { collection: 'Collection', library: 'Library', dashboards: 'Dashboards', about: 'About' };
  const tabs = { overview: 'Overview', findings: 'Findings', prices: 'Prices', categories: 'Categories', films: 'Films', books: 'Books' };
  // The live host serves pages without .html, so compare names, not file names.
  const file = (url) => url.pathname.split('/').pop().replace(/\.html$/, '') || 'index';
  let from = null;
  try {
    from = new URL(document.referrer);
  } catch { /* Arrived directly. */ }
  let link;
  if (['collection', 'library'].includes(document.body.dataset.page) && from?.origin === location.origin && names[file(from)] && file(from) !== file(location)) {
    const tab = file(from) === 'dashboards' ? ': ' + tabs[from.searchParams.get('tab') || 'overview'] : '';
    link = el('a', { href: from.href, textContent: `Back to ${names[file(from)]}${tab}` });
  } else {
    const index = CHAPTERS.findIndex(([id]) => id === loadProgress().at);
    if (index >= 0) link = el('a', { href: 'index.html', textContent: `Back to chapter ${index + 1}: ${CHAPTERS[index][1]}` });
  }
  if (link) document.querySelector('main').prepend(el('p', { className: 'back' }, link));
}

const pages = { collection, library, story, dashboards };
const paddleBar = document.body.dataset.page === 'story' ? paddle() : backLink();
themeToggle();
toTop();
if (document.body.dataset.page === 'collection') landInCollection();
pages[document.body.dataset.page]?.();
