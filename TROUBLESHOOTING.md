
# 🛠️ Troubleshooting Guide – Data Labeling App

This document provides solutions to common issues encountered while using the Data Labeling App.

---

## ❌ Error When Starting to Label a New Dataset

### Symptom:
You try to start labeling a new dataset, but encounter an error like this:

> `googleapiclient.errors.HttpError: This app has encountered an error...`

### Cause:
This typically happens when the CSV file **does not contain the required columns** that the app expects to read and update.

---

### ✅ How to Fix It:

1. Go to your connected **Google Drive folder**
2. Locate the **folder corresponding to the dataset date** (e.g., `2025_02_20`)
3. Manually upload or replace the CSV file with one that includes the **missing required columns**

These columns are:

- `user_name`  
- `binary_flag`  
- `timestamp`  
- `image_exist`  

Make sure these are added **in the correct dataset folder**.

---

### ✅ Full List of Required Columns (in order):

```
listing_url
photo_url
price
title
location
origin_city_list
user_name
binary_flag
timestamp
image_exist
```

Make sure the column names match exactly and are placed in the correct order for compatibility with the app.

---

More common troubleshooting scenarios will be added here as needed.
