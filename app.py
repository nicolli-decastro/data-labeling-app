# app.py (mixed version: listings from GitHub folder, users.csv from Google Drive)

import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import drive_utils as du

st.set_page_config(page_title="Stolen Items Labeling App", layout="wide")

# Google Drive config
ROOT_FOLDER_NAME = 'LabelingAppData'
USERS_CSV = 'users.csv'

# GitHub folder config (dataset folders pushed with the app)
DATASETS_DIR = os.path.join(os.getcwd(), "Data")

# --- Print working directory and files (for debugging) ---
st.code(f"Working directory: {DATASETS_DIR}")
try:
    files = os.listdir(DATASETS_DIR)
    st.code("Files in 'Data':\n" + "\n".join(files))
except Exception as e:
    st.error(f"Could not list files in Data directory: {e}")

# --- Load Users from Google Drive ---
users_df = du.download_csv(USERS_CSV, du.get_folder_id_by_name(ROOT_FOLDER_NAME))
if users_df.empty:
    st.error("Could not load users.csv from Google Drive.")
    st.stop()

# --- Login ---
if "user_name" not in st.session_state:
    st.title("🔐 Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        if submit:
            match = users_df[(users_df['user_name'] == username) & (users_df['password'] == password)]
            if not match.empty:
                st.session_state.user_name = match.iloc[0]['name']
                st.session_state.user_username = username
                st.rerun()
            else:
                st.error("Invalid credentials")

else:
    if "selected_dataset" not in st.session_state:
        st.title(f"👋 Welcome, {st.session_state.user_name}!")
        st.markdown("This app is designed to label marketplace listings to help determine if an item might be stolen.")

        st.subheader("📋 Datasets")
        header_cols = st.columns([2, 1, 2, 1, 1, 2])
        headers = ["City", "Range", "Date", "Total", "Labeled", "Action"]
        for col, label in zip(header_cols, headers):
            col.markdown(f"**{label}**")

        if os.path.exists(DATASETS_DIR):
            for folder_name in sorted(os.listdir(DATASETS_DIR), reverse=True):
                if not folder_name.startswith("20"):
                    continue

                folder_path = os.path.join(DATASETS_DIR, folder_name)
                if not os.path.isdir(folder_path):
                    continue

                for file in os.listdir(folder_path):
                    if not file.endswith(".csv"):
                        continue

                    csv_path = os.path.join(folder_path, file)
                    images_folder = os.path.join(folder_path, file.replace(".csv", "_files"))

                    location_parts = file.replace(".csv", "").split("_")
                    location = " ".join(location_parts[:-1]).title()
                    range_miles = location_parts[-1]

                    drive_folder_id = du.get_folder_id_by_name(folder_name, parent_id=du.get_folder_id_by_name(ROOT_FOLDER_NAME))
                    labeled_file_id = du.get_file_id_by_name(file, drive_folder_id) if drive_folder_id else None

                    if labeled_file_id:
                        labeled_df = du.download_csv(file, drive_folder_id)
                    else:
                        labeled_df = pd.DataFrame()

                    df_original = pd.read_csv(csv_path)
                    total = len(df_original)
                    labeled = labeled_df['binary_flag'].notna().sum() if not labeled_df.empty else 0
                    is_complete = labeled == total

                    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 2, 1, 1, 2])
                    with col1: st.write(location)
                    with col2: st.write(range_miles)
                    with col3: st.write(folder_name.replace("_", "/"))
                    with col4: st.write(total)
                    with col5: st.write(labeled)
                    with col6:
                        key = f"select_{folder_name}_{file}"
                        if is_complete:
                            st.button("✅ Complete", key=key, disabled=True)
                        elif labeled_df.empty:
                            if st.button("🚀 Start Labeling", key=key):
                                if not drive_folder_id:
                                    drive_folder_id = du.create_folder(folder_name, du.get_folder_id_by_name(ROOT_FOLDER_NAME))
                                df_original[['listing_url', 'photo_url', 'price', 'title', 'location', 'origin_city_list']].assign(
                                    user_name='', binary_flag='', timestamp='').to_csv("temp.csv", index=False)
                                du.upload_csv(pd.read_csv("temp.csv"), file, drive_folder_id)
                                st.session_state.selected_dataset = {
                                    "csv_path": csv_path,
                                    "images_folder": images_folder,
                                    "folder_name": folder_name,
                                    "location": location,
                                    "range": range_miles,
                                    "drive_file": file,
                                    "drive_folder_id": drive_folder_id
                                }
                                st.rerun()
                        else:
                            if st.button("🔘 Continue Labeling", key=key):
                                st.session_state.selected_dataset = {
                                    "csv_path": csv_path,
                                    "images_folder": images_folder,
                                    "folder_name": folder_name,
                                    "location": location,
                                    "range": range_miles,
                                    "drive_file": file,
                                    "drive_folder_id": drive_folder_id
                                }
                                st.rerun()

    else:
        sel = st.session_state.selected_dataset
        st.title(f"📦 Labeling: {sel['location']} ({sel['range']}) | {sel['folder_name'].replace('_', '/')} ")

        df = du.download_csv(sel['drive_file'], sel['drive_folder_id'])
        total = len(df)
        labeled = df['binary_flag'].notna().sum()
        st.progress(labeled / total if total else 0, text=f"{labeled} out of {total} listings labeled")

        not_labeled = df[df['binary_flag'].isna()].reset_index(drop=True)

        if not_labeled.empty:
            st.info("🎉 All listings have been labeled!")
        else:
            row = not_labeled.iloc[0]
            image_name = os.path.basename(row['photo_url'])
            image_path = os.path.join(sel['images_folder'], image_name)

            if os.path.exists(image_path):
                st.image(image_path, use_container_width=True)
            else:
                st.warning(f"⚠️ Image not found: {image_name}")

            st.markdown(f"**Title:** {row['title']}")
            st.markdown(f"**Price:** {row['price']}")
            st.markdown(f"**Location:** {row['location']}")
            st.markdown(f"**[View Listing]({row['listing_url']})**")

            label = st.radio("Is this item likely stolen?", ["Yes", "No"])

            if st.button("Submit Label"):
                idx = df[(df['listing_url'] == row['listing_url']) & (df['photo_url'] == row['photo_url'])].index[0]
                df.at[idx, 'binary_flag'] = label
                df.at[idx, 'user_name'] = st.session_state.user_username
                df.at[idx, 'timestamp'] = datetime.now().isoformat()
                du.upload_csv(df, sel['drive_file'], sel['drive_folder_id'])
                df.drop(df.index, inplace=True)  # clear dataframe from memory
                st.success("Label submitted!")
                st.rerun()

        st.divider()
        if st.button("⬅️ Back to Datasets"):
            del st.session_state.selected_dataset
            st.rerun()

    st.divider()
    if st.button("🔒 Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
