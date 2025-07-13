# Data Labeling App – Loss Detection for Retailers

A **Streamlit web application** designed for **retailers and researchers** to label suspicious items from marketplaces (like Facebook Marketplace or Craigslist). The labeled data supports loss detection research by enabling structured annotation of potentially stolen items.

---

## What This App Does

- Login system
- Batch labeling interface for images and listings
- CSV-based tracking for analysis
- Google Drive integration for dataset storage and syncing
- Multipage layout using Streamlit’s native support

---

## What is Streamlit?

[Streamlit](https://streamlit.io/) is an open-source Python framework for building data apps quickly using only Python. It handles all the UI and backend logic automatically, making it ideal for small web tools like this labeling app.

---

## Repository Structure

```bash
├── app.py # Entry point of the app
├── drive_utils.py # Google Drive integration
├── requirements.txt # Dependencies
├── .streamlit/ # Secrets (e.g., GDRIVE_KEY)
├── pages/
│ ├── login.py
│ ├── welcome.py
│ └── labeling_page.py
└── Data/
└── YYYY_MM_DD/ # Example dataset folder
---

## Running the App Locally

We recommend running this app locally using a **graphical interface** such as:

- **Anaconda Navigator**
- **Visual Studio Code**

For complete instructions, follow the official Streamlit guide:  
📘 [Running Streamlit with Anaconda](https://docs.streamlit.io/get-started/installation/anaconda-distribution)

Once your environment is set up, just run:

```bash
streamlit run app.py
---

## Cloud Deployment
You can also deploy this app to the cloud using Streamlit Cloud:

By connecting your GitHub repository

Or using Streamlit’s paid option via Snowflake

For detailed instructions, refer to the official documentation:
📘 [Streamlit Cloud Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app)

# Google Drive API Setup
This app uses a Google Service Account to read and write CSV and image metadata from your Drive.

To enable that, follow this step-by-step guide:
## Google Drive Setup Guide

# Adding New Data
To label your own data:

Create a new folder in Data/ (e.g., Data/2025_08_01/)

Include:

A CSV with item metadata

Corresponding image files

Push the folder to your GitHub repo (if deploying)
or place it in your local file system if running locally.

The app will automatically detect and load available folders.

# Streamlit Pages
Every .py file inside the /pages folder becomes a new page in the sidebar.

login.py: Auth system

welcome.py: Instructions

labeling_page.py: Labeling interface

Learn more: [Streamlit Multipage Docs](https://docs.streamlit.io/library/get-started/multipage-apps)

