# drive_utils.py

import io
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import streamlit as st
import json

# --- Setup credentials from Streamlit secrets ---
creds_dict = json.loads(st.secrets["GDRIVE_KEY"])
SCOPES = ['https://www.googleapis.com/auth/drive']
credentials = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# --- Helper Functions ---
def get_folder_id_by_name(name, parent_id=None):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{name}'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = drive_service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    folders = results.get('files', [])
    return folders[0]['id'] if folders else None


def list_date_folders():
    root_id = get_folder_id_by_name("LabelingAppData")
    results = drive_service.files().list(
        q=f"'{root_id}' in parents and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)",
    ).execute()
    return sorted(results.get('files', []), key=lambda x: x['name'], reverse=True)


def list_csvs_in_folder(folder_id):
    query = f"'{folder_id}' in parents and name contains '.csv'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    return results.get('files', [])


def get_file_id_by_name(name, folder_id):
    query = f"name='{name}' and '{folder_id}' in parents"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None


def download_csv(file_name, folder_id):
    file_id = get_file_id_by_name(file_name, folder_id)
    if file_id is None:
        return pd.DataFrame()
    request = drive_service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    try:
        return pd.read_csv(fh)
    except Exception:
        return pd.DataFrame()


def upload_csv(df, file_name, folder_id):
    # Check if file exists
    file_id = get_file_id_by_name(file_name, folder_id)
    df.to_csv(file_name, index=False)
    media = MediaFileUpload(file_name, mimetype='text/csv')

    if file_id:
        drive_service.files().update(fileId=file_id, media_body=media).execute()
    else:
        drive_service.files().create(
            body={'name': file_name, 'parents': [folder_id]},
            media_body=media
        ).execute()


def get_image_file_id(image_name, image_folder_id):
    if pd.isna(image_name):
        return None
    image_name = str(image_name).strip()
    query = f"name='{image_name}' and '{image_folder_id}' in parents"
    result = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = result.get('files', [])
    return items[0]['id'] if items else None
