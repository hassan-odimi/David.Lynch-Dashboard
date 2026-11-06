"""Plain-assert checks on the built data. Run: .venv/bin/python scripts/test_build_data.py"""
import json
import statistics

import build_data

build_data.main()
lots = json.loads((build_data.OUT / "lots.json").read_text(encoding="utf-8"))
books = json.loads((build_data.OUT / "books.json").read_text(encoding="utf-8"))
by_title = {lot["title"]: lot for lot in lots}


def category_of(fragment):
    (lot,) = [lot for lot in lots if fragment in lot["title"]]
    return lot["category"]


# Sale figures
assert len(lots) == 441
assert len({lot["id"] for lot in lots}) == 441
assert sorted(lot["sheet"] for lot in lots) == list(range(441))
assert sum(lot["sold"] for lot in lots) == 4_245_930
assert statistics.median(lot["sold"] for lot in lots) == 5_200
exact = [lot["sold"] / ((lot["low"] + lot["high"]) / 2) for lot in lots]
assert round(statistics.median(exact), 1) == 18.2
assert round(statistics.median(lot["multiple"] for lot in lots), 1) == 18.2

# Estimates
assert sum(lot["sold"] > lot["high"] for lot in lots) == 440
(below,) = [lot for lot in lots if lot["sold"] < lot["low"]]
assert (below["title"], below["sold"], below["low"], below["high"]) == ("Vladimir Kagan Swan Back Sofa", 6_500, 8_000, 10_000)

# Highest and lowest prices
top = [lot for lot in lots if lot["sold"] == 195_000]
assert len(top) == 2 and max(lot["sold"] for lot in lots) == 195_000
assert all(lot["multiple"] == 780 for lot in top)
assert all(any(name in lot["title"] for lot in top) for name in ('"Ronnie Rocket"', '"Lost Highway"'))
assert lots[-1]["title"] == "EcoloBlue Atmospheric Water Generator" and lots[-1]["sold"] == 910

# Books: counted from the data, because the file's metadata is wrong
all_books = [book for lot in books for book in lot["books"]]
assert len(books) == 38
assert len(all_books) == 287
assert sum(book["author"] in ("Unknown", "Various") for book in all_books) == 167
assert all(lot["lot"] in {l["id"] for l in lots} for lot in books)

# Categories
assert sum(lot["category"] == build_data.OTHER for lot in lots) <= 60
assert by_title["Performax Drum Sander"]["category"] == "Workshop & Tools"
assert build_data.category("Example Belt Sander") == "Workshop & Tools"
assert build_data.category("Example Drum Kit") == "Music & Audio"
assert category_of("Prop Matchbooks") != "Books & Magazines"
assert build_data.category("Photo Matched Electric Guitar") == "Music & Audio"

# Claims in the Overview findings
scripts = [lot for lot in lots if lot["category"] == "Scripts & Papers"]
assert len(scripts) == 11
assert 0.18 < sum(lot["sold"] for lot in scripts) / sum(lot["sold"] for lot in lots) < 0.2
midpoint = lambda lot: (lot["low"] + lot["high"]) / 2
bands = [[lot["multiple"] for lot in lots if low <= midpoint(lot) < high]
         for low, high in ((0, 300), (300, 600), (600, 1000), (1000, 2000), (2000, 5000), (5000, float("inf")))]
medians = [statistics.median(band) for band in bands]
assert medians == sorted(medians, reverse=True) and medians[0] > 20 and medians[-1] < 4

print("all checks passed")
