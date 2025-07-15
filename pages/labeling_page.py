import streamlit as st
import pandas as pd
import sys
import os
import re
from datetime import datetime
import drive_utils as du
import base64
import math
# import streamlit_extras
# from streamlit_extras.let_it_rain import rain

st.set_page_config(page_title="Labeling App", layout="wide")

# Hide the sidebar completely
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

if "selected_dataset" not in st.session_state:
    st.warning("Please select a dataset first.")
    st.switch_page("pages/welcome.py")
    st.stop()

sel = st.session_state.selected_dataset

# MAIN TITLE

col1, col2, col3 = st.columns([4, 1, 0.7])  # side space, center title, side button

with col1:
    st.title("📦 Labeling App")

with col3:
    st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)  # vertical alignment fix
    if st.button("💾 Save Progress", key="save_progress_side"):
        try:
            with st.spinner("Saving Progress...", show_time=True):
                du.upload_csv(df.copy(), sel['drive_file'], sel['drive_folder_id'])
            st.success("Progress saved to Google Drive!")
            st.session_state.progress_saved = True
        except Exception as e:
            st.error(f"Failed to upload: {e}")
    

if "current_df" not in st.session_state:
    st.header("Current df not in the system")
    st.session_state.current_df = du.download_csv(sel['drive_file'], sel['drive_folder_id'])

df = st.session_state.current_df

total = len(df[df['image_exist'] == True])
labeled = df[(df['binary_flag'].notna()) & (df['image_exist'] == True)].shape[0] if 'binary_flag' in df.columns else 0

if "recent_labeled_df" not in st.session_state:
    display_labeled = labeled
else:
    recent_df = st.session_state.recent_labeled_df
    display_labeled = recent_df[(recent_df['binary_flag'].notna()) & (recent_df['image_exist'] == True)].shape[0] if 'binary_flag' in recent_df.columns else 0

# PROGRESS BAR

st.progress(display_labeled / total if total else 0, text=f"{display_labeled} out of {total} listings labeled")

df_with_image = df[df['image_exist'] == True].reset_index(drop=True)

not_labeled = df_with_image[df_with_image['binary_flag'].isna()].reset_index(drop=True)

# HEADER DATASET INFO

col1, col2, col3, col4 = st.columns([4, 3, 1.5, 0.7])
with col1:
    st.markdown(
        f"""
        <div style=" font-size:28px; font-weight:500; margin-bottom:18px;">
            Dataset: {sel['location']} ({sel['range']}) | {sel['folder_name'].replace('_', '/')}
        </div>
        """, unsafe_allow_html=True
    )

if "labels_submitted" in st.session_state and st.session_state.labels_submitted == True:
    with col3:
        st.markdown("""
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        border: 0px solid #4CAF50;
        background-color: #eafbea;
        color: #2e7d32;
        font-size: 15px;
        font-weight: 500;
        padding: 7px 10px;
        border-radius: 7px;
        margin-top: 0px;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    ">
        ✅ Labels Submitted!
    </div>
""", unsafe_allow_html=True)
        
    with col4: 
        if st.button("➡️ Next"):
            st.session_state.labels_submitted = False
            st.session_state.current_df = st.session_state.recent_labeled_df
            # st.session_state.recent_labeled_df = ""
            st.rerun()

st.markdown("<hr style='margin:1px 0;' />", unsafe_allow_html=True)

# Total pages based on df_with_image (entire set of listings with images)
items_per_page = 25
total_pages = math.ceil(total / items_per_page)  # ceiling division

# Finding the page number
page_calculation = math.ceil(labeled / items_per_page) + 1

if page_calculation > total_pages:
     st.session_state.page_number = total_pages
else:
    st.session_state.page_number = page_calculation

# PAGINATION

start_idx = 0
if total_pages > page_calculation:
    end_idx = start_idx + 25
else:
    end_idx = start_idx + (total - labeled)

print("Start and End Indexes for upcoming page: ", start_idx, end_idx)

page_df = not_labeled.iloc[start_idx:end_idx].copy()
# st.write(page_df)

current_page = st.session_state.page_number 

# Display title + pagination
st.markdown(
    f"""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div style="font-size: 28px; font-weight: 600;">Listings</div>
        <div style="font-size: 16px; color: gray;">Page {current_page} of {total_pages}</div>
    </div>
    """,
    unsafe_allow_html=True
)

if labeled == total:
    # du.upload_csv(df.copy(), sel['drive_file'], sel['drive_folder_id'])
    # rain(emoji="🎉", font_size = 54, falling_speed = 5, animation_length = 10)
    st.success("🎉 All listings have been labeled and uploaded to the drive successfully!")

# Create 5x5 grid
num_cols = 5
rows = [page_df[i:i+num_cols] for i in range(0, len(page_df), num_cols)]
# st.markdown(f"row numbers: {rows}")

# Setup dictionary to store new labels
if "batch_labels" not in st.session_state:
    st.session_state.batch_labels = {}

# Creating each listing using the rows in the df

for row_df in rows:
    cols = st.columns(num_cols)
    for idx, col in enumerate(cols):
        if idx < len(row_df):
            listing = row_df.iloc[idx]
            uid = f"{listing['listing_url']}__{listing['photo_url']}"
            image_name = os.path.basename(listing['photo_url'])
            image_path = os.path.join(sel['images_folder'], image_name)

            # Checkbox outside the HTML so Streamlit can capture its state
            # if f"batch_labels[{uid}]" not in st.session_state:
            if uid not in st.session_state.batch_labels:
                # if st.session_state.batch_labels[uid]
                st.session_state.batch_labels[uid] = False

            # Determine current state
            is_selected = st.session_state.batch_labels[uid]

            # Define appearance
            label = "✅ Likely Stolen" if is_selected else "⬜ Likely Stolen"
            button_type = "primary" if is_selected else "secondary"

            # Create the border status for each listing co
            if st.session_state.batch_labels[uid] == True:
                border_style = "4px solid steelblue"
            else:
                border_style = "4px solid white"

            # st.markdown(f"{uid}")
            
            # Capturing the state of the selected item

            with col.container(height=400, border=False):
                if os.path.exists(image_path):

                    # Read image file in binary mode
                    with open(image_path, "rb") as image_file:
                        encoded_image = base64.b64encode(image_file.read()).decode()

                    # Build the HTML string for the container
                    if str(listing['price']) == "Free":
                        price = str(listing['price'])
                        html = f"""
                    <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                        <img src="data:image/jpeg;base64,{encoded_image}" style="width: 100%; border-radius: 10px; margin-bottom: 10px; border: {border_style};" />
                        <div style="font-weight: bold; font-size: 16px; margin-bottom: 5px;">
                            {price}
                        </div>
                        <div style="font-size: 14px; margin-bottom: 3px;">
                            {listing["title"]}
                        </div>
                        <div style="font-size: 13px; color: #666; margin-bottom: 10px;">
                            {listing["location"]}
                        </div>
                    """
                    else: 
                        price = float(str(listing['price']).replace("$", "").replace(",", "").strip())    
                        html = f"""
                    <div style="display: flex; flex-direction: column; justify-content: space-between; height: 100%;">
                        <img src="data:image/jpeg;base64,{encoded_image}" style="width: 100%; border-radius: 10px; margin-bottom: 10px; border: {border_style};" />
                        <div style="font-weight: bold; font-size: 16px; margin-bottom: 5px;">
                            ${price:,.2f}
                        </div>
                        <div style="font-size: 14px; margin-bottom: 3px;">
                            {listing["title"]}
                        </div>
                        <div style="font-size: 13px; color: #666; margin-bottom: 10px;">
                            {listing["location"]}
                        </div>
                    """
                    st.markdown(html, unsafe_allow_html=True)                 

                # Capturing the state of the selected item
                if st.button(label, key=f"btn_{uid}", type=button_type):
                    st.session_state.batch_labels[uid] = not is_selected
                    st.rerun()

if "labels_submitted" not in st.session_state:
    st.session_state.labels_submitted = False

col1, col2, col3, col4, col5, col6, col7 = st.columns([2,2,2,2.3,2, 2,2])
with col4:
    if st.session_state.labels_submitted == False:
        if st.button("**✅ Submit Labels**", type="secondary"):
            listing = 0
            # Copying original dataframe 
            copy_df  = df.copy(deep=True)
            for row in page_df.itertuples():
                uid = f"{row.listing_url}__{row.photo_url}"
                is_stolen = st.session_state.batch_labels.get(uid)

                index = copy_df[(copy_df['listing_url'] == row.listing_url) & (copy_df['photo_url'] == row.photo_url)].index
                if not index.empty:
                    listing += 1
                    copy_df.at[index[0], 'binary_flag'] = "Yes" if is_stolen else "No"
                    copy_df.at[index[0], 'user_name'] = str(st.session_state.user_username)
                    copy_df.at[index[0], 'timestamp'] = datetime.now().isoformat()

            #rain(emoji="🎉", font_size = 54, falling_speed = 5, animation_length = 10)        
            st.session_state.labels_submitted = True
            st.session_state.progress_saved = False
            st.session_state.recent_labeled_df = copy_df
            st.session_state.batch_labels = {}
            st.rerun()
    else:
        if st.button("✅ Submit Labels", type="secondary"):
            st.success("🎉 Labels resubmitted")

with col6:
    if st.session_state.labels_submitted == True:
        st.markdown("""
    <div style="
        display: flex;
        justify-content: center;
        align-items: center;
        border: 0px solid #4CAF50;
        background-color: #eafbea;
        color: #2e7d32;
        font-size: 15px;
        font-weight: 500;
        padding: 7px 10px;
        border-radius: 7px;
        margin-top: 0px;
        width: fit-content;
        margin-left: auto;
        margin-right: auto;
    ">
        ✅ Labels Submitted!
    </div>
""", unsafe_allow_html=True)

with col7:
    if st.session_state.labels_submitted == True:
        if st.button("➡️ Next Page", type="secondary"):
            st.session_state.labels_submitted = False
            st.session_state.current_df = st.session_state.recent_labeled_df
            # st.session_state.recent_labeled_df = ""
            st.rerun()

st.markdown("<hr style='margin:1px 0;' />", unsafe_allow_html=True)

if labeled < total:
    if st.button("💾 Save Progress", key="save_progress_bottom"):
        try:
            with st.spinner("Saving Progress...", show_time=True):
                df_tosave = st.session_state.recent_labeled_df
                du.upload_csv(df_tosave, sel['drive_file'], sel['drive_folder_id'])
            st.success("Progress saved to Google Drive!")

            st.session_state.progress_saved = True

        except Exception as e:
            st.error(f"Failed to upload: {e}")

# st.markdown("<hr style='margin:1px 0;' />", unsafe_allow_html=True)

if st.button("⬅️ Back to Datasets"):
    # print("Status of progress saved: ", st.session_state.progress_saved)
    # if st.session_state.progress_saved == False:
    if "recent_labeled_df" not in st.session_state:
        st.switch_page("pages/welcome.py")
    else:
        if "progress_saved" not in st.session_state or st.session_state.progress_saved == False:
            try:
                with st.spinner("Saving Progress...", show_time=True):
                    df_tosave = st.session_state.recent_labeled_df
                    du.upload_csv(df_tosave, sel['drive_file'], sel['drive_folder_id'])
                st.success("Progress saved to Google Drive!")
                st.session_state.label_submitted = False
                st.session_state.progress_saved = True
                del st.session_state.selected_dataset
                st.switch_page("pages/welcome.py")
            except Exception as e:
                st.error(f"Failed to upload: {e}")
        else:
            st.switch_page("pages/welcome.py")

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