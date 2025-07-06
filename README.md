# David Lynch Collection Dashboard

An interactive Streamlit dashboard for exploring and analyzing data from the David Lynch Collection auction.

## Project Structure

```
lynch_dashboard/
├── lynch_dashboard.py      # Main application file
├── data_processing.py      # Data loading and processing functions
├── visualizations.py       # Chart and visualization functions
├── ui_components.py        # UI components and table configurations
├── about.py               # About page content and layout
├── requirements.txt       # Python dependencies
├── David Lynch Collection Data.json  # Source data file
└── assets/               # Images and static assets
    └── (your image files)
```

## Module Overview

### `data_processing.py`
- **Purpose**: Handles all data loading, cleaning, and processing operations
- **Key Functions**:
  - `load_data()`: Loads and processes JSON data with caching
  - `detect_category()`: Automatically categorizes items based on title keywords
  - `get_filtered_data()`: Applies user filters to the dataset
  - `calculate_summary_stats()`: Computes statistical summaries

### `visualizations.py`
- **Purpose**: Creates all charts and visual components
- **Key Functions**:
  - `create_treemap()`: Hierarchical treemap visualization
  - `create_scatter_plot()`: Price comparison scatter plot
  - `create_horizontal_bar_chart()`: Top/bottom items bar charts
  - `create_dumbbell_chart()`: Estimate vs actual price comparison
  - `show_item_gallery()`: Visual gallery of top items

### `ui_components.py`
- **Purpose**: Manages user interface components and interactions
- **Key Functions**:
  - `create_sidebar_filters()`: Category and keyword filtering
  - `create_data_table()`: Interactive AgGrid table with custom formatting
  - `create_summary_display()`: Statistical summary display
  - `create_download_buttons()`: CSV/HTML export functionality

### `about.py`
- **Purpose**: Contains the About page content and styling
- **Features**: Project description, personal information, and custom CSS

## Key Benefits of This Structure

1. **Modularity**: Each module has a single, clear responsibility
2. **Reusability**: Functions can be easily reused or modified
3. **Maintainability**: Changes to one aspect don't affect others
4. **Testability**: Individual functions can be tested in isolation
5. **Readability**: Clean imports and logical organization

## Running the Dashboard

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the dashboard:
   ```bash
   streamlit run lynch_dashboard.py
   ```

## Data Requirements

The dashboard expects a JSON file named `David Lynch Collection Data.json` with the following structure:

```json
[
  {
    "Title": "Item title",
    "Sold Price": "$1,000",
    "Estimated Price": "$800-1,200",
    "Item URL": "https://...",
    "Item Image": "https://..."
  }
]
```

## Future Enhancements

With this modular structure, you can easily:
- Add new visualization types by extending `visualizations.py`
- Implement additional filters in `ui_components.py`
- Add data export formats in `ui_components.py`
- Create new analysis functions in `data_processing.py`
- Integrate with different data sources by modifying `data_processing.py`

## Design Philosophy

This refactored structure follows the principle of **separation of concerns**, where each module focuses on a specific aspect of the application. This makes the codebase more professional, maintainable, and easier to extend while keeping the core functionality intact.