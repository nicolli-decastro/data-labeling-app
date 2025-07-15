import streamlit as st

# st.set_page_config(page_title="Redirecting...", layout="centered")

# st.sidebar

st.set_page_config(
    page_title="Labeling App",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Hide the sidebar completely
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

if "user_name" in st.session_state:
    st.switch_page("pages/welcome.py")
else:
    st.switch_page("pages/login.py")

