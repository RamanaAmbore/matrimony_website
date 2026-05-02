#!/usr/bin/env bash
#
# webhook-deploy.sh — pull latest, install deps, migrate, rebuild frontend, restart services.
#
# Triggered by the adnanh/webhook listener (hook id "marathakalyanam-deploy")
# on every GitHub push to master. Lives in the repo so changes ship via git.
#
# The webhook listener calls this with command-working-directory set to
# /opt/marathakalyanam, so we always start from the repo root.

set -euo pipefail

REPO_DIR="/opt/marathakalyanam"
BACKEND_DIR="$REPO_DIR/backend"
FRONTEND_DIR="$REPO_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"
BRANCH="master"

API_SERVICE="marathakalyanam_api.service"
WEB_SERVICE="marathakalyanam_web.service"
WEBHOOK_SERVICE="webhook.service"

log() { echo "[$(date -u +%FT%TZ)] $*"; }

cd "$REPO_DIR"

log "Fetching $BRANCH"
git fetch --quiet origin "$BRANCH"
git reset --hard "origin/$BRANCH"
HEAD_SHA="$(git rev-parse --short HEAD)"
log "Now at $HEAD_SHA"

# --- backend ---
if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating backend virtualenv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi
log "Installing backend dependencies"
"$VENV_DIR/bin/pip" install --quiet --no-cache-dir --upgrade pip
"$VENV_DIR/bin/pip" install --quiet --no-cache-dir -e "$BACKEND_DIR"

log "Running Alembic migrations"
( cd "$BACKEND_DIR" && "$VENV_DIR/bin/alembic" upgrade head )

# --- frontend ---
log "Installing frontend dependencies (npm ci)"
( cd "$FRONTEND_DIR" && npm ci --no-audit --no-fund --silent )

log "Building frontend"
( cd "$FRONTEND_DIR" && npm run build --silent )

# --- restart services ---
log "Restarting $API_SERVICE"
sudo /bin/systemctl restart "$API_SERVICE"

log "Restarting $WEB_SERVICE"
sudo /bin/systemctl restart "$WEB_SERVICE"

# --- sync hook definitions if changed ---
HOOKS_SRC="$REPO_DIR/deploy/webhook/hooks.snippet.json"
HOOKS_DST="/opt/webhook/hooks.json"
SYNC_SCRIPT="$REPO_DIR/deploy/webhook/sync-hook.sh"
if [[ -f "$SYNC_SCRIPT" && -f "$HOOKS_SRC" ]]; then
    log "Syncing webhook hook definition"
    sudo "$SYNC_SCRIPT" || log "hook sync failed (non-fatal)"
fi

log "Deploy complete: $HEAD_SHA"
