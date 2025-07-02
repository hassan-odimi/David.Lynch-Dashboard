import json
import pandas as pd
import matplotlib.pyplot as plt

# --- Load the JSON file ---
# Replace the file path with your local file path if needed
with open("David Lynch Collection Data.json", encoding="utf-8") as f:
    data = json.load(f)

# --- Parse data ---
sold_prices = []
estimated_low = []
estimated_high = []
titles = []
urls = []

for item in data:
    sold = int(item["Sold Price"].replace("$", "").replace(",", "").strip())
    est_range = item["Estimated Price"].replace("$", "").replace(",", "").strip()
    if "-" in est_range:
        est_low, est_high = est_range.split("-")
        est_low = int(est_low.strip())
        est_high = int(est_high.strip())
    else:
        est_low = est_high = int(est_range.strip())

    sold_prices.append(sold)
    estimated_low.append(est_low)
    estimated_high.append(est_high)
    titles.append(item["Title"])
    urls.append(item["Item URL"])

# --- Create DataFrame ---
df = pd.DataFrame({
    "Title": titles,
    "Sold Price": sold_prices,
    "Estimated Low": estimated_low,
    "Estimated High": estimated_high,
    "URL": urls
})

# --- Calculate totals ---
total_sold = df["Sold Price"].sum()
total_est_low = df["Estimated Low"].sum()
total_est_high = df["Estimated High"].sum()
average_price = df["Sold Price"].mean()
most_expensive = df.loc[df["Sold Price"].idxmax()]
cheapest = df.loc[df["Sold Price"].idxmin()]

print(f"Total Sold Price: ${total_sold:,}")
print(f"Total Estimated Low: ${total_est_low:,}")
print(f"Total Estimated High: ${total_est_high:,}")
print(f"Average Sold Price: ${average_price:,.2f}")
print("\nMost Expensive Item:")
print(most_expensive)
print("\nCheapest Item:")
print(cheapest)

# --- Plots ---
plt.figure(figsize=(12, 6))
plt.hist(df["Sold Price"], bins=30, color="skyblue", edgecolor="black")
plt.title("Distribution of Sold Prices")
plt.xlabel("Sold Price ($)")
plt.ylabel("Number of Items")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 4))
plt.boxplot(df["Sold Price"], vert=False, patch_artist=True, boxprops=dict(facecolor="lightgreen"))
plt.title("Boxplot of Sold Prices")
plt.xlabel("Sold Price ($)")
plt.tight_layout()
plt.show()

plt.figure(figsize=(10, 6))
plt.scatter(df["Estimated Low"], df["Sold Price"], alpha=0.7, label="Low Estimate", color="orange")
plt.scatter(df["Estimated High"], df["Sold Price"], alpha=0.7, label="High Estimate", color="green")
plt.title("Estimated Price vs Sold Price")
plt.xlabel("Estimated Price ($)")
plt.ylabel("Sold Price ($)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()

