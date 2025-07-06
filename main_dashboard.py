"""
David Lynch Collection Dashboard - Main Application
Interactive Streamlit dashboard for exploring the David Lynch Collection auction data
"""

import streamlit as st

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

# ----------------- Main Title and Introduction -----------------
st.title("🎬 David Lynch Collection Dashboard")
st.markdown("""
*Explore the fascinating world of David Lynch through the auction data of his personal collection.*
""")

# ----------------- Load Data -----------------
# This uses caching to avoid reloading data on every interaction
df = load_data()

# ----------------- Create Sidebar Filters -----------------
selected_categories, keyword = create_sidebar_filters(df)

# ----------------- Apply Filters to Data -----------------
filtered_df = get_filtered_data(df, selected_categories, keyword)

# ----------------- Calculate Summary Statistics -----------------
stats = calculate_summary_stats(filtered_df)

# ----------------- Display Filter Information -----------------
display_filter_info(selected_categories, keyword, len(df), len(filtered_df))

# ----------------- Create Tab Navigation -----------------
tab1, tab2, tab3, tab4, tab5 = create_tab_navigation()

# ----------------- Data Table Tab -----------------
with tab1:
    st.header("📑 Collection Data Table")
    
    # Show summary statistics at the top
    create_summary_display(stats)
    
    # Display the interactive data table
    st.subheader("Detailed Data Table")
    if not filtered_df.empty:
        create_data_table(filtered_df)
        
        # Provide download options
        st.subheader("Export Data")
        create_download_buttons(filtered_df)
    else:
        st.warning("No items match your current filter criteria. Please adjust your filters.")

# ----------------- Treemap Tab -----------------
with tab2:
    st.header("🌳 Collection Treemap")
    
    if not filtered_df.empty:
        st.markdown("""
        This treemap visualization shows the hierarchical structure of the collection, 
        with items grouped by category and sized by their sold price. The color intensity 
        represents the logarithmic scale of the sold price, helping you identify the most 
        valuable items at a glance.
        """)
        
        # Create and display the treemap
        fig_tree = create_treemap(filtered_df)
        st.plotly_chart(fig_tree, use_container_width=True)
    else:
        st.warning("No data available for the treemap with current filters.")

# ----------------- Scatter Plot Tab -----------------
with tab3:
    st.header("📈 Price Analysis")
    
    if not filtered_df.empty:
        st.markdown("""
        This scatter plot compares the estimated average price with the actual sold price 
        for each item. Items above the diagonal line sold for more than estimated, while 
        items below sold for less. The logarithmic scale helps visualize the wide range of prices.
        """)
        
        # Create and display the scatter plot
        fig_scatter = create_scatter_plot(filtered_df)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Add interpretation help
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
        # Visual gallery of top expensive items
        st.markdown("### Visual Gallery: Top 10 Most Expensive Items")
        st.markdown("""
        Here's a visual exploration of the most valuable pieces in the filtered collection. 
        Each card shows the item's image, title, final sale price, and provides a direct link 
        to the original auction listing for more details.
        """)
        
        show_item_gallery(filtered_df, n_items=10, columns=4)
        
        # Most expensive items bar chart
        st.markdown("### Top 10 Most Expensive Items")
        fig_expensive = create_horizontal_bar_chart(
            filtered_df, 
            "Top 10 Most Expensive Items", 
            n_items=10, 
            ascending=False
        )
        st.plotly_chart(fig_expensive, use_container_width=True)
        
        # Cheapest items bar chart
        st.markdown("### Top 10 Cheapest Items")
        fig_cheapest = create_horizontal_bar_chart(
            filtered_df, 
            "Top 10 Cheapest Items", 
            n_items=10, 
            ascending=True
        )
        st.plotly_chart(fig_cheapest, use_container_width=True)
        
        # Dumbbell chart comparing estimates vs actual sales
        st.markdown("### Estimate vs Sold Price Comparison")
        st.markdown("""
        This dumbbell chart shows how the actual sold prices compared to the estimated 
        average prices for the top 10 most expensive items. Gray dots represent estimated 
        prices, gold dots show actual sold prices, and the connecting lines illustrate 
        the difference between expectation and reality.
        """)
        
        fig_dumbbell = create_dumbbell_chart(filtered_df, n_items=10)
        st.plotly_chart(fig_dumbbell, use_container_width=True)
        
        # Additional insights section
        st.markdown("### Key Insights")
        
        # Calculate some interesting statistics
        if len(filtered_df) > 0:
            # Items that sold above/below estimate
            over_estimate = filtered_df[filtered_df["Sold Price"] > filtered_df["Estimate Avg"]]
            under_estimate = filtered_df[filtered_df["Sold Price"] < filtered_df["Estimate Avg"]]
            
            over_percentage = (len(over_estimate) / len(filtered_df)) * 100
            under_percentage = (len(under_estimate) / len(filtered_df)) * 100
            
            # Average premium/discount
            if len(over_estimate) > 0:
                avg_premium = ((over_estimate["Sold Price"] - over_estimate["Estimate Avg"]) / over_estimate["Estimate Avg"] * 100).mean()
            else:
                avg_premium = 0
                
            if len(under_estimate) > 0:
                avg_discount = ((under_estimate["Estimate Avg"] - under_estimate["Sold Price"]) / under_estimate["Estimate Avg"] * 100).mean()
            else:
                avg_discount = 0
            
            # Display insights
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Items Sold Above Estimate", 
                    f"{len(over_estimate)}", 
                    f"{over_percentage:.1f}% of total"
                )
                if avg_premium > 0:
                    st.metric(
                        "Average Premium", 
                        f"+{avg_premium:.1f}%"
                    )
            
            with col2:
                st.metric(
                    "Items Sold Below Estimate", 
                    f"{len(under_estimate)}", 
                    f"{under_percentage:.1f}% of total"
                )
                if avg_discount > 0:
                    st.metric(
                        "Average Discount", 
                        f"-{avg_discount:.1f}%"
                    )
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