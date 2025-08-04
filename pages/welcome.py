import streamlit as st

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

st.set_page_config(page_title="Welcome", layout="wide")

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

col1, col2, col3 = st.columns([0.5,4,0.5])

with col2:

    # Title and Intro
    st.title("👋 Welcome to the Labeling & Visualization App")

    st.markdown(
        """
        Welcome to our platform for manual labeling, AI evaluation, and analyzing suspicious marketplace items! You can use the buttons below to navigate to different functionalities of the app.
        """
    )

    st.markdown("<hr style='margin:1px 0;' />", unsafe_allow_html=True)

    # Navigation Buttons
    st.header("Choose What You Want to Do")

    col1, col2, col3 = st.columns([2,2,2])

    with col1:
        with st.container(border=True):
            st.subheader("📝 Data for Label")
            st.markdown(
                """
                Navigate to the labeling interface where you can:
                - Select from available datasets
                - Label data directly in the app
                - Download the labeled dataset as a CSV  
                """
            )
            if st.button("Go to Labeling Page"):
                st.switch_page("pages/database_label.py")

    with col3:
        with st.container(border=True):
            st.subheader("📊 Data Visualization")
            st.markdown(
                """
                Upload a labeled CSV file (manually labeled or AI-labeled) and:
                - Explore trends in your data  
                - View visualizations to assist in analysis and decision-making  
                """
            )
            if st.button("Go to Visualization Page"):
                st.switch_page("pages/data_visualization.py")

    with col2:
        with st.container(border=True):
            st.subheader("🤖 AI Evaluation Tool")

            st.markdown(
                """
                Evaluate marketplace listings using AI to detect suspicious or stolen items:
                - Automatically flag listings using the AI model  
                - Download results with suspicion scores  
                """,
                unsafe_allow_html=True
            )

            if st.button("Go to AI Tool"):
                st.switch_page("pages/ai_evaluation_upload.py")
