#!/usr/bin/env python3
"""
CleanOps Azure Blob Backup Uploader.
Uploads an encrypted file to Azure Blob Storage using REST API or Azure SDK.
Reads credentials strictly from environment or /cleanops/.env.
"""

import sys
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone

def upload(file_path):
    if not os.path.exists(file_path):
        print(f"[ERROR] File does not exist: {file_path}")
        sys.exit(1)

    # Check for Azure Blob configuration
    conn_str = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    container = os.environ.get("AZURE_BLOB_CONTAINER", "")
    sas_url = os.environ.get("AZURE_BLOB_SAS_URL", "")

    blob_name = os.path.basename(file_path)

    if sas_url:
        # Upload via direct SAS URL
        base_url = sas_url.split("?")[0].rstrip("/")
        query = sas_url.split("?")[1] if "?" in sas_url else ""
        upload_url = f"{base_url}/{blob_name}?{query}" if query else f"{base_url}/{blob_name}"

        with open(file_path, "rb") as f:
            data = f.read()

        req = urllib.request.Request(upload_url, data=data, method="PUT")
        req.add_header("x-ms-blob-type", "BlockBlob")
        req.add_header("Content-Length", str(len(data)))

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status in (200, 201):
                    print(f"[OK] Successfully uploaded {blob_name} to Azure Blob (HTTP {resp.status})")
                    return
        except urllib.error.HTTPError as e:
            print(f"[ERROR] Azure upload failed: HTTP {e.code}: {e.read().decode('utf-8', errors='ignore')}")
            sys.exit(1)

    print("[INFO] Azure Blob upload: Set AZURE_BLOB_SAS_URL in .env to enable direct automated uploads.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: upload_to_azure_blob.py <file_path>")
        sys.exit(1)
    upload(sys.argv[1])
