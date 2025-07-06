"""
UI Components Module for David Lynch Collection Dashboard
Contains reusable UI components and data table configurations
"""

import streamlit as st
import tempfile
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode


def create_sidebar_filters(df):
    """
    Create sidebar filters for category selection and keyword search.
    
    Args:
        df (pd.DataFrame): The main dataset
        
    Returns:
        tuple: (selected_categories, keyword) - user filter selections
    """
    st.sidebar.header("Filter Data")
    categories = sorted(df["Category"].unique())
    
    # Category filter with expandable section
    with st.sidebar.expander("Filter by Category", expanded=True):
        
        # Initialize session state for category selection
        if "selected_categories" not in st.session_state:
            st.session_state.selected_categories = {category: True for category in categories}
        
        # Select/Clear all buttons
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Select All"):
                    for category in categories:
                        st.session_state.selected_categories[category] = True
            with col2:
                if st.button("❌ Clear All"):
                    for category in categories:
                        st.session_state.selected_categories[category] = False
        
        # Individual category checkboxes
        for category in categories:
            st.session_state.selected_categories[category] = st.checkbox(
                category,
                value=st.session_state.selected_categories[category],
                key=f"category_{category}"
            )
    
    # Get selected categories
    selected_categories = [c for c, checked in st.session_state.selected_categories.items() if checked]
    
    # Keyword search input
    keyword = st.sidebar.text_input("Search by keyword in title", "")
    
    return selected_categories, keyword


def create_data_table(df):
    """
    Create an interactive data table using AgGrid with custom formatting and links.
    
    Args:
        df (pd.DataFrame): The filtered dataset to display
        
    Returns:
        None: Displays the table directly in Streamlit
    """
    # Prepare display dataframe
    df_display = df.copy()
    df_display["Link"] = df_display["URL"]
    
    # Configure grid options
    gb = GridOptionsBuilder.from_dataframe(
        df_display[["Image", "Title", "Sold Price", "Estimated Price", "Estimate Avg", "Category", "Link"]]
    )
    
    # Basic grid configuration
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100)
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=False)
    
    # Grid behavior settings
    gb.configure_grid_options(
        enableRangeSelection=True,
        enableBrowserTooltips=True,
        enableCellTextSelection=True,
        domLayout='normal',
        rowHeight=140,
        suppressContextMenu=False
    )
    
    # Currency formatting for price columns
    dollar_formatter = JsCode("""
        function(params) {
            if (params.value != null) {
                return '$' + params.value.toLocaleString();
            } else {
                return '';
            }
        }
    """)
    
    # Apply formatting to price columns
    gb.configure_column("Sold Price", type=["numericColumn"], valueFormatter=dollar_formatter)
    gb.configure_column("Estimate Avg", type=["numericColumn"], valueFormatter=dollar_formatter)
    
    # Column width configuration
    gb.configure_column("Image", minWidth=120, maxWidth=150)
    gb.configure_column("Title", minWidth=250, maxWidth=450, wrapText=True, autoHeight=True)
    gb.configure_column("Sold Price", minWidth=120, maxWidth=140)
    gb.configure_column("Estimated Price", minWidth=140, maxWidth=180)
    gb.configure_column("Estimate Avg", minWidth=120, maxWidth=150)
    gb.configure_column("Category", minWidth=120, maxWidth=200)
    gb.configure_column("Link", minWidth=80, maxWidth=100)
    
    # Custom cell renderer for clickable links
    gb.configure_column(
        "Link",
        header_name="Item Link",
        cellRenderer=JsCode("""
            class UrlRenderer {
                init(params) {
                    this.eGui = document.createElement('a');
                    this.eGui.setAttribute('href', params.value);
                    this.eGui.setAttribute('target', '_blank');
                    this.eGui.setAttribute('title', 'Open item details in new tab');
                    this.eGui.style.display = 'inline-flex';
                    this.eGui.style.alignItems = 'center';
                    this.eGui.innerHTML = '🔗 Open details page';
                }
                getGui() {
                    return this.eGui;
                }
            }
        """)
    )
    
    # Custom cell renderer for clickable images
    gb.configure_column(
        "Image",
        header_name="Item Image",
        cellRenderer=JsCode("""
            class ImageRenderer {
                init(params) {
                    this.eGui = document.createElement('div');
                    this.eGui.innerHTML = `
                        <div style="
                            position: relative;
                            display: inline-block;
                            cursor: pointer;
                        ">
                            <img src="${params.value}" style="
                                width: 100px;
                                transition: transform 0.2s ease;
                                display: block;
                                margin: 0 auto;
                            "
                            onclick="window.open('${params.value}', '_blank')"
                            title="Click to view full image">
                        </div>
                    `;
                }
                getGui() {
                    return this.eGui;
                }
            }
        """)
    )
    
   # Display the grid with forced dark styling
    with st.container():
        st.markdown("""
            <style>
            div[data-testid="stAgGrid"] .ag-theme-alpine-dark {
                background-color: #1e1e1e !important;
                color: #eee !important;
            }
            </style>
        """, unsafe_allow_html=True)

        AgGrid(
            df_display[["Image", "Title", "Sold Price", "Estimated Price", "Estimate Avg", "Category", "Link"]],
            gridOptions=gb.build(),
            enable_enterprise_modules=False,
            allow_unsafe_jscode=True,
            update_mode="NO_UPDATE",
            fit_columns_on_grid_load=True,
            theme="alpine-dark",
            height=600
        )



def create_summary_display(stats):
    """
    Create a formatted summary display of collection statistics.
    
    Args:
        stats (dict): Dictionary containing calculated statistics
        
    Returns:
        None: Displays the summary directly in Streamlit
    """
    if stats["total_items"] == 0:
        st.warning("No items match the current filter criteria.")
        return
    
    # Main summary section
    st.markdown(f"""
    ### Quick Collection Insights
    
    - **Total Items:** {stats["total_items"]:,}
    - **Total Sold Value:** ${stats["total_value"]:,.0f}
    - **Average Sold Price:** ${stats["average_price"]:,.0f}
    - **Price Range:** ${stats["min_price"]:,.0f} - ${stats["max_price"]:,.0f}
    - **Most Expensive Item:** *{stats["most_expensive"]["Title"]}* (${stats["most_expensive"]["Sold Price"]:,.0f})
    - **Cheapest Item:** *{stats["cheapest"]["Title"]}* (${stats["cheapest"]["Sold Price"]:,.0f})
    - **Most Common Category:** {stats["most_common_category"]}
    """)


def create_download_buttons(df):
    """
    Create download buttons for CSV and HTML export of filtered data.
    
    Args:
        df (pd.DataFrame): The filtered dataset to export
        
    Returns:
        None: Displays download buttons directly in Streamlit
    """
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📁 Download as CSV",
            data=csv,
            file_name="lynch_collection_filtered.csv",
            mime="text/csv"
        )
    
    with col2:
        # HTML table download
        df_export = df.copy()
        df_export["Link"] = df_export["URL"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
        html_table = df_export[["Title", "Sold Price", "Estimated Price", "Estimate Avg", "Category", "Link"]].to_html(
            escape=False, index=False
        )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
            tmpfile.write(html_table.encode("utf-8"))
            tmpfile.flush()
            
            st.download_button(
                label="📄 Download as HTML",
                data=open(tmpfile.name, "rb"),
                file_name="lynch_collection_table.html",
                mime="text/html"
            )


def create_tab_navigation():
    """
    Create the main tab navigation for the dashboard.
    
    Returns:
        tuple: Streamlit tab objects for each section
    """
    return st.tabs([
        "📑 Data Table", 
        "🌳 Treemap", 
        "📈 Scatter Plot", 
        "🔍 Insights", 
        "ℹ️ About"
    ])


def display_filter_info(selected_categories, keyword, total_items, filtered_items):
    """
    Display information about current filter settings and results.
    
    Args:
        selected_categories (list): Currently selected categories
        keyword (str): Current search keyword
        total_items (int): Total items in dataset
        filtered_items (int): Items after filtering
        
    Returns:
        None: Displays filter information directly in Streamlit
    """
    if len(selected_categories) < 10 or keyword:  # Only show if filters are active
        st.info(f"""
        **Active Filters:** 
        - Categories: {', '.join(selected_categories) if selected_categories else 'None'}
        - Keyword: "{keyword}" 
        - Showing {filtered_items:,} of {total_items:,} items
        """)
