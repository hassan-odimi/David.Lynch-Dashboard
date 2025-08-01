import os
import json
import time
import random
import urllib.parse

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ---- SETTINGS ----
SOURCE_JSON = "David Lynch Collection Data.json"
OUTPUT_DIR = "images"
MANIFEST_JSON = "downloaded_images.json"

# ---- CREATE IMAGES DIR ----
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---- LOAD DATA ----
with open(SOURCE_JSON, "r") as f:
    data = json.load(f)

# ---- SETUP SELENIUM ----
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# Adjust driver path if needed:
service = Service("/usr/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)

manifest = []

# ---- MAIN LOOP ----
for idx, item in enumerate(data, 1):
    img_url = item.get("Item Image")
    item_id = item.get("Item ID")
    title = item.get("Title")
    sold_price = item.get("Sold Price")
    estimated_price = item.get("Estimated Price")

    # Robust filename
    parsed_url = urllib.parse.urlparse(img_url)
    path = parsed_url.path
    base_name = os.path.basename(path)

    if "." in base_name:
        ext = base_name.split(".")[-1]
    else:
        ext = "jpg"

    filename = f"{item_id}.{ext}"
    filepath = os.path.join(OUTPUT_DIR, filename)

    try:
        # Load the image URL
        driver.get(img_url)

        # Take screenshot of the rendered page (direct image)
        img_data = driver.get_screenshot_as_png()
        with open(filepath, "wb") as f:
            f.write(img_data)

        print(f"✅ Downloaded [{idx}/{len(data)}]: {filename}")

        manifest.append({
            "Item ID": item_id,
            "Filename": filename,
            "Title": title,
            "Sold Price": sold_price,
            "Estimated Price": estimated_price
        })

    except Exception as e:
        print(f"❌ Failed: {img_url} | Error: {e}")

    # Wait politely
    time.sleep(random.uniform(1.5, 3.0))

driver.quit()

# ---- SAVE MANIFEST ----
with open(MANIFEST_JSON, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"\n✅ All done. Downloaded info saved to {MANIFEST_JSON}")
