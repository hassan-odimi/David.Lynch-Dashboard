"""
UI Components Module for David Lynch Collection Dashboard
Contains reusable UI components and data table configurations
"""

import streamlit as st
import tempfile
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import contextlib
import time

@contextlib.contextmanager
def loading_spinner(text="Loading..."):
    """Context manager for showing loading spinners"""
    placeholder = st.empty()
    with placeholder.container():
        st.spinner(text)
        yield
    placeholder.empty()

def show_loading_message(message, duration=0.5):
    """Show a brief loading message"""
    with st.spinner(message):
        time.sleep(duration)


def create_sidebar_filters(df):
    """
    Create clean sidebar filters with professional UX.
    
    Args:
        df (pd.DataFrame): The main dataset
        
    Returns:
        tuple: (selected_categories, keyword) - user filter selections
    """
    # Clean header
    st.sidebar.header("Collection Filters")
    
    # Search with clear button
    st.sidebar.markdown("### Search Collection")
    
    # Initialize search in session state
    if "search_keyword" not in st.session_state:
        st.session_state.search_keyword = ""
    
    col1, col2 = st.sidebar.columns([4, 1])
    
    with col1:
        keyword = st.text_input(
            "Search by keyword in title", 
            value=st.session_state.search_keyword,
            placeholder="e.g., coffee, camera, script...",
            label_visibility="collapsed",
            key=f"search_input_{st.session_state.get('search_clear_counter', 0)}"
        )
    
    with col2:
        if st.button("Clear", use_container_width=True, type="secondary"):
            st.session_state.search_keyword = ""
            # Force the text input to update by using a unique key
            if 'search_clear_counter' not in st.session_state:
                st.session_state.search_clear_counter = 0
            st.session_state.search_clear_counter += 1
            st.rerun()
    
    # Update session state when input changes
    if keyword != st.session_state.search_keyword:
        st.session_state.search_keyword = keyword
    
    keyword = st.session_state.search_keyword
    
    st.sidebar.markdown("---")
    
    # Category filtering
    st.sidebar.markdown("### Filter by Category")
    
    categories = sorted(df["Category"].unique())
    category_counts = df["Category"].value_counts()
    
    # Initialize session state for category selection
    if "selected_categories" not in st.session_state:
        st.session_state.selected_categories = {category: True for category in categories}
    
    # Selection buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Select All", use_container_width=True):
            for category in categories:
                st.session_state.selected_categories[category] = True
            st.rerun()
    
    with col2:
        if st.button("Clear All", use_container_width=True):
            for category in categories:
                st.session_state.selected_categories[category] = False
            st.rerun()
    
    # Improved category grouping - include Props & Memorabilia in main groups
    creative_categories = ["Scripts & Screenplays", "Books & Reference", "Posters & Prints", "Props & Memorabilia"]
    equipment_categories = ["Cameras & Camcorders", "Lighting Equipment", "Instruments & Audio"]
    personal_categories = ["Coffee & Kitchen", "Records & Music", "Furniture"]
    other_categories = [cat for cat in categories if cat not in creative_categories + equipment_categories + personal_categories]
    
    # Creative & Literary items
    with st.sidebar.expander("**Creative & Literary**", expanded=True):
        for category in creative_categories:
            if category in categories:
                count = category_counts.get(category, 0)
                st.session_state.selected_categories[category] = st.checkbox(
                    f"{category} ({count})",
                    value=st.session_state.selected_categories[category],
                    key=f"category_{category}"
                )
    
    # Equipment & Technology
    with st.sidebar.expander("**Equipment & Technology**", expanded=True):
        for category in equipment_categories:
            if category in categories:
                count = category_counts.get(category, 0)
                st.session_state.selected_categories[category] = st.checkbox(
                    f"{category} ({count})",
                    value=st.session_state.selected_categories[category],
                    key=f"category_{category}"
                )
    
    # Personal & Lifestyle
    with st.sidebar.expander("**Personal & Lifestyle**", expanded=True):
        for category in personal_categories:
            if category in categories:
                count = category_counts.get(category, 0)
                st.session_state.selected_categories[category] = st.checkbox(
                    f"{category} ({count})",
                    value=st.session_state.selected_categories[category],
                    key=f"category_{category}"
                )
    
    # Other items
    if other_categories:
        with st.sidebar.expander("**Other Items**", expanded=False):
            for category in other_categories:
                count = category_counts.get(category, 0)
                st.session_state.selected_categories[category] = st.checkbox(
                    f"{category} ({count})",
                    value=st.session_state.selected_categories[category],
                    key=f"category_{category}"
                )
    
    # Get selected categories
    selected_categories = [c for c, checked in st.session_state.selected_categories.items() if checked]
    
    # Price range filter - expanded by default
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Price Range Filter")
    
    min_price = int(df["Sold Price"].min())
    max_price = int(df["Sold Price"].max())
    
    price_range = st.sidebar.slider(
        "Filter by sold price",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        format="$%d",
        help="Drag to set minimum and maximum price range"
    )
    
    if st.session_state.get('price_filter') or keyword or len([c for c, checked in st.session_state.selected_categories.items() if checked]) < len(categories):
        with st.sidebar.container():
            st.markdown("---")
            st.info("🔄 **Filters active** - Results updating...")

    # Store price filter in session state
    if price_range != (min_price, max_price):
        st.session_state.price_filter = price_range
    else:
        st.session_state.price_filter = None
    
    return selected_categories, keyword

def create_data_table(df):
    """
    Create an interactive data table using AgGrid with dynamic theming.
    
    Args:
        df (pd.DataFrame): The filtered dataset to display
        
    Returns:
        None: Displays the table directly in Streamlit
    """
    from theme_utils import theme_manager
    
    # Apply theme-responsive CSS
    current_theme = theme_manager.get_current_theme()
    theme_css = theme_manager.get_theme_css(current_theme)
    st.markdown(theme_css, unsafe_allow_html=True)
    
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
    
    # Display the grid with dynamic theme
    try:
        AgGrid(
            df_display[["Image", "Title", "Sold Price", "Estimated Price", "Estimate Avg", "Category", "Link"]],
            gridOptions=gb.build(),
            enable_enterprise_modules=False,
            allow_unsafe_jscode=True,
            update_mode="NO_UPDATE",
            fit_columns_on_grid_load=True,
            theme=theme_manager.get_aggrid_theme(),  # Dynamic theme!
            height=600,
            key="data_table_main"
        )
    except Exception as e:
        st.error(f"Table failed to load: {e}")
        # Fallback to native Streamlit dataframe
        st.dataframe(df_display[["Title", "Sold Price", "Estimated Price", "Category"]], use_container_width=True)

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
    ### Quick Insights
    
    - **Total Items:** {stats["total_items"]:,}
    - **Total Sold Value:** ${stats["total_value"]:,.0f}
    - **Average Sold Price:** ${stats["average_price"]:,.0f}
    - **Price Range:** ${stats["min_price"]:,.0f} - ${stats["max_price"]:,.0f}
    - **Most Expensive Item:** *{stats["most_expensive"]["Title"]}* (${stats["most_expensive"]["Sold Price"]:,.0f})
    - **Least Expensive Item:** *{stats["cheapest"]["Title"]}* (${stats["cheapest"]["Sold Price"]:,.0f})
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
    """Create enhanced tab navigation with better labels and icons."""
    return st.tabs([
        "📋 Browse Collection", 
        "🗺️ Collection Map", 
        "💰 Price Explorer", 
        "🔍 Key Insights", 
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
