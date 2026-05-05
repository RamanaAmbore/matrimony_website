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

# Localhost ports each service listens on (matches systemd unit files).
API_PORT=8003
WEB_PORT=3003

log() { echo "[$(date -u +%FT%TZ)] $*"; }

# ---- Telegram helper (read once, reuse for success + failure notifications) ----
DOTENV="$REPO_DIR/.env"
TG_TOKEN=""
TG_CHAT=""
if [[ -f "$DOTENV" ]]; then
    TG_TOKEN="$(grep -E '^TELEGRAM_BOT_TOKEN=' "$DOTENV" | cut -d= -f2- | tr -d '[:space:]' || true)"
    TG_CHAT="$(grep -E '^TELEGRAM_CHAT_ID=' "$DOTENV" | cut -d= -f2- | tr -d '[:space:]' || true)"
fi

tg_send() {
    # tg_send <html-body>
    local body="$1"
    if [[ -z "$TG_TOKEN" || -z "$TG_CHAT" ]]; then
        return 0
    fi
    curl -s -o /dev/null \
        -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
        -d "chat_id=${TG_CHAT}" \
        -d "parse_mode=HTML" \
        --data-urlencode "text=${body}" || true
}

CURRENT_STAGE="startup"
HEAD_SHA="(unknown)"

on_error() {
    local exit_code=$?
    local line=$1
    log "DEPLOY FAILED at stage '${CURRENT_STAGE}' (line ${line}, exit ${exit_code})"
    local ist edt
    ist="$(TZ='Asia/Kolkata' date '+%a, %d %b %Y %I:%M %p IST')"
    edt="$(TZ='America/New_York' date '+%I:%M %p EDT')"
    tg_send "<b>Maratha Kalyanam - Deploy FAILED</b>
${ist} · ${edt}
<code>SHA: ${HEAD_SHA}</code>
Stage: <b>${CURRENT_STAGE}</b>
Line ${line}, exit ${exit_code}
Tail of journal: <code>journalctl -u ${WEB_SERVICE} -n 50</code>"
    exit "$exit_code"
}
trap 'on_error $LINENO' ERR

cd "$REPO_DIR"

CURRENT_STAGE="git fetch + reset"
log "Fetching $BRANCH"
git fetch --quiet origin "$BRANCH"
# Fix ownership of any root-created files so git reset and the build can overwrite them.
# Don't suppress errors — if chown fails the rest will fail anyway, fail loud.
sudo /usr/local/sbin/mk-chown-repo || log "mk-chown-repo had non-fatal errors (likely vanished files mid-traversal)"
git reset --hard "origin/$BRANCH"
HEAD_SHA="$(git rev-parse --short HEAD)"
log "Now at $HEAD_SHA"

CURRENT_STAGE="clear frontend caches"
# Drop stale build caches that may have been created with wrong owner during a
# prior root-as-user run. These are all rebuildable by `npm ci` + `npm run build`.
log "Clearing stale frontend build caches"
rm -rf \
    "$FRONTEND_DIR/node_modules/.vite" \
    "$FRONTEND_DIR/node_modules/.vite-temp" \
    "$FRONTEND_DIR/.svelte-kit" \
    "$FRONTEND_DIR/build" 2>/dev/null || true
# Run chown again post-cleanup so any newly-created parent dirs are www-data-owned
sudo /usr/local/sbin/mk-chown-repo || log "mk-chown-repo had non-fatal errors (likely vanished files mid-traversal)"

# --- backend ---
CURRENT_STAGE="backend deps"
if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating backend virtualenv at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi
log "Installing backend dependencies"
"$VENV_DIR/bin/pip" install --quiet --no-cache-dir --upgrade pip
"$VENV_DIR/bin/pip" install --quiet --no-cache-dir -e "$BACKEND_DIR"

CURRENT_STAGE="alembic migrate"
log "Running Alembic migrations"
( cd "$BACKEND_DIR" && "$VENV_DIR/bin/alembic" upgrade head )

# --- frontend ---
# `npm ci` is supposed to wipe node_modules and reinstall, but a prior interrupted
# run can leave a corrupted tree where partial files exist (e.g. vite/dist/node/cli.js
# missing). If the post-build sanity check below fails, the trap fires before any
# restart — we want the broken site to stay up rather than swap in a broken build.
CURRENT_STAGE="npm ci"
log "Installing frontend dependencies (npm ci)"
( cd "$FRONTEND_DIR" && npm ci --no-audit --no-fund )

CURRENT_STAGE="vite build"
log "Building frontend"
( cd "$FRONTEND_DIR" && npm run build )

CURRENT_STAGE="verify build output"
# adapter-node writes a CJS entrypoint here; without it the systemd unit
# crash-loops with MODULE_NOT_FOUND.
if [[ ! -f "$FRONTEND_DIR/build/index.js" ]]; then
    log "ABORT: $FRONTEND_DIR/build/index.js is missing — build did not finish cleanly"
    exit 1
fi
log "Build output verified ($(stat -c %s "$FRONTEND_DIR/build/index.js") bytes)"

# --- restart services ---
CURRENT_STAGE="restart $API_SERVICE"
log "Restarting $API_SERVICE"
sudo /usr/bin/systemctl restart "$API_SERVICE"

CURRENT_STAGE="restart $WEB_SERVICE"
log "Restarting $WEB_SERVICE"
sudo /usr/bin/systemctl reset-failed "$WEB_SERVICE" 2>/dev/null || true
sudo /usr/bin/systemctl restart "$WEB_SERVICE"

# --- post-restart health check ---
CURRENT_STAGE="health check"
log "Waiting for services to come up"
sleep 3
api_status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:${API_PORT}/health" || echo "000")
web_status=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://127.0.0.1:${WEB_PORT}/" || echo "000")
api_active=$(systemctl is-active "$API_SERVICE" || echo "inactive")
web_active=$(systemctl is-active "$WEB_SERVICE" || echo "inactive")
log "Post-restart: api=${api_active} (HTTP ${api_status}), web=${web_active} (HTTP ${web_status})"

if [[ "$api_active" != "active" || "$web_active" != "active" ]]; then
    log "ABORT: one or more services failed to start"
    exit 1
fi
# Web should respond 2xx/3xx on root; treat 4xx/5xx as deploy failure.
if [[ "$web_status" != 2* && "$web_status" != 3* ]]; then
    log "ABORT: web service returned HTTP ${web_status} on /"
    exit 1
fi

# --- sync hook definitions if changed ---
CURRENT_STAGE="sync hook definitions"
HOOKS_SRC="$REPO_DIR/deploy/webhook/hooks.snippet.json"
HOOKS_DST="/opt/webhook/hooks.json"
SYNC_SCRIPT="$REPO_DIR/deploy/webhook/sync-hook.sh"
if [[ -f "$SYNC_SCRIPT" && -f "$HOOKS_SRC" ]]; then
    log "Syncing webhook hook definition"
    sudo "$SYNC_SCRIPT" || log "hook sync failed (non-fatal)"
fi

log "Deploy complete: $HEAD_SHA"

# --- Telegram success notification ---
CURRENT_STAGE="telegram success"
if [[ -n "$TG_TOKEN" && -n "$TG_CHAT" ]]; then
    IST="$(TZ='Asia/Kolkata' date '+%a, %d %b %Y %I:%M %p IST')"
    EDT="$(TZ='America/New_York' date '+%I:%M %p EDT')"
    tg_send "<b>Maratha Kalyanam - Deploy OK</b>
${IST} · ${EDT}
<code>SHA: ${HEAD_SHA}</code>
api HTTP ${api_status} · web HTTP ${web_status}" \
        && log "Telegram notification sent" \
        || log "Telegram notification failed (non-fatal)"
fi
