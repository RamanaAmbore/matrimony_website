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
# Fix ownership of any root-created files so git reset and the build can overwrite them.
# Don't suppress errors — if chown fails the rest will fail anyway, fail loud.
sudo /usr/local/sbin/mk-chown-repo
git reset --hard "origin/$BRANCH"
HEAD_SHA="$(git rev-parse --short HEAD)"
log "Now at $HEAD_SHA"

# Drop stale build caches that may have been created with wrong owner during a
# prior root-as-user run. These are all rebuildable by `npm ci` + `npm run build`.
log "Clearing stale frontend build caches"
rm -rf \
    "$FRONTEND_DIR/node_modules/.vite" \
    "$FRONTEND_DIR/node_modules/.vite-temp" \
    "$FRONTEND_DIR/.svelte-kit" \
    "$FRONTEND_DIR/build" 2>/dev/null || true
# Run chown again post-cleanup so any newly-created parent dirs are www-data-owned
sudo /usr/local/sbin/mk-chown-repo

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
sudo /usr/bin/systemctl restart "$API_SERVICE"

log "Restarting $WEB_SERVICE"
sudo /usr/bin/systemctl restart "$WEB_SERVICE"

# --- sync hook definitions if changed ---
HOOKS_SRC="$REPO_DIR/deploy/webhook/hooks.snippet.json"
HOOKS_DST="/opt/webhook/hooks.json"
SYNC_SCRIPT="$REPO_DIR/deploy/webhook/sync-hook.sh"
if [[ -f "$SYNC_SCRIPT" && -f "$HOOKS_SRC" ]]; then
    log "Syncing webhook hook definition"
    sudo "$SYNC_SCRIPT" || log "hook sync failed (non-fatal)"
fi

log "Deploy complete: $HEAD_SHA"

# --- Telegram notification ---
# Credentials stored in .env (never in git)
DOTENV="$REPO_DIR/.env"
if [[ -f "$DOTENV" ]]; then
    TG_TOKEN="$(grep -E '^TELEGRAM_BOT_TOKEN=' "$DOTENV" | cut -d= -f2- | tr -d '[:space:]')"
    TG_CHAT="$(grep -E '^TELEGRAM_CHAT_ID=' "$DOTENV" | cut -d= -f2- | tr -d '[:space:]')"
    if [[ -n "$TG_TOKEN" && -n "$TG_CHAT" ]]; then
        IST="$(TZ='Asia/Kolkata' date '+%a, %d %b %Y %I:%M %p IST')"
        EDT="$(TZ='America/New_York' date '+%I:%M %p EDT')"
        MSG="<b>Maratha Kalyanam - Deploy OK</b>
${IST} · ${EDT}
<code>SHA: ${HEAD_SHA}</code>"
        curl -s -o /dev/null \
            -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
            -d "chat_id=${TG_CHAT}" \
            -d "parse_mode=HTML" \
            --data-urlencode "text=${MSG}" \
            && log "Telegram notification sent" \
            || log "Telegram notification failed (non-fatal)"
    fi
fi
