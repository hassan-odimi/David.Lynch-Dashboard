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

# Claims in the finale chart
scripts = [lot for lot in lots if lot["category"] == "Scripts & Papers"]
assert len(scripts) == 11
assert 0.18 < sum(lot["sold"] for lot in scripts) / sum(lot["sold"] for lot in lots) < 0.2
midpoint = lambda lot: (lot["low"] + lot["high"]) / 2
bands = [[lot["multiple"] for lot in lots if low <= midpoint(lot) < high]
         for low, high in ((0, 300), (300, 600), (600, 1000), (1000, 2000), (2000, 5000), (5000, float("inf")))]
medians = [statistics.median(band) for band in bands]
assert medians == sorted(medians, reverse=True) and medians[0] > 20 and medians[-1] < 4

# Claims in the story chapters
import re
sale_total = sum(lot["sold"] for lot in lots)
in_category = lambda *names: [lot for lot in lots if lot["category"] in names]
typical = lambda group: statistics.median(lot["multiple"] for lot in group)
total = lambda group: sum(lot["sold"] for lot in group)
assert total(scripts) == 792_025 and round(total(scripts) / sale_total * 100) == 19 and len(scripts) / len(lots) < 0.03
cameras = in_category("Cameras & Film Gear")
assert len(cameras) == 41 and total(cameras) == 405_600
assert round(typical(in_category("Cameras & Film Gear", "Memorabilia"))) == 21
art = in_category("Art & Prints")
assert len(art) == 42 and round(typical(art)) == 31
built = in_category("Workshop & Tools", "Furniture & Rugs", "Lamps & Lighting")
handmade = [lot for lot in built if re.search("homemade|handmade|made by lynch", lot["title"], re.I)]
others = [lot for lot in built if lot not in handmade]
assert len(built) == 104 and len(handmade) == 9 and len(others) == 95
assert round(typical(handmade)) == 23 and round(typical(others)) == 10
assert below in built
guitars = [lot for lot in in_category("Music & Audio") if re.search("guitar|bass", lot["title"], re.I)]
assert len(guitars) == 22 and total(guitars) == 214_825 and round(typical(guitars)) == 15
reading = in_category("Books & Magazines")
signed = [lot for lot in reading if re.search("signed|inscribed", lot["title"], re.I)]
assert round(total(reading) / sale_total * 100) == 9 and len(signed) == 10
assert round(typical(signed)) == 6 and round(typical([lot for lot in reading if lot not in signed])) == 16
chapter_lots = {"15": 195_000, "124": 52_000, "216": 32_500, "213": 35_750, "76": 39_000, "123": 13_000}
assert all(next(lot for lot in lots if lot["id"] == lot_id)["sold"] == sold for lot_id, sold in chapter_lots.items())
assert sum(chapter_lots.values()) == 367_250

print("all checks passed")
