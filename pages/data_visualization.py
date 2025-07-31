import streamlit as st
import numpy as np
import pandas as pd

# -- SIDE BAR CONFIGURATION

hide_streamlit_nav_spacing = """
<style>
/* Reduce top padding */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0rem;
}

/* Hide default search / nav items */
[data-testid="stSidebarNavItems"], [data-testid="stSidebarNav"] {
    display: none;
}
</style>
"""
st.markdown(hide_streamlit_nav_spacing, unsafe_allow_html=True)

# Sidebar Navigation with Links
st.sidebar.markdown("## Navigation")
st.sidebar.page_link("pages/welcome.py", label="Home Page")
st.sidebar.page_link("pages/database_label.py", label="Data for Label")
st.sidebar.page_link("pages/data_visualization.py", label="Data Visualization")
st.sidebar.page_link("pages/ai_evaluation_upload.py", label="AI-Tool")
st.sidebar.button("Logout", use_container_width=True)

# If Logout is clicked
if st.session_state.get("logout", False):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# -- PAGE START

col1, col2, col3 = st.columns([0.2,3,0.2])

with col2:

    st.set_page_config(page_title="Data Visualization", layout="wide")

    st.title("📊 Data Visualization")

    import streamlit as st
    import textwrap
    from geopy.geocoders import Nominatim
    import time

    columns_required = {"price, title, location, model_name, reasoning, price_suspicion, item_bulk, item_new, listing_tone, mentions_retailer, overall_likelihood, stolen"}

    st.markdown(
        f"""
        <div style="margin-top: -10px;">
            <p style="font-size: 16px; color: #555; margin-bottom: 1rem;">
                Upload a labeled CSV file to explore trends, compare AI and human annotations, and assist in your decision-making process.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
        )

    with st.expander("✅ Learn about required columns"):
        st.markdown(
        f"""<div style="font-size: 14px; padding: 8px;">
                <code>{columns_required}</code>
            </p>
            <p style="margin-top: 1rem; font-size: 15px;">
                Optionally, your dataset can also include the <code>binary_flag</code> column for <strong>manually labeled results</strong>. 
                If present, the app will allow you to compare human vs AI labeling outcomes side by side.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
        )

    # --- File Uploader ---
    uploaded_file = st.file_uploader("📁 Upload your labeled CSV file", type=["csv"])

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # --- Check required columns ---
        required_cols = {
            "price", "title", "location", "origin_city_list", "overall_likelihood"
        }

        ai_label_cols = {
            "model_name", "reasoning", "price_suspicion", "item_bulk",
            "item_new", "listing_tone", "mentions_retailer", "overall_likelihood", "stolen"
        }

        missing_cols = required_cols.union(ai_label_cols) - set(df.columns)

        for col in missing_cols:
            if "created_missing_cols" not in st.session_state:
                st.session_state.created_missing_cols = True
            else:
                if col == "overall_likelihood":
                    df[col] = np.random.randint(1, 11, size=len(df))  # Random int from 1 to 10
                else:
                    df[col] = np.nan

        if missing_cols:
            st.warning(f"⚠️ The following columns were missing and have been added with default values: {', '.join(missing_cols)}")
        else:
            st.success("✅ File uploaded and all required columns are present.")

        # --- Optional Column Check: binary_flag ---
        has_manual_label = "binary_flag" in df.columns
        if has_manual_label:
            st.info("✅ Manual labels (`binary_flag`) detected. You can compare them with AI predictions.")
        else:
            st.warning("⚠️ No manual labels (`binary_flag`) found. Only AI-generated labels will be used.")

        
        # --- PLOTS

        import plotly.express as px
        import plotly.graph_objects as go
        from geopy.geocoders import Nominatim
        import time

        # --- Select AI threshold to binarize `overall_likelihood` ---
        st.markdown("### 🎚️ AI Likelihood Threshold")
        st.markdown("Choose the minimum likelihood score (1–10) that you consider to indicate a 'Likely Stolen' item.")
        threshold = st.slider("Likelihood Threshold", min_value=1, max_value=10, value=5)

        # --- Create binary column from AI score ---

        # Convert to numeric first (non-numeric values become NaN)
        df["overall_likelihood"] = pd.to_numeric(df["overall_likelihood"], errors="coerce")

        # Then apply the threshold
        df["ai_binary"] = df["overall_likelihood"].apply(lambda x: 1 if x >= threshold else 0)

        # Page Layout
        col1, col2 = st.columns([0.6,2])

        # -- 1. Summary --
        with col1:
            st.subheader("📊 Dataset Summary")
            total = len(df)
            flagged = df["ai_binary"].sum()
            percentage = round((flagged / total) * 100, 2)
            with st.container(border=True):
                st.metric("Total Listings", total)
                st.metric("Flagged Suspicious", flagged)
                st.metric("Percentage Suspicious", f"{percentage}%")

        # -- 2. Distribution of AI Scores --
        with col2:
            tab1, tab2 = st.tabs(["📈 Distribution of AI Likelihood Scores", "📦 Box Plot: Price vs. AI Label"])
            with tab1:
                st.markdown("##### Distribution of AI Likelihood Scores")
                score_counts = df["overall_likelihood"].value_counts().sort_index().reset_index()
                score_counts.columns = ["Score", "Count"]
                fig_scores = px.line(score_counts, x="Score", y="Count", markers=True)
                st.plotly_chart(fig_scores, title="📈 Distribution of AI Likelihood Scores", use_container_width=True)

            with tab2:
                import plotly.graph_objects as go

                st.markdown("##### Box Plot: Price vs. AI Label")

                fig = go.Figure()

                fig.add_trace(go.Box(
                    y=df[df['ai_binary'] == 0]['price'],
                    name='Not Likely Stolen',
                    marker_color='blue',
                    boxpoints=False  # Hide individual points
                ))

                fig.add_trace(go.Box(
                    y=df[df['ai_binary'] == 1]['price'],
                    name='Likely Stolen',
                    marker_color='red',
                    boxpoints=False  # Hide individual points
                ))

                fig.update_layout(
                    yaxis_title='Listing Price ($)',
                    xaxis_title='AI Label',
                    # title="📦 Box Plot: Price vs. AI Label",
                    yaxis_type='log',  # Still helps readability with huge outliers
                    height=550
                )

                st.plotly_chart(fig, use_container_width=True)

        # -- 3. Box plot of Prices vs. AI Label

        col1, col2 = st.columns([2,2])

        # -- US REGIONS GRAPH

        # -- Region Mapping Setup --
        us_regions = {
            "Northeast": ["CT", "ME", "MA", "NH", "RI", "VT", "NJ", "NY", "PA"],
            "Midwest":   ["IL", "IN", "MI", "OH", "WI", "IA", "KS", "MN", "MO", "NE", "ND", "SD"],
            "South":     ["DE", "FL", "GA", "MD", "NC", "SC", "VA", "DC", "WV", "AL", "KY", "MS", "TN", "AR", "LA", "OK", "TX"],
            "West":      ["AZ", "CO", "ID", "MT", "NV", "NM", "UT", "WY", "AK", "CA", "HI", "OR", "WA"]
        }

        def get_region(state_abbr):
            for region, states in us_regions.items():
                if state_abbr in states:
                    return region
            return "Other"

            # -- Pie and Bar for Flagged Items by Location --

        st.subheader("🗺️ Location Breakdown for Flagged Items")

        # -- Extract State Abbreviation from "location" column --
        df["state_abbr"] = df["location"].str.extract(r",\s*([A-Z]{2})", expand=False)

        # -- Filter flagged listings only --
        flagged_df = df[df["ai_binary"] == 1].copy()

        if flagged_df.empty:
            st.warning("No flagged listings found for geographic analysis.")
        else:
            flagged_df["region"] = flagged_df["state_abbr"].apply(get_region)

            # ---- Pie Chart by Region ----
            region_counts = flagged_df["region"].value_counts().reset_index()
            region_counts.columns = ["Region", "Count"]

            pie_fig = px.pie(region_counts, values="Count", names="Region",
                            title="🧭 Flagged Listings by US Region",
                            color_discrete_sequence=px.colors.qualitative.Set2)

            # ---- Bar Chart by State ----
            state_counts = flagged_df["state_abbr"].value_counts().reset_index()
            state_counts.columns = ["State", "Count"]

            bar_fig = px.bar(state_counts.sort_values("Count", ascending=False),
                            x="State", y="Count",
                            title="🏷️ Flagged Listings by US State",
                            color="Count",
                            color_continuous_scale="Reds")

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(pie_fig, selection_mode="lasso", use_container_width=True)
            with col2:
                st.plotly_chart(bar_fig, selection_mode="lasso", use_container_width=True)

            # ---- Bar Chart by City ----
            st.subheader("🗺️ Flagged Listings by US Cities")
            state_counts = flagged_df["location"].value_counts().reset_index()
            state_counts.columns = ["City", "Count"]

            top_n = st.slider("Choose the number of cities to display", min_value=5, max_value=50, value=20, step=5)

            bar_fig = px.bar(
                state_counts.sort_values("Count", ascending=False).head(top_n),
                x="City",
                y="Count",
                title=f"🏷️ Top {top_n} Flagged Listings by US City",
                color="Count",
                color_continuous_scale="Reds",
            )
            
            st.plotly_chart(bar_fig, selection_mode="lasso", use_container_width=True)

    else:
        st.info("Please upload a CSV file to begin.")
