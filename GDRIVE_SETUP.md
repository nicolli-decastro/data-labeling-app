
# Google Drive API Setup (via Service Account)

This guide walks you through setting up a **Google Service Account** to allow your Streamlit app to securely read and write files to your **Google Drive**.


## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click the project dropdown and select **"New Project"**
3. Name the project (e.g., `streamlit-labeling`) and click **Create**


## Step 2: Enable the Google Drive API

1. With your project selected, go to: [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)
2. Click **Enable**


## Step 3: Create a Service Account

1. Visit the [Service Accounts page](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click **Create Service Account**
3. Enter a name (e.g., `streamlit-service-account`) and click **Create and Continue**
4. Assign the following roles:
   - **Basic > Viewer**
   - **Editor**
5. Click **Done**


## Step 4: Create a JSON Key

1. Click on your newly created service account
2. Go to the **Keys** tab
3. Click **Add Key > Create new key**
4. Select **JSON**, then click **Create**
5. A `.json` file will be downloaded — keep it secure


## Step 5: Share Your Google Drive Folder

1. Open [Google Drive](https://drive.google.com/)
2. Create or select your app folder (e.g., `LabelingAppData`)
3. Right-click the folder → **Share**
4. Copy the **service account email** from your JSON file
5. Paste it into the sharing field and give **Editor** access

✅ The service account can now access this folder.


## Step 6: Add the Key to Streamlit

### If Running Locally

1. Create a `.streamlit/` directory in the root of your project (if it doesn’t exist)
2. Add a file named `secrets.toml`:

```toml
GDRIVE_KEY = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nABC...\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  ...
}
"""
```

> Escape all newline characters in the private key with `\n`.

### If Using Streamlit Cloud

1. Go to your deployed app’s **Settings > Secrets**
2. Add a new secret called `GDRIVE_KEY` and paste the full JSON content

---

## ✅ You're Done!

Your app is now connected to your Drive and can read from and write to the shared folder.

---

## References

- [Google IAM – Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [Google Drive API Documentation](https://developers.google.com/drive/api/guides/about-sdk)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
