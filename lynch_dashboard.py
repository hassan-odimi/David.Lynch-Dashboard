import json
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import tempfile
from about import show_about
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# ----------------- Load data -----------------
@st.cache_data
def load_data():
    with open("David Lynch Collection Data.json", encoding="utf-8") as f:
        data = json.load(f)

    sold_prices, estimated_low, estimated_high, estimated_avg = [], [], [], []
    estimated_price_raw, titles, urls, images = [], [], [], []

    for item in data:
        sold = int(item["Sold Price"].replace("$", "").replace(",", "").strip())
        est_range = item["Estimated Price"].replace("$", "").replace(",", "").strip()
        if "-" in est_range:
            est_low, est_high = est_range.split("-")
            est_low, est_high = int(est_low.strip()), int(est_high.strip())
            est_avg = (est_low + est_high) / 2
        else:
            est_low = est_high = est_avg = int(est_range.strip())

        sold_prices.append(sold)
        estimated_low.append(est_low)
        estimated_high.append(est_high)
        estimated_avg.append(est_avg)
        estimated_price_raw.append(item["Estimated Price"])
        titles.append(item["Title"])
        urls.append(item["Item URL"])
        images.append(item["Item Image"])

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
    return df

df = load_data()


# ----------------- Detect category -----------------
def detect_category(title):
    title = title.lower()
    if any(k in title for k in ["script", "screenplay"]):
        return "Scripts & Screenplays"
    elif any(k in title for k in ["camera", "camcorder"]):
        return "Cameras & Camcorders"
    elif any(k in title for k in ["light", "lighting"]):
        return "Lighting Equipment"
    elif any(k in title for k in ["book", "volume", "reference"]):
        return "Books & Reference"
    elif any(k in title for k in ["poster", "signed poster"]):
        return "Posters & Prints"
    elif any(k in title for k in ["sofa", "chair", "table", "furniture"]):
        return "Furniture"
    elif any(k in title for k in ["mug", "cup", "coffee maker", "espresso"]):
        return "Coffee & Kitchen"
    elif any(k in title for k in ["guitar", "bass", "keyboard", "drum", "microphone", "audio", "speaker"]):
        return "Instruments & Audio"
    elif any(k in title for k in ["record", "album", "vinyl"]):
        return "Records & Music"
    elif any(k in title for k in ["prop", "memorabilia", "production slate"]):
        return "Props & Memorabilia"
    else:
        return "Other"

df["Category"] = df["Title"].apply(detect_category)

# ----------------- Streamlit UI -----------------
st.set_page_config(page_title="David Lynch Collection Dashboard", layout="wide")
st.title("🎬 David Lynch Collection Dashboard")

# ----------------- Sidebar filters -----------------
st.sidebar.header("Filter Data")
categories = sorted(df["Category"].unique())

with st.sidebar.expander("Filter by Category", expanded=True):

    if "selected_categories" not in st.session_state:
        st.session_state.selected_categories = {category: True for category in categories}

    with st.container():
        if st.button("✅ Select All"):
            for category in categories:
                st.session_state.selected_categories[category] = True

        if st.button("❌ Clear All"):
            for category in categories:
                st.session_state.selected_categories[category] = False

    for category in categories:
        st.session_state.selected_categories[category] = st.checkbox(
            category,
            value=st.session_state.selected_categories[category]
        )

selected_categories = [c for c, checked in st.session_state.selected_categories.items() if checked]

keyword = st.sidebar.text_input("Search by keyword in title", "")

filtered_df = df[df["Category"].isin(selected_categories)]
if keyword:
    filtered_df = filtered_df[filtered_df["Title"].str.contains(keyword, case=False, na=False)]

filtered_df["Log Sold Price"] = np.log10(filtered_df["Sold Price"] + 1)

# ----------------- Tabs -----------------
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📑 Data Table", "🌳 Treemap", "📈 Scatter Plot", "🔍 Insights", "ℹ️ About"])

# ----------------- Data Table -----------------
with tab1:
    df_display = filtered_df.copy()
    df_display["Link"] = df_display["URL"]

    gb = GridOptionsBuilder.from_dataframe(
        df_display[["Image", "Title", "Sold Price", "Estimated Price", "Estimate Avg", "Category", "Link"]]
    )

    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=100)
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=False)
    gb.configure_grid_options(
        enableRangeSelection=True,
        enableBrowserTooltips=True,
        enableCellTextSelection=True,
        domLayout='normal',
        rowHeight=120,
        suppressContextMenu=False
    )

    dollar_formatter = JsCode("""
        function(params) {
            if (params.value != null) {
                return '$' + params.value.toLocaleString();
            } else {
                return '';
            }
        }
    """)
    gb.configure_column("Sold Price", type=["numericColumn"], valueFormatter=dollar_formatter)
    gb.configure_column("Estimate Avg", type=["numericColumn"], valueFormatter=dollar_formatter)

    # Enforce clear column sizing
    gb.configure_grid_options(rowHeight=140)
    gb.configure_column("Image", minWidth=120, maxWidth=150)
    gb.configure_column("Title", minWidth=250, maxWidth=450, wrapText=True, autoHeight=True)
    gb.configure_column("Sold Price", minWidth=120, maxWidth=140)
    gb.configure_column("Estimated Price", minWidth=140, maxWidth=180)
    gb.configure_column("Estimate Avg", minWidth=120, maxWidth=150)
    gb.configure_column("Category", minWidth=120, maxWidth=200)
    gb.configure_column("Link", minWidth=80, maxWidth=100)


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

        # Compute basic stats on filtered data
    total_items = filtered_df.shape[0]
    total_value = filtered_df["Sold Price"].sum()
    average_price = filtered_df["Sold Price"].mean()
    min_price = filtered_df["Sold Price"].min()
    max_price = filtered_df["Sold Price"].max()

    most_expensive = filtered_df.loc[filtered_df["Sold Price"].idxmax()]
    cheapest = filtered_df.loc[filtered_df["Sold Price"].idxmin()]

    most_common_category = (
        filtered_df["Category"].value_counts().idxmax()
        if not filtered_df["Category"].empty else "N/A"
    )

    # Show a summary block
    st.markdown(f"""
    ### Quick Collection Insights

    - **Total Items:** {total_items}
    - **Total Sold Value:** ${total_value:,.0f}
    - **Average Sold Price:** ${average_price:,.0f}
    - **Most Expensive Item:** *{most_expensive["Title"]}* (${most_expensive["Sold Price"]:,.0f})
    - **Cheapest Item:** *{cheapest["Title"]}* (${cheapest["Sold Price"]:,.0f})
    """)

    st.subheader("Detailed Data Table")
    AgGrid(
        df_display[["Image", "Title", "Sold Price", "Estimated Price", "Estimate Avg", "Category", "Link"]],
        gridOptions=gb.build(),
        enable_enterprise_modules=False,
        allow_unsafe_jscode=True,
        update_mode="NO_UPDATE",
        fit_columns_on_grid_load=True,
        theme="alpine",
        height=600
    )

    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button("Download as CSV", data=csv, file_name="lynch_filtered.csv", mime="text/csv")

    df_export = df_display.copy()
    df_export["Link"] = df_export["URL"].apply(lambda x: f'<a href="{x}" target="_blank">Open</a>')
    html_table = df_export[["Title", "Sold Price", "Estimated Price", "Estimate Avg", "Category", "Link"]].to_html(escape=False, index=False)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        tmpfile.write(html_table.encode("utf-8"))
        tmpfile.flush()
        st.download_button(
            label="Download as HTML",
            data=open(tmpfile.name, "rb"),
            file_name="lynch_table.html",
            mime="text/html"
        )

# ----------------- Treemap -----------------
with tab2:
    st.subheader("Treemap by Category and Title")
    fig_tree = px.treemap(
        filtered_df,
        path=["Category", "Title"],
        values="Sold Price",
        color="Log Sold Price",
        color_continuous_scale="reds",
        title="Treemap of Total Sold Price (Colour: Log(Sold Price))"
    )
    fig_tree.update_coloraxes(colorbar_title="Log(Sold Price)")
    st.plotly_chart(fig_tree, use_container_width=True)

# ----------------- Scatter Plot -----------------
with tab3:
    st.subheader("Sold Price vs Estimated Average")

    fig_scatter = px.scatter(
        filtered_df,
        x="Estimate Avg",
        y="Sold Price",
        color="Category",
        hover_data=["Title", "Estimated Price", "Sold Price", "URL"],
        title="Scatter Plot of Sold Price vs Estimated Average",
        labels={"Estimate Avg": "Estimated Average ($)", "Sold Price": "Sold Price ($)"}
    )
    fig_scatter.update_xaxes(type="log")
    st.plotly_chart(fig_scatter, use_container_width=True)
# ----------------- Insights -----------------
with tab4:
    st.subheader("🔍 Deeper Insights")
    # ---------------------------
    # Gallery for Top Expensive
    # ---------------------------

    st.markdown("### Quick Look: Top 10 Most Expensive Items")

    def show_top_gallery(df, N=10, columns=2):
        sorted_df = df.nlargest(N, "Sold Price").sort_values("Sold Price", ascending=False).reset_index(drop=True)
        cols = st.columns(columns)
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
        height: 450px;  /* Fixed card height */
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

    # Use the helper
    show_top_gallery(filtered_df, N=10, columns=4)
    # ---------------------------
    # Define Top 10 Expensive / Cheapest
    # ---------------------------

    top_expensive = filtered_df.nlargest(10, "Sold Price")
    top_expensive_sorted = top_expensive.sort_values("Sold Price", ascending=False)  # for horizontal bar

    top_cheapest = filtered_df.nsmallest(10, "Sold Price")
    top_cheapest_sorted = top_cheapest.sort_values("Sold Price", ascending=True)

    # ---------------------------
    # Horizontal bar: Most Expensive
    # ---------------------------

    fig_expensive = px.bar(
        top_expensive_sorted,
        x="Sold Price",
        y="Title",
        orientation="h",
        color="Category",
        category_orders={"Title": top_expensive_sorted["Title"].tolist()},
        title="Top 10 Most Expensive Items",
        labels={"Sold Price": "Sold Price ($)", "Title": "Item"},
        text="Sold Price"
    )
    fig_expensive.update_traces(texttemplate='$%{text:,.0f}', textposition='inside')
    st.plotly_chart(fig_expensive, use_container_width=True)

    # ---------------------------
    # Horizontal bar: Cheapest
    # ---------------------------

    fig_cheapest = px.bar(
        top_cheapest_sorted,
        x="Sold Price",
        y="Title",
        orientation="h",
        color="Category",
        category_orders={"Title": top_cheapest_sorted["Title"].tolist()},
        title="Top 10 Cheapest Items",
        labels={"Sold Price": "Sold Price ($)", "Title": "Item"},
        text="Sold Price"
    )
    fig_cheapest.update_traces(texttemplate='$%{text:,.0f}', textposition='inside')
    st.plotly_chart(fig_cheapest, use_container_width=True)

    # ---------------------------
    # Optional: Dumbbell Chart
    # ---------------------------

    st.markdown("### Estimate vs Sold for Top 10 Most Expensive")

    fig_dumbbell = px.scatter(
        top_expensive_sorted,
        x="Estimate Avg",
        y="Title",
        color_discrete_sequence=["gray"],
        symbol_sequence=["circle"],
        labels={"Estimate Avg": "Estimate Avg ($)", "Title": "Item"}
    )

    fig_dumbbell.add_scatter(
        x=top_expensive_sorted["Sold Price"],
        y=top_expensive_sorted["Title"],
        mode='markers',
        marker=dict(color="gold"),
        name="Sold Price"
    )

    for _, row in top_expensive_sorted.iterrows():
        fig_dumbbell.add_shape(
            type="line",
            x0=row["Estimate Avg"],
            y0=row["Title"],
            x1=row["Sold Price"],
            y1=row["Title"],
            line=dict(color="lightgray", width=2)
        )

    fig_dumbbell.update_layout(
        title="Top 10: Sold vs Estimated Avg",
        xaxis_title="Price ($)",
        yaxis_title="",
        height=600
    )

    st.plotly_chart(fig_dumbbell, use_container_width=True)

with tab5:
    show_about()

# with tab5:
#     st.title("ℹ️ About this Project")
#
#     st.markdown("""
#     *I am fascinated by cinema that defies convention and invites deeper reflection.
#     Only a few have done so like David Lynch. I have always admired his wonderfully strange personality, which reminds me of my grandfather’s eccentric spirit. David Lynch’s work, with its surreal imagery and layered narratives, has profoundly influenced modern art and cinema.
#     This dashboard is my way of diving into the life of David Lynch through the books, art, and everyday objects that shaped his vision.
#     I feel sadness at his passing, but his art and memory will live on through what he left behind.*
#
#     ---
#
#     This interactive dashboard showcases and analyses items from the **David Lynch Collection**, auctioned by [Julien's Auctions](https://www.juliensauctions.com/en/auctions/julien-s-auctions-turner-classic-movies-present-the-david-lynch-collection).
#
#     **Features:**
#     - Explore detailed auction data for scripts, props, memorabilia, and more.
#     - See price trends, top items, category breakdowns, and visual insights.
#     - Interactive charts, dynamic filters, and visual galleries.
#
#     ---
#     **Source:** All auction data was sourced from [Julien's Auctions](https://www.juliensauctions.com/en/auctions/julien-s-auctions-turner-classic-movies-present-the-david-lynch-collection).
#
#     ---
#     **About Me:**
#     My name is Hassan Odimi. I am a UX & Product Designer with Computer Scinece backround based in Sweden. I am passionate about cinema, art, design and creating meaningful interactive experiences that invite exploration and reflection.
#     If you’d like to see more of my work, ideas, and projects, I invite you to visit my portfolio at [www.hassan-odimi.se](https://www.hassan-odimi.se/).
#     Feel free to connect, share thoughts, or collaborate. I’d love to hear from you.
