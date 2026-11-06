"""Build site/data/lots.json and site/data/books.json from the source JSON files."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOTS_SOURCE = ROOT / "data" / "David Lynch Collection Data.json"
BOOKS_SOURCE = ROOT / "data" / "David Lynch Collection - Books.json"
OUT = ROOT / "site" / "data"

# First match wins, so order matters: specific phrases come before the broad
# word lists, and tools come before instruments ("Drum Sander" is a sander).
RULES = [
    ("Scripts & Papers", r"\b(scripts?|screenplays?|treatments?|storyboards?|notes?|notebooks?|manuscripts?|presentations?|letters?|contracts?|call sheets?)\b"),
    ("Memorabilia", r"\b(memorabilia|props?|ephemera|scrapbook|transcendental meditation items|premiere briefcase|window card|record label|sheriff department|production office vintage telephone)\b"),
    ("Art & Prints", r"\bmonoprints?\b"),
    ("Books & Magazines", r"\b(books?|magazines?|periodicals|volumes?|encyclop\w+|dictionar\w+|comics?|issues|proof print)\b"),
    ("Cameras & Film Gear", r"\b35mm print|\b(cameras?|c-stands?|fog machine|megaphones?|hasselblad|moviola|vcr|blu-?rays?|laserdisc|dvds?|vhs|tv|capture and playback|walkie talkies|film tools|light meters?)\b"),
    ("Clothing & Personal", r"\b(caps?|neckties|wingtips|socks|cuff links|jewelry|canes|hats?|ring|sunglasses|reading glasses|shirts?|t-shirts?|jackets?|suits?|shoes|clothing|apparel|aprons?|cigar tube)\b"),
    ("Lamps & Lighting", r"\b(jtl everlight|lighting|lamps?|lights?|light kit|chandeliers?|sconces?)\b"),
    ("Furniture & Rugs", r"\b(coffee table|art studio chair|dinette|patio furniture|podium|telephone stand|old stand)\b"),
    ("Coffee & Kitchen", r"(?<!license )\b(mugs?|cups?|teacups?|saucers?|coffee|espresso|grinders?|bowls?|plates?|platters?|dishes|glassware|spoons|brilliantware|belleek|creamer|tableware|kitchen|cookware|knives|barware|kitchenware|pots?|pans?|teapots?|blender|toaster|refrigerator|microwave)\b"),
    ("Workshop & Tools", r"\b(saws?|sanders?|drills?|lathes?|routers?|planers?|jointers?|clamps?|tools?|workbench\w*|vacuum|compressors?|welders?|vises?|hammers?|wrench\w*|ladders?|sawhorses?|shapers?|nailers?|chisels?|paint|brushes|easels?|woodshop|shop tables|pedestal roller|shaping mold|art supplies|home art studio)\b"),
    ("Music & Audio", r"\b(guitars?|bass|keyboards?|drums?|microphones?|mics?|speakers?|amps?|amplifiers?|mixers?|synth\w*|trumpet|cornet|saxophone|violin|piano|records?|vinyl|albums?|turntables?|stereo|audio|headphones?|pedals?|sampl\w+|recorders?|receivers?|cds?|harmonicas?|ukulele|banjo|mandolin|flute|lap steel|theremin|kalimba|rain stick|vocal producer|war sangam|evolution mk-225)\b"),
    ("Art & Prints", r"\b(paintings?|prints?|lithographs?|sculptures?|woodblock|drawings?|photographs?|photos?|posters?|artworks?|canvas|portrait|etchings?|serigraphs?|collage|art)\b"),
    ("Cameras & Film Gear", r"\b(camcorders?|lens(es)?|tripods?|polaroids?|35mm|16mm|film|bolex|arri|light meters?|slate|monitors?|projectors?|clapper|dolly|editing)\b"),
    ("Furniture & Rugs", r"\b(sofas?|chairs?|tables?|desks?|stools?|benches|bench|cabinets?|shelves|shelving|dressers?|beds?|rugs?|carpets?|credenzas?|ottomans?|armchairs?|lounge|sideboards?|couch|bookcases?|nightstands?|mirrors?|screens?)\b"),
]
OTHER = "Household & Other"

# "Photo Matched" describes a lot's provenance, not what the lot is.
PROVENANCE = re.compile(r"\b(photo|screen)[- ]matched\b")


def category(title):
    text = PROVENANCE.sub("", title.lower())
    return next((name for name, rule in RULES if re.search(rule, text)), OTHER)


def dollars(text):
    return int(re.sub(r"\D", "", text))


def item_number(url):
    return re.search(r"/items/(\d+)", url).group(1)


def build_lots(source):
    lots = []
    for item in source:
        low, high = (dollars(part) for part in item["Estimated Price"].split("-"))
        sold = dollars(item["Sold Price"])
        lots.append({
            "id": item["Item ID"],
            "title": item["Title"],
            "low": low,
            "high": high,
            "sold": sold,
            "multiple": round(sold / ((low + high) / 2), 1),
            "category": category(item["Title"]),
            "url": item["Item URL"],
        })
    lots.sort(key=lambda lot: (-lot["sold"], int(lot["id"])))
    for position, lot in enumerate(lots):
        lot["sheet"] = position  # tile position in img/wall.webp, most expensive first
    return lots


def build_books(source, lots):
    # The two sources spell some URLs differently, so match on the item number.
    ids = {item_number(lot["url"]): lot["id"] for lot in lots}
    return [{
        "title": lot["lot_title"],
        "category": lot["category"],
        "lot": ids[item_number(lot["url"])],
        "books": [{"title": book["title"], "author": book["author"]} for book in lot["books"]],
    } for lot in source["lots"]]


def write(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lots = build_lots(json.loads(LOTS_SOURCE.read_text(encoding="utf-8")))
    write("lots.json", lots)
    write("books.json", build_books(json.loads(BOOKS_SOURCE.read_text(encoding="utf-8")), lots))


if __name__ == "__main__":
    main()
