"""
David Lynch Collection Dashboard - Main Application
Interactive Streamlit dashboard for exploring the David Lynch Collection auction data
"""

import streamlit as st
from theme_utils import theme_manager

# Import our custom modules
from data_processing import load_data, get_filtered_data, calculate_summary_stats
from visualizations import (
    create_treemap, create_scatter_plot, create_horizontal_bar_chart,
    create_dumbbell_chart, show_item_gallery
)
from ui_components import (
    create_sidebar_filters, create_data_table, create_summary_display,
    create_download_buttons, create_tab_navigation, display_filter_info
)
from about import show_about

# ----------------- Page Configuration -----------------
st.set_page_config(
    page_title="David Lynch Collection Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)
# Apply global theme styling
try:
    current_theme = theme_manager.get_current_theme()
    theme_css = theme_manager.get_theme_css(current_theme)
    st.markdown(theme_css, unsafe_allow_html=True)
except Exception:
    pass  # Fallback gracefully if theme manager fails

# Enhanced styling for better tab experience
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        border-radius: 8px 8px 0px 0px;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- Main Title and Introduction -----------------
st.title("🎬 David Lynch Collection Dashboard")
st.markdown("""
*Explore the fascinating world of David Lynch through the auction data of his personal collection.*
""")

# Add loading for data loading (after st.set_page_config())
with st.spinner("🔄 Loading David Lynch Collection data..."):
    df = load_data()

# Add loading for filter application (after getting filters)
selected_categories, keyword = create_sidebar_filters(df)

# Show loading when applying filters
if selected_categories or keyword or hasattr(st.session_state, 'price_filter'):
    with st.spinner("🔍 Applying filters..."):
        price_filter = getattr(st.session_state, 'price_filter', None)
        filtered_df = get_filtered_data(df, selected_categories, keyword, price_filter)
        stats = calculate_summary_stats(filtered_df)
else:
    filtered_df = df
    stats = calculate_summary_stats(df)

# Display filter information with loading feedback
if filtered_df.empty:
    st.warning("⚠️ No items match your current filters. Try adjusting your selection.")
else:
    display_filter_info(selected_categories, keyword, len(df), len(filtered_df))

# ----------------- Create Tab Navigation -----------------
tab1, tab2, tab3, tab4, tab5 = create_tab_navigation()

# ----------------- Data Table Tab -----------------
with tab1:
    st.header("📋 Browse Collection")
    
    with st.expander("💡 How to use this table", expanded=False):
        st.markdown("""
        - **Click column headers** to sort
        - **Use the sidebar** to filter by category or search keywords  
        - **Click item images** to view full-size
        - **Use 'Open details'** to view original auction listings
        """)
    
    if not filtered_df.empty:
        with st.spinner("📋 Loading collection table..."):
            create_summary_display(stats)
            
        st.subheader("Detailed Data Table")
        with st.spinner("🔄 Preparing interactive table..."):
            create_data_table(filtered_df)
            
        st.subheader("Export Data")
        create_download_buttons(filtered_df)
    else:
        st.warning("No items match your current filter criteria. Please adjust your filters.")

# ----------------- Treemap Tab -----------------
with tab2:
    st.header("🗺️ Collection Map")
    
    if not filtered_df.empty:
        col_info, col_chart = st.columns([1, 2])
        
        with col_info:
            st.markdown("""
            **Reading this visualisation:**
            
            🔶 **Size** = Sale price  
            🎨 **Colour** = Price intensity  
            📦 **Groups** = Categories
            
            **What to look for:**
            - Largest rectangles = highest-value items
            - Darkest colours = premium pieces
            - Category distribution patterns
            """)
        
        with col_chart:
            with st.spinner("🗺️ Generating collection map..."):
                fig_tree = create_treemap(filtered_df)
                st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.warning("No data available for the treemap with current filters.")

# ----------------- Scatter Plot Tab -----------------
with tab3:
    st.header("💰 Price Explorer")
    
    if not filtered_df.empty:
        st.markdown("""
        This scatter plot compares the estimated average price with the actual sold price 
        for each item. Items above the diagonal line sold for more than estimated, while 
        items below sold for less.
        """)
        
        with st.spinner("📈 Analyzing price patterns..."):
            fig_scatter = create_scatter_plot(filtered_df)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.markdown("""
        **How to read this chart:**
        - Points above the diagonal indicate items that sold above their estimated average
        - Points below the diagonal show items that sold below their estimated average  
        - The further from the diagonal, the greater the difference between estimate and actual sale
        """)
    else:
        st.warning("No data available for the scatter plot with current filters.")

# ----------------- Insights Tab -----------------
with tab4:
    st.header("🔍 Collection Insights")
    
    if not filtered_df.empty:
        # Quick metrics (no loading needed - fast calculation)
        col1, col2, col3 = st.columns(3)
        
        with st.spinner("📊 Calculating insights..."):
            over_estimate = filtered_df[filtered_df["Sold Price"] > filtered_df["Estimate Avg"]]
            under_estimate = filtered_df[filtered_df["Sold Price"] < filtered_df["Estimate Avg"]]
            over_percentage = (len(over_estimate) / len(filtered_df)) * 100
            avg_premium = ((over_estimate["Sold Price"] - over_estimate["Estimate Avg"]) / over_estimate["Estimate Avg"] * 100).mean() if len(over_estimate) > 0 else 0
        
        with col1:
            st.metric("Above Estimate", f"{over_percentage:.0f}%", f"{len(over_estimate)} items")
        
        with col2:
            if avg_premium > 0:
                st.metric("Average Premium", f"+{avg_premium:.0f}%")
            else:
                st.metric("Average Premium", "0%")
        
        with col3:
            highest_category = filtered_df["Category"].value_counts().idxmax()
            st.metric("Top Category", highest_category, f"{filtered_df['Category'].value_counts().iloc[0]} items")
        
        st.markdown("---")
        
        insight_tab1, insight_tab2, insight_tab3 = st.tabs(["📊 Market Performance", "🖼️ Top Items", "📈 Price Patterns"])
        
        with insight_tab1:
            st.markdown("#### Estimate vs Actual Performance")
            st.markdown("How auction estimates compared to final sale prices for the most valuable items.")
            
            with st.spinner("📊 Creating performance analysis..."):
                fig_dumbbell = create_dumbbell_chart(filtered_df, n_items=10)
                st.plotly_chart(fig_dumbbell, use_container_width=True, key="dumbbell_insights")
            
            st.markdown("#### Market Insights")
            st.markdown(f"""
            - **{over_percentage:.0f}%** of items exceeded their estimates
            - Average premium on over-performing items: **{avg_premium:.0f}%**
            - The "Lynch factor" drove significant collector interest beyond functional value
            """)
        
        with insight_tab2:
            st.markdown("#### Visual Gallery: Collection Highlights")
            st.markdown("The most valuable and distinctive pieces from the filtered selection.")
            
            with st.spinner("🖼️ Loading collection highlights..."):
                show_item_gallery(filtered_df, n_items=8, columns=4)
        
        with insight_tab3:
            st.markdown("#### Price Distribution Analysis")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("**Highest Values**")
                with st.spinner("📈 Analyzing top items..."):
                    fig_expensive = create_horizontal_bar_chart(
                        filtered_df, 
                        "Top 10 Most Expensive", 
                        n_items=10, 
                        ascending=False
                    )
                    st.plotly_chart(fig_expensive, use_container_width=True, key="expensive_insights")
            
            with col_right:
                st.markdown("**Best Value Finds**")
                with st.spinner("💰 Finding best values..."):
                    fig_cheapest = create_horizontal_bar_chart(
                        filtered_df, 
                        "Top 10 Cheapest", 
                        n_items=10, 
                        ascending=True
                    )
                    st.plotly_chart(fig_cheapest, use_container_width=True, key="cheapest_insights")
    else:
        st.warning("No data available for insights with current filters.")
# ----------------- About Tab -----------------
with tab5:
    show_about()

# ----------------- Footer -----------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>Data sourced from <a href='https://www.juliensauctions.com' target='_blank'>Julien's Auctions</a> • 
    Built with ❤️ using Streamlit and Plotly • 
    <a href='https://www.hassan-odimi.se' target='_blank'>Hassan Odimi</a></p>
</div>
""", unsafe_allow_html=True)