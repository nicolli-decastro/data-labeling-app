import streamlit as st
import pandas as pd
import sys
import os
import re
from datetime import datetime
import drive_utils as du

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
# Capture the button click
logout_clicked = st.sidebar.button("Logout", use_container_width=True)

# If it was clicked, clear session_state and rerun
if logout_clicked:
    # remove everything
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# -- PAGE START

if "user_name" not in st.session_state:
    st.switch_page("pages/login.py")

# GitHub folder config (dataset folders pushed with the app)
DATASETS_DIR = os.path.join(os.getcwd(), "Data")

st.set_page_config(page_title="Datasets for Label", layout="wide")

spacer_col1, content_col, spacer_col2 = st.columns([0.2, 7, 0.2])
with content_col:
    # Title & Description
    st.title("📝 Label Your Marketplace Datasets")
    
    st.markdown(
        """
        <div style="font-size: 17px; color: #555;">
                Select a dataset from the available options to begin labeling marketplace listings 
                for suspicious or likely stolen items. You can: 
            </p>
            <p style="font-size: 16px; line-height: 1.6; margin-top: 1rem;">
                <span style="display: block;">🔍 <strong>Browse</strong> available datasets</span>
                <span style="display: block;">🖊️ <strong>Label</strong> items directly in the app</span>
                <span style="display: block;">📥 <strong>Download</strong> labeled datasets as CSV files</span>
                <span style="display: block;">📊 <strong>Visualize</strong> trends in the Data Visualization page</span>
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<hr style='margin-top: 0px;'>", unsafe_allow_html=True)

    st.subheader("📜 Datasets")

    header_cols = st.columns([1.2, 0.8, 1, 1, 0.8, 1.9,1.8])
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
                print(images_folder)

                if not os.path.exists(images_folder):
                    continue
                if not file.endswith(".csv"):
                    continue

                csv_path = os.path.join(folder_path, file)
                images_folder = os.path.join(folder_path, file.replace(".csv", "_files"))

                # New logic to support merged/national datasets
                location_parts = file.replace(".csv", "").split("_")

                if len(location_parts) >= 3 and location_parts[-1].endswith("mi"):
                    # Standard city_state_miles format
                    location = " ".join(location_parts[:-1]).title()
                    range_miles = location_parts[-1]
                else:
                    # Fallback for merged or national datasets
                    location = " ".join(location_parts).title()
                    range_miles = "Merged"

                drive_folder_id = du.get_folder_id_by_name(folder_name, parent_id=st.session_state.root_folder_id)
                
                if not drive_folder_id:
                    drive_folder_id = du.create_drive_folder(folder_name, st.session_state.root_folder_id)

                labeled_file_id = du.get_file_id_by_name(file, drive_folder_id)
                date = folder_name.replace("_", "/")
                local_key = f"local_df_{date}_{file}"

                # If there is a df in the Drive download this csv and check again for any updates in the images in the folder
                if labeled_file_id:
                    labeled_df = du.download_csv(file, drive_folder_id)
                    df = labeled_df.copy() if not labeled_df.empty else None

                    if df is not None:
                        # Ensure required columns exist
                        if 'user_name' not in df.columns:
                            df['user_name'] = pd.Series([pd.NA] * len(df), dtype="string")
                        if 'binary_flag' not in df.columns:
                            df['binary_flag'] = pd.Series([pd.NA] * len(df), dtype="string")
                        if 'timestamp' not in df.columns:
                            df['timestamp'] = pd.Series([pd.NA] * len(df), dtype="string")
                        if 'image_exist' not in df.columns:
                            df['image_exist'] = pd.Series([False] * len(df))
                        
                        # Create a set of all image filenames in the folder
                        image_files = set(os.listdir(images_folder))

                        def match_image_exists(photo_url):
                            if not isinstance(photo_url, str) or pd.isna(photo_url):
                                return False

                            photo_name = os.path.basename(photo_url).strip()

                            # DEBUG: Check sample match attempts
                            for img in image_files:
                                if img.endswith(photo_name):
                                    return True
                            return False

                        df['image_exist'] = df['photo_url'].apply(match_image_exists)
                        print(f"Number of images that are matched: {len(df[df['image_exist'] == True])}")

                        length = len(df[df['image_exist'] == True])
                else:
                    df = None

                # If there is no df in the Drive creates a copy of the local df with the new columns
                if df is None:
                    df_original = pd.read_csv(csv_path)
                    df = df_original.copy()

                    df['user_name'] = pd.Series([pd.NA] * len(df), dtype="string")
                    df['binary_flag'] = pd.Series([pd.NA] * len(df), dtype="string")
                    df['timestamp'] = pd.Series([pd.NA] * len(df), dtype="string")

                    # Create a set of all image filenames in the folder
                    image_files = set(os.listdir(images_folder))

                    def match_image_exists(photo_url):
                        if not isinstance(photo_url, str) or pd.isna(photo_url):
                            return False

                        photo_name = os.path.basename(photo_url).strip()

                        # DEBUG: Check sample match attempts
                        for img in image_files:
                            if img.endswith(photo_name):
                                return True
                        return False

                    df['image_exist'] = df['photo_url'].apply(match_image_exists)
                    print(f"Number of images that are matched: {len(df[df['image_exist'] == True])}")

                st.session_state[local_key] = df

                total = len(df[df['image_exist'] == True])
                labeled = df[(df['binary_flag'].notna()) & (df['image_exist'] == True)].shape[0] if 'binary_flag' in df.columns else 0
                file_in_drive = labeled_file_id is not None

                if total == 0:
                    continue
                else:
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 0.8, 1, 1, 0.8, 1.9,1.8])
                    with col1: st.write(f"**{location}**")
                    with col2: st.write(range_miles)
                    with col3: st.write(f"**{date}**")
                    with col4:
                        st.markdown(f"""
                            <div style="
                                display: flex;
                                margin-left: 5px;
                                align-items: center;
                                height: 100%;  /* Optional: define height if vertical centering isn't working */
                            ">
                                {labeled if file_in_drive else 0}
                            </div>
                        """, unsafe_allow_html=True)
                    with col5: st.write(total)
                    with col6:
                        key = f"select_{folder_name}_{file}"
                        if not file_in_drive or labeled == 0:
                            if st.button("🚀 Start Labeling", key=key):
                                try:
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
                                    st.session_state.file_missing = False

                                except Exception as e:
                                    if (
                                        hasattr(e, "resp") 
                                        and hasattr(e, "content") 
                                        and "storageQuotaExceeded" in str(e.content)
                                    ):
                                        st.session_state.file_missing = True
                                        st.warning(
                                            f"⚠️ File **{file}** missing from Google Drive: Please add this CSV to the folder **{folder_name}**."
                                        )
                                else:
                                    st.error("An unexpected error occurred during upload.")
                                    st.exception(e)

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
                        if "file_missing" not in st.session_state:
                            disabled = False
                        else:
                            if st.session_state.file_missing == True:
                                disabled = True
                            else:
                                disabled = False
                        csv_bytes = df.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            label="⬇️ Download CSV",
                            disabled=disabled,
                            data=csv_bytes,
                            file_name=file,
                            mime="text/csv",
                            key=f"download_{date}_{file}"
                        )            
        st.divider()
        if st.button("🔒 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

