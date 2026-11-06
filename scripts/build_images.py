"""Download lot images into site/img and build the wall sheet. Rerun to fill gaps."""
import io
import json
import time
import urllib.parse
import urllib.request

from PIL import Image, ImageChops, ImageOps

import build_data

ROOT = build_data.ROOT
IMG = ROOT / "site" / "img"
LOCAL = ROOT / "archived_auction_data" / "items_images"
SHEET_COLUMNS = 21
TILE = 64


def sized_url(url):
    parts = urllib.parse.urlsplit(url)
    query = dict(urllib.parse.parse_qsl(parts.query), width="1200")
    return parts._replace(query=urllib.parse.urlencode(query)).geturl()


def download(url):
    request = urllib.request.Request(sized_url(url), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        image = Image.open(io.BytesIO(response.read()))
        image.load()  # open() is lazy; surface a corrupt download here
        return image


def local_copy(lot_id):
    """Fallback: the archived copies have dark bars baked in, so crop to the bright area."""
    image = Image.open(LOCAL / f"{lot_id}.jpg").convert("RGB")
    return image.crop(image.convert("L").point(lambda v: 255 if v > 40 else 0).getbbox())


def on_white(image):
    image = image.convert("RGBA")
    return Image.alpha_composite(Image.new("RGBA", image.size, "white"), image).convert("RGB")


def save(image, path, size):
    copy = image.copy()
    copy.thumbnail((size, size))
    copy.save(path, "WEBP", quality=80, method=6)


def build_wall(lots):
    side = SHEET_COLUMNS * TILE
    sheet = Image.new("RGB", (side, side), "white")
    for lot in lots:
        tile = ImageOps.fit(Image.open(IMG / "thumbs" / f"{lot['id']}.webp"), (TILE, TILE))
        row, column = divmod(lot["sheet"], SHEET_COLUMNS)
        sheet.paste(tile, (column * TILE, row * TILE))
    sheet.save(IMG / "wall.webp", "WEBP", quality=75, method=6)


def build_share():
    """JPEG link preview, because some apps do not show WebP."""
    canvas = Image.new("RGB", (1200, 630), "#F4F0E7")
    lot = ImageOps.contain(Image.open(IMG / "lots" / "15.webp").convert("RGB"), (1120, 570))
    left, top = (1200 - lot.width) // 2, (630 - lot.height) // 2
    box = (left, top, left + lot.width, top + lot.height)
    canvas.paste(ImageChops.multiply(canvas.crop(box), lot), box)
    canvas.save(IMG / "share.jpg", "JPEG", quality=85)


def main():
    (IMG / "lots").mkdir(parents=True, exist_ok=True)
    (IMG / "thumbs").mkdir(parents=True, exist_ok=True)
    source = json.loads(build_data.LOTS_SOURCE.read_text(encoding="utf-8"))
    failed = []
    for item in source:
        lot_id = item["Item ID"]
        large, thumb = IMG / "lots" / f"{lot_id}.webp", IMG / "thumbs" / f"{lot_id}.webp"
        if large.exists() and thumb.exists():
            continue
        try:
            image = download(item["Item Image"])
            time.sleep(0.2)
        except OSError as error:
            failed.append(f"{lot_id} {item['Title']}: {error}")
            image = local_copy(lot_id)
        image = on_white(image)
        save(image, large, 1200)
        save(image, thumb, 400)

    build_wall(json.loads((build_data.OUT / "lots.json").read_text(encoding="utf-8")))
    build_share()
    print(f"{len(failed)} lots used the local copy")
    print("\n".join(failed))


if __name__ == "__main__":
    main()
