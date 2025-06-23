import streamlit as st
import pandas as pd
import sys
import os
import re
from datetime import datetime
import drive_utils as du

st.set_page_config(page_title="Login", layout="centered")

# Hide the sidebar completely
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

# Google Drive config
ROOT_FOLDER_NAME = 'LabelingAppData'
USERS_CSV = 'users.csv'

def reset_local_dataframes():
    for key in list(st.session_state.keys()):
        if key.startswith("local_df_") or key == "current_df":
            del st.session_state[key]

st.title("🔐 Login")

with st.form("login_form"):
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    submit = st.form_submit_button("Login")

    if submit:
        folder_id = du.get_folder_id_by_name(ROOT_FOLDER_NAME)
        if not folder_id:
            st.error("Could not find root folder on Google Drive.")
            st.stop()

        users_df = du.download_csv(USERS_CSV, folder_id)
        match = users_df[(users_df['user_name'] == username) & (users_df['password'] == password)]

        if not match.empty:
            st.session_state.user_name = match.iloc[0]['name']
            st.session_state.user_username = username
            st.session_state.root_folder_id = folder_id
            reset_local_dataframes()
            st.success("Login successful! Redirecting...")
            st.switch_page("pages/welcome.py")
        else:
            st.error("Invalid credentials")