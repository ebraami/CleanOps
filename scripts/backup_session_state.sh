#!/usr/bin/env bash
# ==============================================================================
# CleanOps Antigravity Session Encrypted Backup Script
# Archives conversation databases, transcripts, and settings with AES-256.
# Prunes local archives older than 7 days and dispatches to OFFSITE destination.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
PASSPHRASE_FILE="$PROJECT_ROOT/.backup_passphrase"
BACKUP_DIR="$PROJECT_ROOT/backups"
AGY_HOME="$HOME/.gemini/antigravity-cli"

TIMESTAMP="$(date -u +"%Y%m%d_%H%M%S")"
ARCHIVE_NAME="cleanops_session_${TIMESTAMP}"
STAGING_DIR="/tmp/cleanops_backup_${TIMESTAMP}"
ENCRYPTED_FILE="$BACKUP_DIR/${ARCHIVE_NAME}.tar.gz.enc"
LATEST_LINK="$BACKUP_DIR/cleanops_session_latest.tar.gz.enc"

# Ensure passphrase file exists
if [[ ! -f "$PASSPHRASE_FILE" ]]; then
    echo "[ERROR] Passphrase file not found: $PASSPHRASE_FILE"
    exit 1
fi

# Load environment configuration if present
if [[ -f "$ENV_FILE" ]]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

mkdir -p "$BACKUP_DIR" "$STAGING_DIR"

echo "[1/5] Staging Antigravity session data (using SQLite safe online backup)..."

# Use python to perform safe online backups of active SQLite databases
python3 - <<EOF
import os
import sqlite3
import shutil

agy_home = "$AGY_HOME"
staging = "$STAGING_DIR"

# 1. Backup master conversation_summaries.db safely
src_sum = os.path.join(agy_home, "conversation_summaries.db")
if os.path.exists(src_sum):
    dst_sum = os.path.join(staging, "conversation_summaries.db")
    try:
        s_con = sqlite3.connect(src_sum)
        d_con = sqlite3.connect(dst_sum)
        s_con.backup(d_con)
        s_con.close()
        d_con.close()
    except Exception as e:
        print(f"Warning on conversation_summaries: {e}")

# 2. Backup conversation databases
conv_src = os.path.join(agy_home, "conversations")
conv_dst = os.path.join(staging, "conversations")
os.makedirs(conv_dst, exist_ok=True)

if os.path.exists(conv_src):
    for f in os.listdir(conv_src):
        if f.endswith(".db"):
            sp = os.path.join(conv_src, f)
            dp = os.path.join(conv_dst, f)
            try:
                s_con = sqlite3.connect(sp)
                d_con = sqlite3.connect(dp)
                s_con.backup(d_con)
                s_con.close()
                d_con.close()
            except Exception as e:
                # If hot lock, fallback to standard copy
                shutil.copy2(sp, dp)

# 3. Copy brain directory (transcripts and artifacts)
brain_src = os.path.join(agy_home, "brain")
brain_dst = os.path.join(staging, "brain")
if os.path.exists(brain_src):
    shutil.copytree(brain_src, brain_dst, ignore=shutil.ignore_patterns("*.tmp", "chunks"))

# 4. Copy settings and state
for fname in ["settings.json", "antigravity_state.pbtxt", "jetski_state.pbtxt"]:
    fp = os.path.join(agy_home, fname)
    if os.path.exists(fp):
        shutil.copy2(fp, os.path.join(staging, fname))
EOF

echo "[2/5] Creating compressed tar archive..."
TAR_TMP="/tmp/${ARCHIVE_NAME}.tar.gz"
tar -czf "$TAR_TMP" -C "$STAGING_DIR" .
rm -rf "$STAGING_DIR"

echo "[3/5] Encrypting archive with OpenSSL AES-256 (PBKDF2)..."
openssl enc -aes-256-cbc -pbkdf2 -iter 100000 \
    -in "$TAR_TMP" \
    -out "$ENCRYPTED_FILE" \
    -pass "file:$PASSPHRASE_FILE"

rm -f "$TAR_TMP"
chmod 600 "$ENCRYPTED_FILE"

# Update 'latest' pointer
ln -sf "$ENCRYPTED_FILE" "$LATEST_LINK"
echo "  -> Encrypted backup created: $ENCRYPTED_FILE ($(du -h "$ENCRYPTED_FILE" | cut -f1))"

echo "[4/5] Enforcing local retention policy (pruning backups older than 7 days)..."
find "$BACKUP_DIR" -name "cleanops_session_*.tar.gz.enc" -type f -mtime +7 -exec rm -f {} +

echo "[5/5] Dispathing to OFFSITE destination..."
DEST_TYPE="${OFFSITE_DESTINATION_TYPE:-manual_export}"

case "$DEST_TYPE" in
    "sftp_scp")
        if [[ -n "${OFFSITE_SCP_TARGET:-}" ]]; then
            echo "  -> SCP transfer to $OFFSITE_SCP_TARGET..."
            scp -B -q "$ENCRYPTED_FILE" "$OFFSITE_SCP_TARGET"
            echo "  -> Offsite transfer complete."
        else
            echo "  [WARN] OFFSITE_SCP_TARGET not specified. Skipping SCP transfer."
        fi
        ;;
    "azure_blob")
        if [[ -n "${AZURE_STORAGE_CONNECTION_STRING:-}" && -n "${AZURE_BLOB_CONTAINER:-}" ]]; then
            echo "  -> Uploading to Azure Blob Storage container: $AZURE_BLOB_CONTAINER..."
            python3 "$SCRIPT_DIR/upload_to_azure_blob.py" "$ENCRYPTED_FILE"
            echo "  -> Azure Blob upload complete."
        else
            echo "  [WARN] Azure Blob credentials not fully configured in .env."
        fi
        ;;
    "manual_export"|*)
        echo "  -> Mode: manual_export"
        echo "  -> Offsite ready: You can securely pull this encrypted backup to your local machine via:"
        echo "     scp $USER@$(hostname -I | awk '{print $1}'):$ENCRYPTED_FILE ./"
        ;;
esac

echo "Backup workflow finished successfully at $(date -u +"%Y-%m-%d %H:%M:%S UTC")."
