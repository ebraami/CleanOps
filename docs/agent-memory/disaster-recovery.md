# CleanOps Disaster Recovery Runbook

> Step-by-step restoration runbook if the Azure VM is lost or migrated.

## Prerequisites
- Clean Ubuntu 22.04 or 24.04 VM (or local Linux machine).
- SSH access with sudo privileges.
- GitHub access to `https://github.com/ebraami/CleanOps.git`.
- `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_URL` from secure password vault.

## Step-by-Step Restoration Procedure
1. **Clone Repository**:
   ```bash
   sudo git clone https://github.com/ebraami/CleanOps.git /cleanops
   sudo chown -R $USER:$USER /cleanops
   cd /cleanops
   ```

2. **Restore Secrets**:
   ```bash
   cp /cleanops/.env.example /cleanops/.env
   chmod 600 /cleanops/.env
   # Edit /cleanops/.env and insert the real SUPABASE_SERVICE_ROLE_KEY
   ```

3. **Install Antigravity CLI**:
   ```bash
   curl -fsSL https://antigravity.google/install.sh | bash
   agy  # Authenticate with Google account
   ```

4. **Deploy Systemd Services & MCP Config**:
   ```bash
   mkdir -p ~/.config/systemd/user ~/.gemini/config
   cp /cleanops/deploy/systemd/* ~/.config/systemd/user/
   cp /cleanops/deploy/mcp/mcp_config.json.template ~/.gemini/config/mcp_config.json
   systemctl --user daemon-reload
   systemctl --user enable --now cleanops-gateway.service antigravity-cli-daemon.service
   ```

5. **(Optional) Restore Conversation History Snapshot**:
   If an offsite encrypted snapshot is available:
   ```bash
   /cleanops/scripts/restore_session_state.sh /path/to/cleanops_session_backup.tar.gz.enc
   ```

6. **Verify Recovery**:
   ```bash
   curl -s http://127.0.0.1:8080/health
   python3 /cleanops/scripts/sync_project_memory.py
   agy -p "Verify system status and active phase"
   ```
