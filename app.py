# app.py (mixed version: listings from GitHub folder, users.csv from Google Drive)

import streamlit as st
import pandas as pd
import sys
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

def reset_local_dataframes():
    for key in list(st.session_state.keys()):
        if key.startswith("local_df_") or key == "current_df":
            del st.session_state[key]

# --- Login ---
users_df = None
if "user_name" not in st.session_state:
    reset_local_dataframes()
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
            if users_df.empty:
                st.error("Could not load users.csv from Google Drive.")
                st.stop()

            match = users_df[(users_df['user_name'] == username) & (users_df['password'] == password)]
            if not match.empty:
                st.session_state.user_name = match.iloc[0]['name']
                st.session_state.user_username = username
                st.session_state.root_folder_id = folder_id
                reset_local_dataframes()
                st.rerun()
            else:
                st.error("Invalid credentials")

else:
    if "selected_dataset" not in st.session_state:
        st.title(f"👋 Welcome, {st.session_state.user_name}!")
        st.markdown("This app is designed to label marketplace listings to help determine if an item might be stolen.")

        st.subheader("📜 Datasets")
        header_cols = st.columns([2, 1, 2, 1, 1, 3])
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
                    else:
                        df = None

                    # If there is no df in the Drive creates a copy of the local df with the new columns
                    if df is None:
                        df_original = pd.read_csv(csv_path)
                        df = df_original.copy()
                        df['image_exist'] = df['photo_url'].apply(lambda x: os.path.exists(os.path.join(images_folder, os.path.basename(str(x)))) if isinstance(x, str) or not pd.isna(x) else False)
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
                        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 2, 1, 1, 3])
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
                                    st.rerun()
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
                                    st.rerun()

        st.divider()
        if st.button("🔒 Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    else:
        sel = st.session_state.selected_dataset
        st.title(f"📦 Labeling App")

        if "current_df" not in st.session_state:
            st.session_state.current_df = du.download_csv(sel['drive_file'], sel['drive_folder_id'])

        df = st.session_state.current_df
        total = len(df[df['image_exist'] == True])
        labeled = df[(df['binary_flag'].notna()) & (df['image_exist'] == True)].shape[0] if 'binary_flag' in df.columns else 0

        st.progress(labeled / total if total else 0, text=f"{labeled} out of {total} listings labeled")

        df_with_image = df[df['image_exist'] == True].reset_index(drop=True)

        not_labeled = df_with_image[df_with_image['binary_flag'].isna()].reset_index(drop=True)

        st.subheader(f"Dataset: {sel['location']} ({sel['range']}) | {sel['folder_name'].replace('_', '/')} ")

        if not_labeled.empty:
            try:
                du.upload_csv(df.copy(), sel['drive_file'], sel['drive_folder_id'])
                st.success("🎉 All listings have been labeled and uploaded to the drive successfully!")
            except Exception as e:
                st.error(f"Failed to submit labels: {e}")

        else:
            row = not_labeled.iloc[0]
            image_name = os.path.basename(row['photo_url'])
            image_path = os.path.join(sel['images_folder'], image_name)

            image_exists = row['image_exist']
            print("Does the next listing have an image?", image_exists)
            sys.stdout.flush()

            # import pdb; pdb.set_trace()

            if row['image_exist'] == True:
                try:
                    if os.path.exists(image_path):
                        container1 = st.container(border=True)
                        container1.subheader(f"{row['title']}")
                        container1.write(f"**Price:** {row['price']}")
                        container1.write(f"**Location:** {row['location']}")
                        container1.image(image_path, use_container_width=False)
                        container1.write(f"**[View Listing]({row['listing_url']})**")
                    else:
                        idx = df[(df['listing_url'] == row['listing_url']) & (df['photo_url'] == row['photo_url'])].index[0]
                        df.at[idx, 'image_exist'] = False
                        st.session_state.current_df = df
                        st.rerun()
                except Exception as e:
                    st.warning(f"⚠️ Could not load image: {e}")
                    idx = df[(df['listing_url'] == row['listing_url']) & (df['photo_url'] == row['photo_url'])].index[0]
                    df.at[idx, 'image_exist'] = False
                    st.session_state.current_df = df
                    st.rerun()
            else:
                st.rerun()

            container2 = st.container(border=True)

            label = container2.radio("Is this item likely stolen?", ["Yes", "No"])

            # Initialize in session if not already stored
            if "current_df" not in st.session_state:
                st.session_state.current_df = df.copy()

            # Replace df with session copy
            df = st.session_state.current_df

            idx = df[(df['listing_url'] == row['listing_url']) & (df['photo_url'] == row['photo_url'])].index[0]
            print("The binary flag for this listing with index: ", idx, " is ", df.at[idx, 'binary_flag'])

            # Initialize the current listing ID
            current_listing_id = f"{row['listing_url']}__{row['photo_url']}"
            # Check if current listing ID and the listing id of the labeled row are the same
            is_same_listing = st.session_state.get("last_labeled_id", "") == current_listing_id

            if st.session_state.get("label_submitted", False) and is_same_listing:
                st.info("✅ Label already submitted")
                btn_lbl_text = "Re-submit Label"
            else:
                st.session_state.label_submitted = False  # reset if it's a new listing
                btn_lbl_text = "Submit Label"

            col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1,0.5])
            
            with col1:
                btnSubmit = st.button(btn_lbl_text, type='secondary')
                if btnSubmit:
                    try:
                        idx = df[(df['listing_url'] == row['listing_url']) & (df['photo_url'] == row['photo_url'])].index[0]
                        df.at[idx, 'binary_flag'] = str(label)
                        df.at[idx, 'user_name'] = str(st.session_state.user_username)
                        df.at[idx, 'timestamp'] = datetime.now().isoformat()

                        st.session_state.progress_saved = False
                        st.session_state.label_submitted = True
                        st.session_state.last_labeled_id = current_listing_id  # ← TRACK this listing specifically

                    except Exception as e:
                        st.error(f"Error: {e}")

            with col2:
                if st.session_state.get("label_submitted", False):
                        if st.button("Next Listing"):

                            st.session_state.label_submitted = False
                            st.session_state.last_labeled_id = ""
                            st.rerun()
            
            if st.session_state.get("label_submitted", False):
                st.success(f"Label Successfully Submitted!")

        print("OIIII")
        st.divider()

        print("Total listings labeled: ", labeled)
        print("Total listings: ", total)

        if labeled < total:
            if st.button("💾 Save Progress"):
                try:
                    with st.spinner("Saving Progress...", show_time=True):
                        du.upload_csv(df.copy(), sel['drive_file'], sel['drive_folder_id'])
                    st.success("Progress saved to Google Drive!")

                    st.session_state.progress_saved = True

                except Exception as e:
                    st.error(f"Failed to upload: {e}")
        else:
            try:
                du.upload_csv(df.copy(), sel['drive_file'], sel['drive_folder_id'])
                st.success("🎉 All listings have been labeled and uploaded to the drive successfully!")
            except Exception as e:
                st.error(f"Failed to submit labels: {e}")

        st.divider()
        if st.button("⬅️ Back to Datasets"):
            print("Status of progress saved: ", st.session_state.progress_saved)
            if st.session_state.progress_saved == False:
                try:
                    with st.spinner("Saving Progress...", show_time=True):
                        du.upload_csv(df.copy(), sel['drive_file'], sel['drive_folder_id'])
                    st.success("Progress saved to Google Drive!")
                    st.session_state.label_submitted = False
                    st.session_state.progress_saved = True
                    del st.session_state.selected_dataset
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to upload: {e}")
            else:
                del st.session_state.selected_dataset
                st.rerun()

     # Ask user if they want to save progress before logout
        with st.popover("🔒 Logout",):
            if st.button("💾 Save and Logout", key="btn_save_logout"):
                print("Button save and logout clicked")
                try:
                    with st.spinner("Saving Progress...", show_time=True):
                        du.upload_csv(df.copy(), sel['drive_file'], sel['drive_folder_id'])
                    st.success("Progress saved to Google Drive!")
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to upload labeled listings to Google Drive: {e}")
            if st.button("❌ Logout Without Saving", key="btn_logout_no_save"):
                print("Button logout clicked")
                st.write("You will be logged out")
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


            
                    
