def get_current_theme_colors():
    """Get current theme colors using the theme manager."""
    try:
        theme_name = theme_manager.get_current_theme()
        colors = theme_manager.themes[theme_name]['colors']
        return colors, theme_name
    except:
        # Simple fallback
        return {
            'background': '#1f2937',
            'text': '#f9fafb',
            'border': '#374151'
        }, 'dark'


"""
Books Tab Module for David Lynch Collection Dashboard
Creates "The Lynch Library" with book catalog, author network, and reading map
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import urllib.parse
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
from typing import Dict, List, Any
try:
    from theme_utils import theme_manager
    THEME_MANAGER_AVAILABLE = True
except ImportError:
    THEME_MANAGER_AVAILABLE = False
    # Fallback theme colors
    DEFAULT_COLORS = {
        'background': '#0e1117',
        'text': '#fafafa', 
        'border': '#262730'
    }


@st.cache_data
def load_books_data() -> Dict[str, Any]:
    """Load the David Lynch Books Collection JSON data with caching."""
    try:
        with st.spinner("Loading books collection..."):
            with open("David Lynch Collection - Books.json", "r", encoding="utf-8") as f:
                return json.load(f)
    except FileNotFoundError:
        st.error("Books data file 'David Lynch Collection - Books.json' not found. Please check the file path.")
        return {"collection_metadata": {}, "lots": []}
    except json.JSONDecodeError:
        st.error("Invalid JSON format in books data file.")
        return {"collection_metadata": {}, "lots": []}


@st.cache_data
def extract_books_dataframe(books_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract individual books from lots into a flat DataFrame with caching."""
    books_list = []
    
    for lot in books_data.get("lots", []):
        lot_title = lot.get("lot_title", "Unknown Lot")
        lot_url = lot.get("url", "")
        lot_category = lot.get("category", "Unknown")
        
        for book in lot.get("books", []):
            books_list.append({
                "book_title": book.get("title", "Unknown Title"),
                "author": book.get("author", "Unknown Author"),
                "category": lot_category,
                "book_type": book.get("type", ""),
                "lot_title": lot_title,
                "lot_url": lot_url,
                "notes": book.get("notes", "")
            })
    
    return pd.DataFrame(books_list)


def create_simple_search_links(book_title: str, author: str) -> str:
    """Create simplified search links for finding books online."""
    
    # Clean titles and authors
    clean_title = book_title.replace('"', '').strip()
    clean_author = author.replace('"', '').strip()
    
    # Skip very generic or incomplete entries
    if (
        len(clean_title) < 3 or 
        clean_title.lower() in ["unknown", "various", "books", "collection"] or
        any(term in clean_title.lower() for term in ["lot of", "group", "volumes", "works by"])
    ):
        return "—"
    
    # URL encode search terms
    title_encoded = urllib.parse.quote(clean_title)
    author_encoded = urllib.parse.quote(clean_author) if clean_author.lower() not in ["unknown", "various"] else ""
    
    # Create combined search term
    if author_encoded:
        search_term = f"{clean_title} {clean_author}"
    else:
        search_term = clean_title
    
    combined_encoded = urllib.parse.quote(search_term)
    
    # Create search URLs
    google_books = f"https://www.google.com/search?tbm=bks&q={combined_encoded}"
    amazon = f"https://www.amazon.com/s?k={combined_encoded}&i=stripbooks"
    
    # Simplified, more compact link display
    return f"""
    <div style="display: flex; gap: 6px; width: 100%;">
        <a href="{google_books}" target="_blank" style="
            color: #ff4b4b; 
            text-decoration: none;
            font-size: 11px;
            padding: 3px 6px;
            border: 1px solid #ff4b4b;
            border-radius: 4px;
            display: inline-block;
            white-space: nowrap;
            background: rgba(255, 75, 75, 0.1);
        ">📚 Books</a>
        <a href="{amazon}" target="_blank" style="
            color: #ff9500; 
            text-decoration: none;
            font-size: 11px;
            padding: 3px 6px;
            border: 1px solid #ff9500;
            border-radius: 4px;
            display: inline-block;
            white-space: nowrap;
            background: rgba(255, 149, 0, 0.1);
        ">🛒 Shop</a>
    </div>
    """


def create_book_insights(df: pd.DataFrame, books_data: Dict[str, Any]) -> None:
    """Display quick insights about the book collection."""
    
    if df.empty:
        st.warning("No books data available.")
        return
    
    # Collection metadata
    metadata = books_data.get("collection_metadata", {})
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Books", len(df))
    
    with col2:
        st.metric("Book Lots", metadata.get("total_lots", 0))
    
    with col3:
        unique_authors = df[(df["author"] != "Unknown") & (df["author"] != "Various")]["author"].nunique()
        st.metric("Unique Authors", unique_authors)
    
    with col4:
        st.metric("Categories", df["category"].nunique())
    
    # Category distribution
    st.subheader("📊 Books by Category")
    
    with st.spinner("Creating category chart..."):
        category_counts = df["category"].value_counts()
        
        # Get current theme colors (will update when theme changes)
        colors, theme_name = get_current_theme_colors()
        
        # Create category chart with proper contrast
        fig = px.bar(
            x=category_counts.values,
            y=category_counts.index,
            orientation='h',
            title="Distribution of Books by Category",
            labels={"x": "Number of Books", "y": "Category"}
        )
        
        # Apply theme colors with excellent contrast
        fig.update_layout(
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font=dict(color=colors['text'], family="Arial, sans-serif"),
            showlegend=False,
            height=450,
            margin=dict(l=20, r=20, t=50, b=20),
            title=dict(
                text="Distribution of Books by Category",
                font=dict(color=colors['text'], size=18, family="Arial, sans-serif"),
                x=0.5,
                y=0.95
            )
        )
        
        # Use theme-appropriate bar color with good contrast
        bar_color = '#dc2626' if theme_name == 'light' else '#f87171'
        
        fig.update_traces(
            marker_color=bar_color,
            hovertemplate='<b>%{y}</b><br>Books: %{x}<extra></extra>',
            marker_line=dict(color=colors['border'], width=1)
        )
        
        fig.update_xaxes(
            gridcolor=colors['border'], 
            showgrid=True,
            color=colors['text'],
            title=dict(
                text="Number of Books", 
                font=dict(color=colors['text'], size=14, family="Arial, sans-serif")
            ),
            tickfont=dict(color=colors['text'], size=12)
        )
        
        fig.update_yaxes(
            gridcolor=colors['border'],
            color=colors['text'],
            title=dict(
                text="Category", 
                font=dict(color=colors['text'], size=14, family="Arial, sans-serif")
            ),
            tickfont=dict(color=colors['text'], size=12)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Top authors with better presentation
    st.subheader("✍️ Most Frequent Authors")
    
    # Filter out unknown and various authors
    books_with_known_authors = df[(df["author"] != "Unknown") & (df["author"] != "Various")].copy()
    
    if len(books_with_known_authors) > 0:
        top_known_authors = books_with_known_authors["author"].value_counts().head(10)
        
        for rank, (author_name, book_count) in enumerate(top_known_authors.items(), 1):
            col1, col2, col3 = st.columns([0.5, 4, 1])
            with col1:
                st.markdown(f"**{rank}.**")
            with col2:
                st.markdown(f"**{author_name}**")
            with col3:
                st.markdown(f"`{book_count} book{'s' if book_count > 1 else ''}`")
        
        # Show count of excluded authors
        unknown_count = len(df[df['author'] == 'Unknown'])
        various_count = len(df[df['author'] == 'Various'])
        excluded_total = unknown_count + various_count
        
        if excluded_total > 0:
            st.info(f"📝 Note: {excluded_total} books excluded ({unknown_count} unknown, {various_count} various/unspecified authors)")
    else:
        st.write("No author information available.")


def create_books_table(df: pd.DataFrame, search_term: str = "", selected_category: str = "All") -> None:
    """Create AgGrid table for books with filtering and search links."""
    
    if df.empty:
        st.warning("No books to display.")
        return
    
    with st.spinner("Filtering books..."):
        # Apply filters
        filtered_df = df.copy()
        
        if search_term:
            mask = (
                filtered_df["book_title"].str.contains(search_term, case=False, na=False) |
                filtered_df["author"].str.contains(search_term, case=False, na=False) |
                filtered_df["lot_title"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]
        
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df["category"] == selected_category]
        
        if filtered_df.empty:
            st.info("No books match your search criteria.")
            return
        
        # Add search links column
        filtered_df["search_links"] = filtered_df.apply(
            lambda row: create_simple_search_links(row["book_title"], row["author"]), 
            axis=1
        )
    
    with st.spinner("Loading book table..."):
        # Apply theme CSS if available
        if THEME_MANAGER_AVAILABLE:
            try:
                st.markdown(
                    theme_manager.get_theme_css(theme_manager.get_current_theme()),
                    unsafe_allow_html=True
                )
            except:
                pass  # Silently fail if theme manager doesn't work
        
        # Prepare display DataFrame - removed book_type
        display_df = filtered_df[["book_title", "author", "category", "lot_title", "search_links", "lot_url"]].copy()
        
        # Configure grid options
        gb = GridOptionsBuilder.from_dataframe(display_df)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)
        gb.configure_side_bar()
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=False)
        
        # Grid behavior
        gb.configure_grid_options(
            enableRangeSelection=True,
            enableBrowserTooltips=True,
            enableCellTextSelection=True,
            domLayout='normal',
            rowHeight=50,
            suppressContextMenu=False
        )
        
        # Column configurations - removed book_type
        gb.configure_column("book_title", header_name="Book Title", minWidth=250, maxWidth=400, wrapText=True)
        gb.configure_column("author", header_name="Author", minWidth=150, maxWidth=250)
        gb.configure_column("category", header_name="Category", minWidth=120, maxWidth=180)
        gb.configure_column("lot_title", header_name="Lot Title", minWidth=200, maxWidth=350, wrapText=True)
        gb.configure_column("search_links", header_name="Find Book", minWidth=140, maxWidth=200, resizable=True)
        gb.configure_column("lot_url", header_name="Auction", minWidth=80, maxWidth=100)
        
        # Search links renderer
        gb.configure_column(
            "search_links",
            cellRenderer=JsCode("""
                class SearchRenderer {
                    init(params) {
                        this.eGui = document.createElement('div');
                        this.eGui.innerHTML = params.value;
                    }
                    getGui() {
                        return this.eGui;
                    }
                }
            """)
        )
        
        # URL renderer for lot links
        gb.configure_column(
            "lot_url",
            cellRenderer=JsCode("""
                class UrlRenderer {
                    init(params) {
                        this.eGui = document.createElement('a');
                        this.eGui.setAttribute('href', params.value);
                        this.eGui.setAttribute('target', '_blank');
                        this.eGui.setAttribute('title', 'View auction lot');
                        this.eGui.style.color = '#ff4b4b';
                        this.eGui.style.textDecoration = 'none';
                        this.eGui.innerHTML = '🔗 View';
                    }
                    getGui() {
                        return this.eGui;
                    }
                }
            """)
        )
        
        # Display grid with theme handling
        if THEME_MANAGER_AVAILABLE:
            try:
                aggrid_theme = theme_manager.get_aggrid_theme()
            except:
                aggrid_theme = "alpine-dark"
        else:
            aggrid_theme = "alpine-dark"
            
        AgGrid(
            display_df,
            gridOptions=gb.build(),
            enable_enterprise_modules=False,
            allow_unsafe_jscode=True,
            update_mode="NO_UPDATE",
            fit_columns_on_grid_load=True,
            theme=aggrid_theme,
            height=600
        )
    
    # Display filter results
    searchable_books = len(filtered_df[filtered_df["search_links"] != "—"])
    st.info(f"Showing {len(filtered_df)} of {len(df)} books | {searchable_books} books have search links available")


def create_author_category_flow(df: pd.DataFrame) -> None:
    """Create Sankey diagram showing flow from Categories to all book titles (including Unknown/Various authors)."""
    
    if df.empty:
        st.warning("No data available for author-category flow.")
        return
    
    with st.spinner("Creating category flow diagram..."):
        # Get theme colors for dynamic styling
        colors, theme_name = get_current_theme_colors()
        
        # Use ALL books for the Sankey diagram
        flow_df = df.copy()
        
        # Create a comprehensive Sankey: All Books → Categories
        category_counts = flow_df['category'].value_counts()
        categories = category_counts.index.tolist()
        
        # Create nodes: Root + Categories  
        all_nodes = ["Lynch's Complete Library"] + categories
        
        # Create dynamic colors based on theme with better accessibility
        if theme_name == 'dark':
            root_color = 'rgba(239, 68, 68, 1.0)'  # Bright red for dark theme
            category_base_colors = [
                'rgba(239, 68, 68, 0.9)',    # Red
                'rgba(59, 130, 246, 0.9)',   # Blue  
                'rgba(16, 185, 129, 0.9)',   # Green
                'rgba(245, 158, 11, 0.9)',   # Amber
                'rgba(139, 92, 246, 0.9)',   # Purple
                'rgba(249, 115, 22, 0.9)',   # Orange
                'rgba(236, 72, 153, 0.9)',   # Pink
                'rgba(20, 184, 166, 0.9)',   # Teal
                'rgba(132, 204, 22, 0.9)',   # Lime
                'rgba(168, 85, 247, 0.9)'    # Violet
            ]
        else:  # light theme - use darker, more saturated colors
            root_color = 'rgba(185, 28, 28, 1.0)'  # Dark red for light theme
            category_base_colors = [
                'rgba(185, 28, 28, 0.8)',    # Dark red
                'rgba(29, 78, 216, 0.8)',    # Dark blue
                'rgba(5, 150, 105, 0.8)',    # Dark green
                'rgba(217, 119, 6, 0.8)',    # Dark amber
                'rgba(109, 40, 217, 0.8)',   # Dark purple
                'rgba(234, 88, 12, 0.8)',    # Dark orange
                'rgba(190, 24, 93, 0.8)',    # Dark pink
                'rgba(13, 148, 136, 0.8)',   # Dark teal
                'rgba(101, 163, 13, 0.8)',   # Dark lime
                'rgba(124, 58, 237, 0.8)'    # Dark violet
            ]
        
        node_colors = [root_color]
        
        for i in range(len(categories)):
            node_colors.append(category_base_colors[i % len(category_base_colors)])
        
        # Create links: Root → Each category
        source_indices = [0] * len(categories)  # All from root
        target_indices = list(range(1, len(categories) + 1))  # To each category
        values = category_counts.tolist()
        
        # Create link colors with better transparency
        link_colors = []
        for i in range(len(categories)):
            base_color = category_base_colors[i % len(category_base_colors)]
            # Adjust transparency based on theme
            if theme_name == 'dark':
                link_color = base_color.replace('0.9)', '0.4)')
            else:
                link_color = base_color.replace('0.8)', '0.3)')
            link_colors.append(link_color)
        
        # Create Sankey diagram with improved styling
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=25,
                thickness=30,
                line=dict(color=colors['border'], width=2),
                label=[f"{node}<br>({category_counts.get(node, len(flow_df))} books)" 
                      if node != "Lynch's Complete Library" 
                      else f"{node}<br>({len(flow_df)} books total)" 
                      for node in all_nodes],
                color=node_colors,
                x=[0.1] + [0.9] * len(categories),
                y=[0.5] + [i/(len(categories)-1) for i in range(len(categories))],
                hovertemplate='<b>%{label}</b><extra></extra>'
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color=link_colors,
                hovertemplate='<b>%{source.label}</b> → <b>%{target.label}</b><br>%{value} books<extra></extra>'
            )
        )])
        
        # Force better font contrast for Sankey labels
        fig.update_layout(
            title=dict(
                text="Complete Book Collection Flow by Category",
                font=dict(color=colors['text'], size=20, family="Arial, sans-serif"),
                x=0.5,
                y=0.95
            ),
            font=dict(size=14, color=colors['text'], family="Arial, sans-serif"),
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            height=550,
            margin=dict(t=80, b=30, l=30, r=30)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Flow statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Categories", len(categories))
    with col2:
        st.metric("All Books", len(flow_df))
    with col3:
        largest_category = category_counts.index[0]
        largest_count = category_counts.iloc[0]
        st.metric("Largest Category", f"{largest_category} ({largest_count} books)")
    
    # Category insights
    st.markdown("### 📊 Complete Category Distribution")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top 5 Categories:**")
        for i, (category, count) in enumerate(category_counts.head(5).items(), 1):
            percentage = (count / len(flow_df)) * 100
            st.write(f"{i}. **{category}**: {count} books ({percentage:.1f}%)")
    
    with col2:
        st.write("**Collection Overview:**")
        total_books = len(flow_df)
        avg_books_per_category = total_books / len(categories)
        
        st.write(f"• **Average books per category**: {avg_books_per_category:.1f}")
        st.write(f"• **Total categories**: {len(categories)}")
        st.write(f"• **Collection diversity**: High variety across {len(categories)} subject areas")


def create_reading_map(df: pd.DataFrame) -> None:
    """Create sunburst visualization of Lynch's reading map."""
    
    if df.empty:
        st.warning("No data available for reading map.")
        return
    
    with st.spinner("Creating reading map..."):
        # Prepare hierarchical data
        hierarchy_data = []
        
        # Group by category and type
        for category in df["category"].unique():
            category_df = df[df["category"] == category]
            category_count = len(category_df)
            
            # Add category level
            hierarchy_data.append({
                "ids": category,
                "labels": f"{category}<br>({category_count} books)",
                "parents": "",
                "values": category_count
            })
            
            # Add book types within category
            for book_type in category_df["book_type"].unique():
                if book_type:  # Skip empty types
                    type_df = category_df[category_df["book_type"] == book_type]
                    type_count = len(type_df)
                    type_id = f"{category}_{book_type}"
                    
                    hierarchy_data.append({
                        "ids": type_id,
                        "labels": f"{book_type}<br>({type_count} books)",
                        "parents": category,
                        "values": type_count
                    })
        
        if not hierarchy_data:
            st.info("No hierarchical data available for reading map.")
            return
        
        # Convert to DataFrame
        hierarchy_df = pd.DataFrame(hierarchy_data)
        
        # Get theme colors for dynamic styling
        colors, theme_name = get_current_theme_colors()
        
        # Create sunburst chart with theme manager integration
        fig = go.Figure(go.Sunburst(
            ids=hierarchy_df["ids"],
            labels=hierarchy_df["labels"],
            parents=hierarchy_df["parents"],
            values=hierarchy_df["values"],
            branchvalues="total",
            hovertemplate='<b>%{label}</b><br>%{value} books<extra></extra>',
            maxdepth=2,
            insidetextorientation='radial',
            textfont=dict(
                size=12,
                color=colors['text'],
                family="Arial, sans-serif"
            ),
            # Theme-appropriate color scheme
            marker=dict(
                colors=[
                    # Light theme: darker colors for contrast
                    '#dc2626', '#1e40af', '#059669', '#d97706', '#7c2d12',
                    '#be185d', '#0891b2', '#365314', '#7c3aed', '#92400e',
                    '#b91c1c', '#1e3a8a', '#047857', '#b45309', '#581c87'
                ] if theme_name == 'light' else [
                    # Dark theme: brighter, more vibrant colors
                    '#ff6b6b', '#4dabf7', '#69db7c', '#ffd43b', '#ff8787',
                    '#ff8cc8', '#74c0fc', '#8ce99a', '#da77f2', '#ffb366',
                    '#ff9999', '#91c7ff', '#b3e5b3', '#ffe066', '#c199ff',
                    '#ffcc99', '#b3d9ff', '#ccf2cc', '#f0b3ff', '#ffe6b3'
                ],
                line=dict(color=colors['border'], width=2)
            )
        ))
        
        fig.update_layout(
            title=dict(
                text="Lynch's Reading Map - Categories and Types",
                font=dict(color=colors['text'], size=20, family="Arial, sans-serif"),
                x=0.5,
                y=0.95
            ),
            font=dict(size=13, color=colors['text'], family="Arial, sans-serif"),
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            height=650,
            margin=dict(t=80, b=30, l=30, r=30)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Reading map insights
    st.subheader("📖 Reading Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Dominant Categories:**")
        top_categories = df["category"].value_counts().head(5)
        for i, (category, count) in enumerate(top_categories.items(), 1):
            percentage = (count / len(df)) * 100
            st.write(f"{i}. {category}: {count} books ({percentage:.1f}%)")
    
    with col2:
        st.write("**Book Types Distribution:**")
        type_counts = df[df["book_type"] != ""]["book_type"].value_counts().head(5)
        for i, (book_type, count) in enumerate(type_counts.items(), 1):
            st.write(f"{i}. {book_type}: {count} books")


def show_books_tab():
    """Main function to display the Lynch Library tab."""
    
    st.header("📚 The Lynch Library")
    st.markdown("""
    *Explore David Lynch's personal book collection - from surrealist art to transcendental meditation, 
    from film theory to woodworking guides. Discover the literary influences behind his unique vision.*
    """)
    
    # Load data
    books_data = load_books_data()
    if not books_data or not books_data.get("lots"):
        st.error("Unable to load books data.")
        return
    
    # Extract books DataFrame
    df = extract_books_dataframe(books_data)
    
    if df.empty:
        st.error("No books data found in the collection.")
        return
    
    # Create sub-tabs
    tab1, tab2, tab3 = st.tabs(["📖 Book Catalog", "🌊 Category Flow", "🗺️ Reading Map"])
    
    with tab1:
        st.subheader("📊 Collection Insights")
        create_book_insights(df, books_data)
        
        st.markdown("---")
        st.subheader("📚 Book Catalog")
        
        # Filters
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_term = st.text_input(
                "Search books, authors, or lots",
                placeholder="e.g., 'Kubrick', 'surrealism', 'photography'...",
                help="Search across book titles, authors, and lot titles"
            )
        
        with col2:
            categories = ["All"] + sorted(df["category"].unique().tolist())
            selected_category = st.selectbox(
                "Filter by category",
                categories,
                help="Filter books by main category"
            )
        
        # Display table
        create_books_table(df, search_term, selected_category)
    
    with tab2:
        st.subheader("🌊 Complete Category Flow")
        st.markdown("""
        *Discover how Lynch's entire book collection flows across different subject categories. 
        This diagram includes all books, showing the complete scope of his literary interests.*
        """)
        create_author_category_flow(df)
    
    with tab3:
        st.subheader("🗺️ Lynch's Reading Map")
        st.markdown("""
        *Navigate the thematic landscape of Lynch's library. This hierarchical view shows how books 
        are organized by category and type, revealing his intellectual interests and influences.*
        """)
        create_reading_map(df)


if __name__ == "__main__":
    show_books_tab()