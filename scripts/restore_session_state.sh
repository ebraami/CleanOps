#!/usr/bin/env bash
# ==============================================================================
# CleanOps Antigravity Session Restore Script
# Decrypts and unpacks an encrypted session archive into ~/.gemini/antigravity-cli/
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PASSPHRASE_FILE="$PROJECT_ROOT/.backup_passphrase"
AGY_HOME="$HOME/.gemini/antigravity-cli"

if [[ $# -lt 1 ]]; then
    DEFAULT_BACKUP="$PROJECT_ROOT/backups/cleanops_session_latest.tar.gz.enc"
    if [[ -f "$DEFAULT_BACKUP" ]]; then
        BACKUP_FILE="$DEFAULT_BACKUP"
    else
        echo "Usage: $0 <path_to_encrypted_backup_file.tar.gz.enc>"
        exit 1
    fi
else
    BACKUP_FILE="$1"
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "[ERROR] Backup file not found: $BACKUP_FILE"
    exit 1
fi

if [[ ! -f "$PASSPHRASE_FILE" ]]; then
    echo -n "Enter encryption passphrase: "
    read -rs PASSPHRASE
    echo
else
    PASSPHRASE="$(cat "$PASSPHRASE_FILE")"
fi

echo "[1/3] Decrypting archive with OpenSSL AES-256..."
TMP_TAR="/tmp/cleanops_restore_$$.tar.gz"

echo -n "$PASSPHRASE" | openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 \
    -in "$BACKUP_FILE" \
    -out "$TMP_TAR" \
    -pass stdin

echo "[2/3] Unpacking session state into $AGY_HOME..."
mkdir -p "$AGY_HOME/conversations" "$AGY_HOME/brain"
tar -xzf "$TMP_TAR" -C "$AGY_HOME"
rm -f "$TMP_TAR"

echo "[3/3] Session restore complete."
echo "Restored conversations:"
ls -lh "$AGY_HOME/conversations" | head -n 10
echo "Antigravity CLI is ready to resume previous conversations."
