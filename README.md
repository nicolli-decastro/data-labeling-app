
# Data Labeling App – Loss Detection for Retailers

A Streamlit web application designed for retailers and researchers to label and evaluate potentially stolen marketplace listings (e.g., from Facebook Marketplace or Craigslist). This platform supports loss prevention efforts by enabling structured annotation, AI-driven analysis, and visual data exploration.


## What This App Does

Login System for secure access

- Manual Labeling of listings with CSV export
- AI Evaluation to flag suspicious items and resume interrupted runs
- Data Visualization to explore trends and insights 
- Google Drive Integration for syncing datasets and results
- Multipage Navigation with session tracking and upload management


## What is Streamlit?

[Streamlit](https://streamlit.io/) is an open-source Python framework for building data apps quickly using only Python. It handles all the UI and backend logic automatically, making it ideal for small web tools like this labeling app.


## Repository Structure

```
├── app.py                       # Main entry point for the Streamlit app  
├── drive_utils.py               # Google Drive API integration  
├── requirements.txt             # Python dependencies  
├── .streamlit/                  # Secrets (e.g., GDRIVE_KEY, API_KEYS) for local use only
│   └── secrets.toml             
├── AI_Model_Files/              # AI model-related logic
│   ├── config.py
│   └── label_Machine_test.py    
├── uploaded_data/               # User-specific uploaded files and output
│   └── <user_name>/
│       ├── listings_to_evaluate.csv  
│       ├── images.zip
│       ├── extracted_images/
│       │   └── <image files>
│       └── listings_model_results_<timestamp>.csv
├── pages/                       # Streamlit multipage layout
│   ├── ai_evaluation_upload.py
│   ├── data_visualization.py
│   ├── database_label.py
│   ├── labeling_page.py
│   ├── login.py       
│   └── welcome.py       
└── Data/                        # Example datasets
    └── YYYY_MM_DD/              # Folder by date (e.g., 2025_02_20)
```

## Running the App Locally

We recommend running this app locally using a **graphical interface** such as:

- **Anaconda Navigator**
- **Visual Studio Code**

For complete instructions, follow the official Streamlit guide:  
📘 [Running Streamlit with Anaconda](https://docs.streamlit.io/get-started/installation/anaconda-distribution)

Once your environment is set up, run the app with:

```bash
streamlit run app.py
```

### 🔐 Required: API Keys Setup
Before running the app, you must create a hidden .streamlit folder in the root directory of the project. Inside this folder, add a file named secrets.toml containing your API keys:

```bash
# .streamlit/secrets.toml

# Example secrets.toml structure
API_KEYS = ["your-api-keys", ...]
GDRIVE_KEY = """{
  "type": ...
  }

```

⚠️ Make sure this file is not committed to your repository. Add .streamlit/secrets.toml to your .gitignore file to keep your credentials safe.

## Cloud Deployment

You can also deploy this app to the cloud using **Streamlit Cloud**:

- By connecting your GitHub repository  
- Or using Streamlit’s paid option via **Snowflake**

📘 [Streamlit Cloud Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)


## Google Drive API Setup

This app uses a **Google Service Account** to read and write CSV and image metadata from your Drive.

To enable that, follow this step-by-step guide:  
📘 [Google Drive Setup Guide](./GDRIVE_SETUP.md)

## Adding New Data

To label your own data:

1. Create a new folder in `Data/` (e.g., `Data/2025_08_01/`)
2. Include:
   - A CSV with item metadata
   - Corresponding image files
   - Ensure the CSV includes a column with file names or paths that match the image files inside the subfolder
3. Push the folder to your GitHub repo (if deploying),  
   or place it in your local file system if running locally.

📌 Important:
The only supported way to add data is by pushing it to the GitHub repository using Git.
Do not upload files using GitHub’s web interface, as it cannot handle:
- Large image file sizes
- A high number of files
- Folder structures properly

Also, storing images on Google Drive is not recommended due to API rate limits and delayed file access.

If you’re running the app locally, place the folder directly in your local Data/ directory. The app will automatically detect and display datasets that follow this structure.

## Streamlit Pages

Every `.py` file inside the `/pages` folder becomes a new page in the sidebar:

- `login.py`: Auth system  
- `welcome.py`: Instructions  
- `labeling_page.py`: Labeling interface  

📘 Learn more: [Streamlit Multipage Docs](https://docs.streamlit.io/library/get-started/multipage-apps)
