# The David Lynch Collection

A static site that studies the 441 lots of the David Lynch Collection, sold by Julien's Auctions. It shows every lot with its estimate, sold price and multiple, and adds a library of the books in the sale, a wall of objects that turns into a chart, charts by category and estimate, and a bidding game called Guess the price.

Live site: [lynch.hassan-odimi.se](https://lynch.hassan-odimi.se)

## The main finding

The sale made $4,245,930. The median lot sold for 18.2 times the midpoint of its estimate, and 440 of 441 lots sold above their high estimate. The one exception was the Vladimir Kagan Swan Back Sofa, which sold for $6,500 against an estimate of $8,000 to $10,000. The highest price was a tie at $195,000 between the "Ronnie Rocket" and "Lost Highway" scripts, each 780 times its midpoint.

Whether sold prices include buyer's premium is not known.

## Repository

- `site/` is the whole website: plain HTML, CSS and JavaScript, with no build step.
- `scripts/` holds the data build, the image build and the data tests.
- `data/` holds the two source JSON files.
- `archived_auction_data/` and `Lynch Collection Insights.ipynb` are the original collection work.

## Rebuild the data

The scripts use Python 3. `build_data.py` needs only the standard library, and `build_images.py` needs Pillow.

```bash
python3 scripts/test_build_data.py
```

This runs `scripts/build_data.py`, which writes `site/data/`, and then checks the published figures.

To download the images again, delete `site/img/lots` and `site/img/thumbs` first, because the script skips files that already exist.

```bash
pip install -r requirements.txt
```

```bash
python3 scripts/build_images.py
```

## Run it locally

```bash
python3 -m http.server --directory site
```

Then open <http://localhost:8000>.

## Deploy

The site is hosted on Cloudflare Pages, and `site/` is the folder to publish.

```bash
npx wrangler pages deploy site --project-name david-lynch-collection --branch main
```

## Source and credit

All auction data and lot images come from [Julien's Auctions](https://www.juliensauctions.com/en/auctions/julien-s-auctions-turner-classic-movies-present-the-david-lynch-collection). This is an independent study by [Hassan Odimi](https://www.hassan-odimi.se) and is not affiliated with Julien's Auctions.

The earlier Streamlit version is kept at the git tag `streamlit-v1`.

## Licence

The code is under the MIT licence. It does not cover the data or images. See [LICENSE](LICENSE).
