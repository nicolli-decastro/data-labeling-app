import streamlit as st
import pandas as pd
import zipfile
import os

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

# --- Check user session ---

import glob

# Create user upload folder if not exists
if "user_username" not in st.session_state:
    st.switch_page("pages/login.py")

# -- FIND FILES UNDER USER FOLDER

username = st.session_state.user_username
base_path = os.path.join("uploaded_data", username)
os.makedirs(base_path, exist_ok=True)

# --- Find current CSV and ZIP (one of each max) ---
existing_csvs = glob.glob(os.path.join(base_path, "*.csv"))
existing_zips = glob.glob(os.path.join(base_path, "*.zip"))

# Detect existing CSV and ZIP
# Exclude any CSVs that are model result files
csv_files = [
    f for f in os.listdir(base_path)
    if f.endswith(".csv") and "model_results" not in f
]
zip_files = [f for f in os.listdir(base_path) if f.endswith(".zip")]
result_file = [
    f for f in os.listdir(base_path)
    if f.endswith(".csv") and "model_results" in f
]

# -- CHECK IF FILES EXIST
csv_exists = len(csv_files) > 0
zip_exists = len(zip_files) > 0
result_exists = len(result_file) > 0

# -- FIND FILE PATHS
csv_path = os.path.join(base_path, csv_files[0]) if csv_exists else None
zip_path = os.path.join(base_path, zip_files[0]) if zip_exists else None
result_path = os.path.join(base_path, result_file[0]) if result_exists else None

# -- FIND FILE NAMES         
csv_filename = os.path.basename(csv_path) if csv_exists else None
zip_filename = os.path.basename(zip_path) if zip_exists else None
result_filename = os.path.basename(result_path) if result_exists else None

if csv_exists:
    # Step 1: Load the original CSV
    df_original = pd.read_csv(csv_path)
    total_original = len(df_original)

df_result = None
if result_exists:
    # Load the results file if exist and compare results
    df_result = pd.read_csv(result_path)
    labeled_count = len(df_result)
    remaining = total_original - labeled_count

# -- ACTUAL PAGE CONTENT STARTS

col1, col2, col3 = st.columns([0.2,3,0.2])

with col2:
    st.set_page_config(page_title="AI Evaluation Upload", layout="wide")
    st.title("🤖 Upload Listings for AI Evaluation")

    tab1, tab2 = st.tabs(["About the Tool", "Upload Files"])
    with tab1:
        st.markdown(
            f"""<div style="margin-bottom: 1.5rem;">
        <h4>🧠 About the AI Evaluation Tool</h4>
        <p>
            This tool uses an AI model to evaluate marketplace listings and identify potentially suspicious or stolen items.
            It analyzes listing details and associated images to flag entries that may require further investigation.
        </p>
        <p><strong>To use the tool:</strong></p>
        <ol>
            <li>
            Upload a <strong>CSV file</strong> containing the listing data.<br>
            The CSV must include a column with the photo_url or image filename (e.g., abc123.jpg)
            that exactly matches the image names inside the ZIP file.
            </li>
            <li>
            Upload a <strong>ZIP file</strong> containing the product <strong>images</strong> referenced in the CSV.<br>
            Filenames must exactly match those listed in the CSV file.
            </li>
        </ol>
        <p>
            Once both files are uploaded and validated, the tool will run the AI model and provide insights through suspicion scores. You can then download the evaluated listings as a new CSV file.
        </p>
        </div>
        """,
        unsafe_allow_html=True)

        with st.container(border=True):
            # --- Display previously uploaded files ---
            st.subheader("📁 Current Uploaded Files")

            if csv_path:
                st.markdown(f"**CSV:** `{csv_filename}`")
            else:
                st.markdown("_No CSV uploaded yet._")

            if zip_path:
                st.markdown(f"**ZIP of Images:** `{zip_filename}`")
            else:
                st.markdown("_No ZIP file uploaded yet._")

    with tab2:

        with st.container(border=True):
            # --- Upload New CSV ---
            st.subheader("📤 Upload a CSV (Replaces Existing)")

            columns_required = {"photo_url", "price", "title", "location", "origin_city_list"}
            req_columns_html = f"""<div style="font-size: 14px; padding: 8px;">
                        <code>{columns_required}</code>
                    </p>
                    <p style="margin-top: 1rem; font-size: 15px;">
                        Optionally, your dataset can also include the <code>binary_flag</code> column for <strong>manually labeled results</strong>. 
                        If present, the app will allow you to compare human vs AI labeling outcomes side by side.
                    </p>
                </div>"""

            if result_exists and csv_exists:
                st.warning(f"⚠️ Found an AI result file: {result_path}  with {labeled_count} listings evaluated out of {total_original} by the AI model. If you upload a new file the current progress will be lost!")

            new_csv = st.file_uploader("Upload CSV", type=["csv"], key="csv")

            with st.expander("✅ Learn about required columns"):
                st.markdown(req_columns_html, unsafe_allow_html=True)

            if new_csv:
                # Delete old CSVs
                for f in existing_csvs:
                    os.remove(f)
                
                # Save new CSV
                save_path = os.path.join(base_path, new_csv.name)
                with open(save_path, "wb") as f:
                    f.write(new_csv.read())

                name_csv = new_csv.name

                # Clear the uploader’s session_state value
                del st.session_state["csv"]

                #  Reset any flags and rerun
                st.session_state.model_success = False
                st.session_state.new_csv = True
                st.rerun()
            
            #if "new_csv" in st.session_state and st.session_state.new_csv == True:
                # st.success(f"✅ New CSV saved as `{name_csv}`")

            # --- Validate CSV if uploaded ---
            if csv_exists:
                try:
                    # VALIDATE NAME: NO NAMES CONTAINING MODEL_RESULTS

                    df = pd.read_csv(csv_path)
                    required_cols = {"photo_url", "price", "title", "location", "origin_city_list"}
                    missing_cols = required_cols - set(df.columns)
                    if missing_cols:
                        st.error(f"🚫 Missing columns in CSV: {', '.join(missing_cols)}")
                        df = None
                    else:
                        st.success(f"✅ CSV `{csv_files[0]}` validated successfully.")
                except Exception as e:
                    st.error(f"🚫 Error reading CSV: {e}")
                    df = None
                    st.stop()
            else:
                df = None
        
        with st.container(border=True):

            # --- Upload New ZIP ---
            st.subheader("🖼️ Upload a ZIP of Images (Replaces Existing)")
            new_zip = st.file_uploader("Upload ZIP of images", type=["zip"], key="zip")

            if new_zip:
                # Delete old ZIPs
                for f in existing_zips:
                    os.remove(f)

                # Save new ZIP
                save_path = os.path.join(base_path, new_zip.name)
                with open(save_path, "wb") as f:
                    f.write(new_zip.read())
                
                # st.rerun()

                st.success(f"✅ New ZIP saved as `{new_zip.name}`")

            # Define extracted image folder
            images_folder = os.path.join(base_path, "extracted_images")
            images_extracted = os.path.exists(images_folder) and len(os.listdir(images_folder)) > 0

            # --- Step 4: Extract ZIP if not already extracted ---
            if zip_exists and not images_extracted:
                try:
                    os.makedirs(images_folder, exist_ok=True)
                    with st.spinner("🔧 Extracting images..."):
                        with zipfile.ZipFile(zip_path, "r") as zip_ref:
                            zip_ref.extractall(images_folder)
                            number_images = len(zip_ref.namelist()) - 1 # minus 1 is because the unzipped file is a nested folder, folder extracted_images > original zipped folder name > images as .png or .jpg 
                        st.success(f"✅ Extracted {number_images} images")
                        images_extracted = True
                        # st.rerun()
                except zipfile.BadZipFile:
                    st.error("🚫 Uploaded ZIP file is invalid.")
                    st.stop()

            # --- Step 6: Compare image filenames with CSV ---
            if df is not None and images_extracted:
                valid_exts = [".jpg", ".jpeg", ".png", ".webp"]
                extracted_images = {
                    fname.strip()
                    for root, _, files in os.walk(images_folder)
                    for fname in files
                    if os.path.splitext(fname)[1].lower() in valid_exts
                }

                df["image_filename"] = df["photo_url"].apply(
                    lambda x: os.path.basename(x).strip() if isinstance(x, str) and x else ""
                )
                df["image_exists"] = df["image_filename"].isin(extracted_images)

                matched = df["image_exists"].sum()
                total = len(df)
                missing = total - matched

                st.info(f"📸 {matched}/{total} listings have matching images.")

                # st.rerun()

                if missing > 0:
                    with st.expander("⚠️ Listings missing images"):
                        st.dataframe(df[~df["image_exists"]][["photo_url", "image_filename"]])

    st.divider()

    # --- ACTUAL AI MODEL SECTION

    from AI_Model_Files.label_Machine_test import run_model
    import AI_Model_Files.config as config
    from datetime import datetime

    # --- Final Check: Ready to run AI ---
    if csv_exists and images_extracted and "image_exists" in df.columns:

        # Keep only listings with images that exists
        df_to_evaluate = df[df["image_exists"] == True]

        # Number of total listings that have images to be evaluated
        total_rows = len(df_to_evaluate)

        st.markdown("## 🤖 Ready to Run AI Model")
        st.success("All inputs are validated. You can now run the AI model to evaluate the listings.")

        st.markdown("#### 🔢 Select Number of Listings to Analyze")

        col1, col2, col3, col4 = st.columns([2,0.5,1.5,0.5])

        with col3:
            if result_exists:
                with st.container(border=True):

                    st.markdown(f"""
                        <div style="
                            text-align: center;
                            padding: 1rem 0;
                            font-size: 18px;
                        ">
                            <div style="font-weight: 600; font-size: 20px;">
                                ✅ <span style="color:#262730;">{labeled_count:,}</span> of <span style="color:#262730;">{total_original:,}</span> listings processed
                            </div>
                            <div style="margin-bottom: 0.5rem; color: #666;">
                                {"✅ <b>All listings processed.</b>" if remaining == 0 else f"⏳ <b>{remaining:,}</b> remaining"}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No AI result file found yet. You can run the AI model to begin labeling.")

        with col1:
            max_to_process = st.number_input(
            "How many listings do you want to run through the AI model?",
            min_value=1,
            max_value=total_rows,
            value=min(500, total_rows),  # default value, like 500 or full if small
            step=50)

            if st.button("🚀 Run AI Model on Listings"):

                # Only create a result path in case one already does not exist
                print(f"Result file exists?? {result_exists}")
                if result_exists == False:
                    # Build filename using original CSV name
                    original_name = os.path.splitext(os.path.basename(csv_path))[0]
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    result_filename = f"{original_name}_model_results_{timestamp}.csv"
                    result_path = os.path.join(base_path, result_filename)

                with st.spinner("Running model... this may take a few minutes ⏳"):
                    try:
                        # Run your model
                        run_model(csv_path, images_folder, result_path, max_to_process=max_to_process)

                        st.session_state.model_success = True

                        st.rerun()

                    except Exception as e:
                        st.error(f"🚫 Error running model: {e}")
                        st.session_state.model_success = False
            
            if "model_success" in st.session_state:
                if st.session_state.model_success == True:
                    st.success("✅ Model completed successfully!")
                    with open(result_path, "rb") as f:
                        st.download_button("📥 Download Results", data=f, file_name=result_filename)
    else:
        st.warning("⚠️ Upload a valid CSV and ZIP file with matching images to enable model execution.")

