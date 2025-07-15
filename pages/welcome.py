import streamlit as st
import pandas as pd
import sys
import os
import re
from datetime import datetime
import drive_utils as du

if "user_name" not in st.session_state:
    st.switch_page("pages/login.py")

# GitHub folder config (dataset folders pushed with the app)
DATASETS_DIR = os.path.join(os.getcwd(), "Data")

st.set_page_config(page_title="Welcome", layout="wide")

# Hide the sidebar completely
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

spacer_col1, content_col, spacer_col2 = st.columns([1, 6, 1])
with content_col:
    st.title(f"👋 Welcome, {st.session_state.user_name}!")
    st.markdown("This app is designed to label marketplace listings to help determine if an item might be stolen.")
    
    st.subheader("📜 Datasets")

    header_cols = st.columns([1.2, 1, 1, 1, 0.8, 1.9,1.8])
    headers = ["City", "Range", "Date", "Labeled", "Total", "Action", "Download"]
    
    for col, label in zip(header_cols, headers):
        col.markdown(f"<div style='margin-bottom: 0.8rem'><strong>{label}</strong></div>", unsafe_allow_html=True)

    if os.path.exists(DATASETS_DIR):
        for folder_name in sorted(os.listdir(DATASETS_DIR), reverse=True):
            if not folder_name.startswith("20"):
                continue

            folder_path = os.path.join(DATASETS_DIR, folder_name)
            if not os.path.isdir(folder_path):
                continue

            for file in os.listdir(folder_path):
                # Skip dataset if its images folder doesn't exist
                images_folder = os.path.join(folder_path, file.replace(".csv", "_files"))
                if not os.path.exists(images_folder):
                    continue
                if not file.endswith(".csv"):
                    continue

                csv_path = os.path.join(folder_path, file)
                images_folder = os.path.join(folder_path, file.replace(".csv", "_files"))

                location_parts = file.replace(".csv", "").split("_")
                location = " ".join(location_parts[:-1]).title()
                range_miles = location_parts[-1]

                drive_folder_id = du.get_folder_id_by_name(folder_name, parent_id=st.session_state.root_folder_id)
                if not drive_folder_id:
                    drive_folder_id = du.create_drive_folder(folder_name, st.session_state.root_folder_id)

                labeled_file_id = du.get_file_id_by_name(file, drive_folder_id)
                local_key = f"local_df_{file}"

                # If there is a df in the Drive download this csv and check again for any updates in the images in the folder
                if labeled_file_id:
                    labeled_df = du.download_csv(file, drive_folder_id)
                    df = labeled_df.copy() if not labeled_df.empty else None
                    # Checks for any update in the image folders in case new pictures were added or deleted
                    df['image_exist'] = df['photo_url'].apply(lambda x: os.path.exists(os.path.join(images_folder, os.path.basename(x))) if isinstance(x, str) else False)
                    #df['image_exist'] = df['photo_url'].apply(lambda x: check_image_exists(x, images_folder))

                    length = len(df[df['image_exist'] == True])
                else:
                    df = None

                # If there is no df in the Drive creates a copy of the local df with the new columns
                if df is None:
                    df_original = pd.read_csv(csv_path)
                    df = df_original.copy()
                    # Checks how many images actually exist with the file path from the photo_url column
                    df['image_exist'] = df['photo_url'].apply(lambda x: os.path.exists(os.path.join(images_folder, os.path.basename(str(x)))) if isinstance(x, str) or not pd.isna(x) else False)
                    #df['image_exist'] = df['photo_url'].apply(lambda x: check_image_exists(x, images_folder))

                    df['user_name'] = pd.Series([pd.NA] * len(df), dtype="string")
                    df['binary_flag'] = pd.Series([pd.NA] * len(df), dtype="string")
                    df['timestamp'] = pd.Series([pd.NA] * len(df), dtype="string")


                st.session_state[local_key] = df

                total = len(df[df['image_exist'] == True])
                labeled = df[(df['binary_flag'].notna()) & (df['image_exist'] == True)].shape[0] if 'binary_flag' in df.columns else 0
                file_in_drive = labeled_file_id is not None

                if total == 0:
                    continue
                else:
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1, 1, 1, 0.8, 1.9,1.8])
                    with col1: st.write(location)
                    with col2: st.write(range_miles)
                    with col3: st.write(folder_name.replace("_", "/"))
                    with col4: st.write(labeled if file_in_drive else 0)
                    with col5: st.write(total)
                    with col6:
                        key = f"select_{folder_name}_{file}"
                        if not file_in_drive:
                            if st.button("🚀 Start Labeling", key=key):
                                du.upload_csv(df, file, drive_folder_id)
                                st.session_state.selected_dataset = {
                                    "csv_path": csv_path,
                                    "images_folder": images_folder,
                                    "folder_name": folder_name,
                                    "location": location,
                                    "range": range_miles,
                                    "drive_file": file,
                                    "drive_folder_id": drive_folder_id
                                }
                                st.session_state.current_df = df
                                st.switch_page("pages/labeling_page.py")
                        elif labeled == total and total > 0:
                            st.button("✅ Complete", key=key, disabled=True)
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
                                st.session_state.current_df = df
                                st.switch_page("pages/labeling_page.py")
                    with col7:
                            csv_bytes = df.to_csv(index=False).encode("utf-8")
                            st.download_button(
                                label="⬇️ Download CSV",
                                data=csv_bytes,
                                file_name=file,
                                mime="text/csv",
                                key=f"download_{file}"
                            )
            
        st.divider()
        if st.button("🔒 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

