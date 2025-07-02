import streamlit as st

def show_about():
    # Start a centered container with max width to limit text span
    st.markdown(
        """
        <style>
        .about-container {
            max-width: 1000px;
            margin-left: auto;
            margin-right: auto;
            padding-left: 30px;
            padding-right: 30px;
        }
        </style>
        <div class="about-container">
        """,
        unsafe_allow_html=True
    )

    # ---- Reflection block with bigger David portrait ----
    left_col, right_col = st.columns([1, 2])  # Keep ratio 1:2 for balance

    with left_col:
        st.image("assets/lynch.webp", width=420)

    with right_col:
        st.markdown("""
        ### A Personal Reflection

        *I am fascinated by cinema that defies convention and invites deeper reflection.*
        Only a few have done so like **David Lynch**. I have always admired his wonderfully strange personality, which reminds me of my grandfather’s eccentric spirit.
        His work — with its surreal imagery and layered narratives — has profoundly influenced modern art and cinema.

        This dashboard is my way of diving into the life of David Lynch through the books, art, and everyday objects that shaped his vision.
        I feel sadness at his passing, but his art and memory will live on through what he left behind.
        """)

    st.markdown("---")

    st.markdown("""
    ### About the Project

    This interactive dashboard showcases and analyses items from the **David Lynch Collection**, auctioned by [Julien's Auctions](https://www.juliensauctions.com/en/auctions/julien-s-auctions-turner-classic-movies-present-the-david-lynch-collection).

    **Features:**
    - Explore detailed auction data for scripts, props, memorabilia, and more.
    - See price trends, top items, category breakdowns, and visual insights.
    - Interactive charts, dynamic filters, and visual galleries.

    **Source:**
    All auction data was sourced from [Julien's Auctions](https://www.juliensauctions.com/en/auctions/julien-s-auctions-turner-classic-movies-present-the-david-lynch-collection).
    """)

    st.markdown("---")

    # ---- Creator block with your photo, no caption ----
    creator_col1, creator_col2 = st.columns([1, 5])

    with creator_col1:
        st.image("assets/hassan.png", width=180)

    with creator_col2:
        st.markdown("""
        ### Creator

        My name is **Hassan Odimi**, and I'm a UX Designer passionate about **cinema**, **unconventional design**, and creating meaningful interactive experiences.
        This project combines my love of film, data, and design — and I hope it invites reflection and curiosity.

        👉 You can explore more of my work at [www.hassan-odimi.se](https://www.hassan-odimi.se)

        Feel free to reach out, connect, or collaborate — I’d love to hear from you.
        """)

    # Close the centered container
    st.markdown("</div>", unsafe_allow_html=True)
