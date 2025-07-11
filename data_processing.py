"""
Data Processing Module for David Lynch Collection Dashboard
Handles data loading, cleaning, and category detection
"""

import json
import pandas as pd
import numpy as np
import streamlit as st


@st.cache_data
def load_data():
    """
    Load and process the David Lynch Collection data from JSON file.
    Returns a pandas DataFrame with processed pricing and category information.
    """
    with open("David Lynch Collection Data.json", encoding="utf-8") as f:
        data = json.load(f)

    # Initialize lists to store processed data
    sold_prices, estimated_low, estimated_high, estimated_avg = [], [], [], []
    estimated_price_raw, titles, urls, images = [], [], [], []

    # Process each item in the dataset
    for item in data:
        # Clean and convert sold price to integer
        sold = int(item["Sold Price"].replace("$", "").replace(",", "").strip())
        
        # Process estimated price range
        est_range = item["Estimated Price"].replace("$", "").replace(",", "").strip()
        if "-" in est_range:
            est_low, est_high = est_range.split("-")
            est_low, est_high = int(est_low.strip()), int(est_high.strip())
            est_avg = (est_low + est_high) / 2
        else:
            est_low = est_high = est_avg = int(est_range.strip())

        # Append processed values to lists
        sold_prices.append(sold)
        estimated_low.append(est_low)
        estimated_high.append(est_high)
        estimated_avg.append(est_avg)
        estimated_price_raw.append(item["Estimated Price"])
        titles.append(item["Title"])
        urls.append(item["Item URL"])
        images.append(item["Item Image"])

    # Create DataFrame with all processed data
    df = pd.DataFrame({
        "Title": titles,
        "Sold Price": sold_prices,
        "Estimated Low": estimated_low,
        "Estimated High": estimated_high,
        "Estimate Avg": estimated_avg,
        "Estimated Price": estimated_price_raw,
        "URL": urls,
        "Image": images
    })
    
    # Add category classification
    df["Category"] = df["Title"].apply(detect_category)
    
    # Add log transformation for visualization purposes
    df["Log Sold Price"] = np.log10(df["Sold Price"] + 1)
    
    return df


def detect_category(title):
    """
    Automatically categorize items based on keywords in their titles.
    This function uses pattern matching to classify David Lynch collection items.
    
    Args:
        title (str): The title of the auction item
        
    Returns:
        str: The detected category name
    """
    title = title.lower()
    
    # Define category keywords - organized by most specific to general
    category_keywords = {
        "Scripts & Screenplays": ["script", "screenplay"],
        "Cameras & Camcorders": ["camera", "camcorder"],
        "Lighting Equipment": ["light", "lighting"],
        "Books & Reference": ["book", "volume", "reference"],
        "Posters & Prints": ["poster", "signed poster"],
        "Furniture": ["sofa", "chair", "table", "furniture"],
        "Coffee & Kitchen": ["mug", "cup", "coffee maker", "espresso"],
        "Instruments & Audio": ["guitar", "bass", "keyboard", "drum", "microphone", "audio", "speaker"],
        "Records & Music": ["record", "album", "vinyl"],
        "Props & Memorabilia": ["prop", "memorabilia", "production slate"]
    }
    
    # Check each category for matching keywords
    for category, keywords in category_keywords.items():
        if any(keyword in title for keyword in keywords):
            return category
    
    # Default category if no matches found
    return "Other"


@st.cache_data
def get_filtered_data(df, selected_categories, keyword="", price_filter=None):
    """
    Filter the DataFrame based on selected categories, keyword search, and price range.
    Now with caching for better performance.
    """
    # Convert lists to tuples for hashing
    selected_categories = tuple(sorted(selected_categories))
    
    # Filter by categories
    filtered_df = df[df["Category"].isin(selected_categories)]
    
    # Apply keyword filter if provided
    if keyword:
        filtered_df = filtered_df[
            filtered_df["Title"].str.contains(keyword, case=False, na=False)
        ]
    
    # Apply price filter if provided
    if price_filter:
        min_price, max_price = price_filter
        filtered_df = filtered_df[
            (filtered_df["Sold Price"] >= min_price) & 
            (filtered_df["Sold Price"] <= max_price)
        ]
    
    return filtered_df


@st.cache_data
def calculate_summary_stats(df):
    """
    Calculate summary statistics for the filtered dataset.
    Now cached for better performance.
    """
    # Convert DataFrame to a hashable representation
    df_hash = hash(str(df.values.tobytes()))
    
    if df.empty:
        return {
            "total_items": 0,
            "total_value": 0,
            "average_price": 0,
            "min_price": 0,
            "max_price": 0,
            "most_expensive": None,
            "cheapest": None,
            "most_common_category": "N/A"
        }
    
    stats = {
        "total_items": df.shape[0],
        "total_value": df["Sold Price"].sum(),
        "average_price": df["Sold Price"].mean(),
        "min_price": df["Sold Price"].min(),
        "max_price": df["Sold Price"].max(),
        "most_expensive": df.loc[df["Sold Price"].idxmax()],
        "cheapest": df.loc[df["Sold Price"].idxmin()],
        "most_common_category": df["Category"].value_counts().idxmax()
    }
    
    return stats
