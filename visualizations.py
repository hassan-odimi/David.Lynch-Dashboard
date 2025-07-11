"""
Visualization Module for David Lynch Collection Dashboard
Contains functions for creating charts and visualizations
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def create_treemap(df):
    """
    Create a treemap visualization showing collection hierarchy by category and title.
    
    Args:
        df (pd.DataFrame): Filtered dataset with Category, Title, and Sold Price columns
        
    Returns:
        plotly.graph_objects.Figure: Treemap figure
    """
    fig_tree = px.treemap(
        df,
        path=["Category", "Title"],
        values="Sold Price",
        color="Log Sold Price",
        color_continuous_scale="reds",
        title="Treemap of Total Sold Price (Colour: Log(Sold Price))"
    )
    fig_tree.update_coloraxes(colorbar_title="Log(Sold Price)")
    return fig_tree


def create_scatter_plot(df):
    """
    Create a scatter plot comparing sold prices with estimated averages.
    
    Args:
        df (pd.DataFrame): Filtered dataset with price and category information
        
    Returns:
        plotly.graph_objects.Figure: Scatter plot figure
    """
    fig_scatter = px.scatter(
        df,
        x="Estimate Avg",
        y="Sold Price",
        color="Category",
        hover_data=["Title", "Estimated Price", "Sold Price", "URL"],
        title="Scatter Plot of Sold Price vs Estimated Average",
        labels={"Estimate Avg": "Estimated Average ($)", "Sold Price": "Sold Price ($)"}
    )
    fig_scatter.update_xaxes(type="log")
    return fig_scatter


def create_horizontal_bar_chart(df, title_text, n_items=10, ascending=False):
    """
    Create a horizontal bar chart for top expensive or cheapest items.
    
    Args:
        df (pd.DataFrame): Dataset to process
        title_text (str): Title for the chart
        n_items (int): Number of items to show
        ascending (bool): Whether to sort in ascending order (for cheapest items)
        
    Returns:
        plotly.graph_objects.Figure: Horizontal bar chart figure
    """
    # Get top/bottom items based on sorting preference
    if ascending:
        top_items = df.nsmallest(n_items, "Sold Price").sort_values("Sold Price", ascending=True)
    else:
        top_items = df.nlargest(n_items, "Sold Price").sort_values("Sold Price", ascending=False)
    
    fig_bar = px.bar(
        top_items,
        x="Sold Price",
        y="Title",
        orientation="h",
        color="Category",
        category_orders={"Title": top_items["Title"].tolist()},
        title=title_text,
        labels={"Sold Price": "Sold Price ($)", "Title": "Item"},
        text="Sold Price"
    )
    fig_bar.update_traces(texttemplate='$%{text:,.0f}', textposition='inside')
    return fig_bar


def create_dumbbell_chart(df, n_items=10):
    """Create a dumbbell chart comparing estimated vs sold prices for top items."""
    top_expensive = df.nlargest(n_items, "Sold Price").sort_values("Sold Price", ascending=False)
    
    fig_dumbbell = px.scatter(
        top_expensive,
        x="Estimate Avg",
        y="Title",
        color_discrete_sequence=["gray"],
        labels={"Estimate Avg": "Price ($)", "Title": "Item"},
        title=""  # Remove title to avoid conflicts
    )
    
    # Update traces with explicit names
    fig_dumbbell.data[0].name = "Estimated"
    
    # Add sold prices
    fig_dumbbell.add_scatter(
        x=top_expensive["Sold Price"],
        y=top_expensive["Title"],
        mode='markers',
        marker=dict(color="gold", size=8),
        name="Actual Sale"
    )
    
    # Connect with lines
    for _, row in top_expensive.iterrows():
        fig_dumbbell.add_shape(
            type="line",
            x0=row["Estimate Avg"],
            y0=row["Title"],
            x1=row["Sold Price"],
            y1=row["Title"],
            line=dict(color="lightgray", width=2)
        )
    
    fig_dumbbell.update_layout(
        height=600,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig_dumbbell

def show_item_gallery(df, n_items=10, columns=4):
    """
    Display a visual gallery of top items with images, titles, and prices.
    
    Args:
        df (pd.DataFrame): Dataset containing item information
        n_items (int): Number of items to display
        columns (int): Number of columns in the gallery layout
    """
    # Get top items sorted by price
    sorted_df = df.nlargest(n_items, "Sold Price").sort_values("Sold Price", ascending=False).reset_index(drop=True)
    
    # Create column layout
    cols = st.columns(columns)
    
    # Display each item in the gallery
    for idx, row in sorted_df.iterrows():
        with cols[idx % columns]:
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 20px;
                    text-align: left;
                    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
                    height: 450px;
                    display: flex;
                    flex-direction: column;
                    justify-content: flex-start;
                ">
                    <div>
                        <img src="{row['Image']}" style="width: 100%; height: auto; border-radius: 4px; max-height: 180px; object-fit: contain;" />
                        <h4 style="margin: 10px 0;">#{idx+1}: {row['Title']}</h4>
                        <p style="font-weight: bold; font-size: 18px;">💲 ${row['Sold Price']:,.0f}</p>
                    </div>
                    <a href="{row['URL']}" target="_blank" style="
                        display: inline-block;
                        margin-top: 8px;
                        padding: 6px 12px;
                        background-color: #f63366;
                        color: #fff;
                        text-decoration: none;
                        border-radius: 4px;
                        align-self: flex-start;
                    ">Visit Item Page</a>
                </div>
                """,
                unsafe_allow_html=True
            )


def create_category_distribution_chart(df):
    """
    Create a pie chart showing the distribution of items by category.
    
    Args:
        df (pd.DataFrame): Dataset with Category column
        
    Returns:
        plotly.graph_objects.Figure: Pie chart figure
    """
    category_counts = df['Category'].value_counts()
    
    fig_pie = px.pie(
        values=category_counts.values,
        names=category_counts.index,
        title="Distribution of Items by Category"
    )
    
    return fig_pie


def create_price_distribution_histogram(df):
    """
    Create a histogram showing the distribution of sold prices.
    
    Args:
        df (pd.DataFrame): Dataset with Sold Price column
        
    Returns:
        plotly.graph_objects.Figure: Histogram figure
    """
    fig_hist = px.histogram(
        df,
        x="Sold Price",
        nbins=30,
        title="Distribution of Sold Prices",
        labels={"Sold Price": "Sold Price ($)", "count": "Number of Items"}
    )
    
    # Add logarithmic scale option for better visualization
    fig_hist.update_xaxes(type="log")
    
    return fig_hist
