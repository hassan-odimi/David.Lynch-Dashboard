# David Lynch Collection: static site rebuild plan

Approved by Hassan on 2026-11-06. Follow the steps in order. Stop at every **STOP** and wait for Hassan's answer.

## Goal

Replace the Streamlit app with a static site in the auction catalogue look, hosted on Cloudflare Pages at `lynch.hassan-odimi.se`. Tidy the repo so it reads well to a reviewer.

## Decisions already made

Do not reopen these.

- **Platform:** plain HTML, CSS and JS. No framework, no npm build. Cloudflare Pages cannot run a Streamlit server.
- **Look:** auction catalogue. Source: `docs/redesign/catalogue-mock.dc.html`. Live board: https://claude.ai/artifact/7ek8H6VLwodfJeSgCYBGK2 (board 1).
- **Pages:** Overview, Collection, Library, About.
- **Features:** lot detail, filters stored in the URL, Guess the price, wall that becomes a chart.
- **Images:** self-hosted, with source credit.
- **Address:** `lynch.hassan-odimi.se`, plus the free `pages.dev` address.
- **Old app:** tag `streamlit-v1`, then remove its code from `main`. Git history is not rewritten.
- **Left out:** light mode, CSV export, room-by-room tour, price climb opening, Sankey and sunburst charts, Amazon links.

## Rules for every step

- Work in this checkout on branch `redesign/plan`. Never push.
- Commit once per step. Add files by name. Never run `git add .` or `git add -A`.
- Never touch the uncommitted `requirements.txt`, `Lynch Portfolio Screens/`, `.venv/` or `venv/`, except where step 8 says so.
- Use `.venv` for Python. Pillow is already installed there.
- Keep it small: stdlib and native browser features first, no new dependency, fewest files that work.
- Put text from data or the URL on the page with `textContent`, never `innerHTML`.
- Do not state anything the data cannot support. Do not use "Lynch factor" or "from his home and studio". Do not call `Item ID` a lot number, because that is not confirmed. Whether sold prices include buyer's premium is also unknown.
- Before you mark a step done, run its check and report the real result.

## Target structure

```text
site/
  index.html          Overview: finding, figures, wall, Guess the price
  collection.html     image grid, search, sort, filters, lot detail
  library.html        books
  about.html
  style.css
  app.js              shared helpers and page code
  data/lots.json
  data/books.json
  img/lots/<id>.webp  1200 px
  img/thumbs/<id>.webp 400 px
  img/wall.webp       441-lot image sheet
scripts/
  build_data.py
  build_images.py
  test_build_data.py
```

## Design values

From the mock-up. If this list and the mock-up differ, the mock-up wins.

- **Colours:** paper `#F4F0E7`, ink `#1B1815`, muted `#5E564C`, panel `#EBE5D8`, red accent `#B3261E`. Red is for prices and results only.
- **Type:** Libre Caslon Display for large figures and headings, Libre Caslon Text for captions and prose, Libre Franklin for interface text. Load them with the Google Fonts link in the mock-up.
- **Rules:** 1 px ink lines, no shadows, no rounded corners, no emoji.
- **Objects:** `mix-blend-mode: multiply` so white photo backgrounds melt into the paper.
- **Width:** content `max-width` 1240 px, 24 px side gutter. Touch targets at least 44 px.

## Facts checked against the data

- 441 lots, $4,245,930 total, $5,200 median sale.
- Median multiple 18.2× (sold price against estimate midpoint).
- 440 of 441 sold above the high estimate. One sold below its low estimate: Vladimir Kagan Swan Back Sofa, $6,500 against $8,000 to $10,000.
- Highest price is a tie at $195,000: "Ronnie Rocket" and "Lost Highway", each 780× their midpoint.
- Lowest price: EcoloBlue Atmospheric Water Generator, $910.
- Books file: 38 lots, 287 books. Its metadata says 62 lots and 315 books, and those figures are wrong. Count from the data.
- 167 books have no known author. Say so rather than hide it.

## Steps

### 1. Lock the data

Skill: `lean-build`.

- Write `scripts/build_data.py`, stdlib only. It reads the two source JSON files and writes `site/data/lots.json` and `site/data/books.json`.
- Each lot holds id, title, low, high, sold, multiple, category and URL.
- Start categories from `docs/redesign/draft-categories.py`. Fix rule order: "Performax Drum Sander" currently lands in Music & Audio, and must be Workshop & Tools. The fix should work for that kind of title, not only that one.
- Write `scripts/test_build_data.py` with plain asserts: every figure in "Facts checked against the data", "Household & Other" at 60 lots or fewer, the drum sander in Workshop & Tools, and "Prop Matchbooks" not in Books & Magazines.

**Check:** `.venv/bin/python scripts/test_build_data.py` passes.

**STOP:** show Hassan a table of each category with its count and 5 sample titles. Apply corrections, then continue.

### 2. Prepare images

- **STOP first:** ask Hassan to approve downloading 441 images from `assets.basta.app`, about 30 to 50 MB after conversion. The local copies in `archived_auction_data/items_images/` are poor: 441 px tall with dark bars baked in.
- Write `scripts/build_images.py` with `urllib` and Pillow. Take each `Item Image` URL from the data, set `width=1200`, and save `site/img/lots/<id>.webp` and `site/img/thumbs/<id>.webp`. Use a generic User-Agent and go one at a time.
- If a download fails, crop the local copy instead and list that lot in the output.
- Build `site/img/wall.webp`: a 21 by 21 sheet of 64 px square crops, most expensive first. Add a sheet position field to each lot.

**Check:** 441 files in each folder, and the total size of `site/` is printed. View a sample of 12 images and report any that do not have a white background, because multiply will not suit them.

### 3. Build Overview and Collection

Skills: `interfaces:build-design`, `interfaces:better-layout`, `interfaces:better-typography`, `interfaces:better-colors`.

- **Overview:** copy the hero and key figures from the mock-up. Add a short block on the one lot that sold below estimate.
- **Collection:** grid of thumbnails with title, sold price and multiple.
  - Search matches plain text. A search for `(` must work, because it crashes the old app.
  - Sort: highest price (default), highest multiple, lowest price, title.
  - Category buttons with counts.
  - Price bands: under $2,500 (51 lots), $2,500 to $5,000 (153), $5,000 to $10,000 (129), $10,000 to $25,000 (82), over $25,000 (26).
  - One summary line with the result count and a Reset button. One message for no results.
- **URL filters:** keep filter state in the query string with `URLSearchParams`. Reloading or sharing the link restores the view. Ignore unknown values.
- Lazy-load thumbnails. Give every image alt text from the lot title.
- Add page titles, a meta description and an `og:image`.

**Check:** run a local server with `.venv/bin/python -m http.server --directory site`, then use `playwright-cli` to test search, each filter, Reset, a reload on a filtered URL, and no console errors.

### 4. Build the wall and Guess the price

Skill: `dataviz`.

- **Wall on Overview:** take positions, scales, guide lines and tile animation from the mock-up. Replace the sheet URL. Keep 32 columns by 14 rows on desktop. Under 700 px wide, use 21 by 21 and a square chart.
- Selecting a tile shows its title, estimate, sold price and multiple, with a link to its lot detail.
- Tiles stay out of the tab order. Add a visible link to Collection as the accessible route to the same lots.
- `prefers-reduced-motion` turns the animation off.
- **Guess the price on Overview:** use the 5 lots, the 4 bands and the reveal text from the mock-up. Add a share button for the final score with `navigator.share`, falling back to the clipboard.

**Check:** with `playwright-cli`, toggle the wall both ways, select a tile, and play one full round including Play again. Confirm 441 tiles and a correct score. Take desktop and 375 px screenshots and look at them.

### 5. Build lot detail, Library and About

Skills: `odimi-voice`, `design:ux-copy`.

- **Lot detail:** native `<dialog>` on Collection, opened from `?lot=<id>` so it can be shared. Show the large image, estimate, sold price, multiple, and a link to the Julien's listing. Closing it restores the filtered URL.
- **Library:** count everything from `data/books.json`. Search, category buttons, and a list with title, author and a link to the lot. Show unknown authors honestly.
- **About:** carry over the reflection, project notes, creator block and photos from `about.py` and `assets/`. Credit Julien's Auctions as the data and image source. State that the site is independent and not affiliated.
- Edit the prose with `odimi-voice`: British spelling, no em dashes, no invented claims.

**STOP:** show Hassan the edited About text and all new page copy. Apply changes, then continue.

**Check:** with `playwright-cli`, open a `?lot=` URL directly, close the dialog, search the Library, and confirm the Library counts match the facts above.

### 6. Check quality

Skills: `interfaces:better-accessibility`, `design:accessibility-review`, `interfaces:better-interface`.

- Keyboard only: every control can be reached and has a visible focus ring. The dialog traps and returns focus.
- Contrast at 4.5:1 or better for text.
- 375 px, 768 px and 1440 px widths have no sideways page scroll.
- Fix what you find. List anything you leave and why.

**Check:** report results per item, with screenshots at each width. Do not claim a screen reader pass unless you ran one.

### 7. Review the code

Skills: `ponytail:ponytail-review`, `code-review`.

Remove dead code and fix real findings.

**Check:** step 1 tests still pass and step 3 to 5 browser checks still pass.

### 8. Clean the repo

Skills: `ponytail:ponytail-audit`, `caveman-commit`.

**STOP first:** ask Hassan three things.

1. What should happen to the uncommitted `requirements.txt`? The site only needs Pillow, for `build_images.py`.
2. Which licence, if any? The repo has none. The images and data belong to others, so any licence should cover the code only.
3. OK to remove the Streamlit files now? This stays local until Hassan pushes.

Then:

- Tag `streamlit-v1` at the last commit that still has the Streamlit app, locally only.
- `git rm` `main_dashboard.py`, `data_processing.py`, `visualizations.py`, `ui_components.py`, `books_tab.py`, `theme_utils.py`, `about.py`.
- `git mv` both source JSON files into `data/`, and update the script paths.
- Keep `archived_auction_data/` and the notebook.
- Add `.venv/` to `.gitignore`.
- Rewrite `README.md` in plain language: what the site shows, the main finding, the live link, how to rebuild the data, how to run it locally, how to deploy, and the source credit. Use `odimi-voice`. The current README names a file that does not exist.

**Check:** a fresh `build_data.py` run and its tests pass, and `git status` shows only the items Hassan chose to leave.

### 9. Go live

Skill: `verify-and-stop`. No Cloudflare skill is installed, so use Wrangler through `npx`.

**STOP first:** ask Hassan to confirm the project name and approve publishing. Hassan must run the login. Never handle a Cloudflare token or password.

```bash
npx wrangler login
```

```bash
npx wrangler pages project create david-lynch-collection --production-branch main
```

```bash
npx wrangler pages deploy site --project-name david-lynch-collection --branch main
```

Check the `pages.dev` address first. Then Hassan does these in order:

1. In the Cloudflare dashboard, open the Pages project, then Custom domains, and add `lynch.hassan-odimi.se`. Do this before adding DNS.
2. At the domain's DNS provider, add the CNAME that Cloudflare shows.
3. After the live check passes, push the branch and merge it to `main`. The Streamlit Cloud app stops working at that point.
4. Delete or archive the Streamlit Cloud app, and set the GitHub repo's description and homepage.

**Check:** on the real address, load all 4 pages on desktop and phone width, test a shared filter link and a `?lot=` link, confirm images load from the site itself, and confirm no console errors.

## Done means

- All 4 pages, the wall, the game and lot detail work at the live address.
- All checks above have reported results.
- `main` holds only the site, scripts, data, archive, notebook and README.
- Anything skipped or unverified is listed for Hassan.
