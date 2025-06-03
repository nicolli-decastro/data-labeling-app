# app.py (mixed version: listings from GitHub folder, users.csv from Google Drive)

import streamlit as st
import pandas as pd
import os
import re
from datetime import datetime
import drive_utils as du

st.set_page_config(page_title="Stolen Items Labeling App", layout="centered")

# Google Drive config
ROOT_FOLDER_NAME = 'LabelingAppData'
USERS_CSV = 'users.csv'

# GitHub folder config (dataset folders pushed with the app)
DATASETS_DIR = os.path.join(os.getcwd(), "Data")

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
        headers = ["City", "Range", "Date", "Labeled", "Total", "Action"]
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

                    df = pd.read_csv(csv_path)

                    total = len(df)
                    labeled = df['binary_flag'].notna().sum()
                    is_complete = labeled == total

                    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 2, 1, 1, 2])
                    with col1: st.write(location)
                    with col2: st.write(range_miles)
                    with col3: st.write(folder_name.replace("_", "/"))
                    with col4: st.write(labeled)
                    with col5: st.write(total)
                    with col6:
                        key = f"select_{folder_name}_{file}"
                        if is_complete:
                            st.button("✅ Complete", key=key, disabled=True)
                        else:
                            if st.button("🔘 Label dataset", key=key):
                                st.session_state.selected_dataset = {
                                    "csv_path": csv_path,
                                    "images_folder": images_folder,
                                    "folder_name": folder_name,
                                    "location": location,
                                    "range": range_miles
                                }
                                st.rerun()
                    
                    st.divider()
                    if st.button("🔒 Logout", key="logout_button_top"):
                        for key in list(st.session_state.keys()):
                            del st.session_state[key]
                        st.rerun()


    else:
        sel = st.session_state.selected_dataset
        st.title(f"📦 Labeling App")

        df = pd.read_csv(sel['csv_path'])

        # Converting floats to strings in dataset for listings

        df['binary_flag'] = df['binary_flag'].astype(str)
        df['user_name'] = df['user_name'].astype(str)
        df['timestamp'] = df['timestamp'].astype(str)

        total = len(df)
        labeled = df['binary_flag'].notna().sum()
        st.progress(labeled / total if total else 0, text=f"{labeled} out of {total} listings labeled")

        not_labeled = df[df['binary_flag'].isna()].reset_index(drop=True)

        container1 = st.container(border=True)
        container1.header(f"Dataset: {sel['location']} ({sel['range']}) | {sel['folder_name'].replace('_', '/')}")

        if not_labeled.empty:
            st.info("🎉 All listings have been labeled!")

            # ✅ Clear DataFrame from memory
            del df

            st.divider()
            if st.button("⬅️ Back to Datasets"):
                    del st.session_state.selected_dataset
                    st.rerun()
            if st.button("🔒 Logout", key="logout_button_bottom"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        else:
            row = not_labeled.iloc[0]
            image_name = os.path.basename(row['photo_url'])
            image_path = os.path.join(sel['images_folder'], image_name)

            if os.path.exists(image_path):
                container = st.container(border=True)
                container.subheader(f"**Title:** {row['title']}")
                container.write(f"**Price:** {row['price']}")
                container.write(f"**Location:** {row['location']}")
                container.image(image_path, use_container_width=False)
                container.write(f"**[View Listing]({row['listing_url']})**")

                label = st.radio("Is this item likely stolen?", ["Yes", "No"])

            else:
                st.warning(f"⚠️ Image not found: {image_name}")

            if st.button("Submit Label", type="primary"):
                idx = df[(df['listing_url'] == row['listing_url']) & (df['photo_url'] == row['photo_url'])].index[0]
                df.at[idx, 'binary_flag'] = label
                df.at[idx, 'user_name'] = st.session_state.user_username
                df.at[idx, 'timestamp'] = datetime.now().isoformat()

                # ✅ Write changes back to the original file
                df.to_csv(sel['csv_path'], index=False)

                # ✅ Clear DataFrame from memory
                del df

                st.success("Label submitted!")
                st.rerun()

            st.divider()

            if st.button("⬅️ Back to Datasets"):
                    del st.session_state.selected_dataset
                    st.rerun()

            if st.button("🔒 Logout", key="logout_button_bottom"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    
