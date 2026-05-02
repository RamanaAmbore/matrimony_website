#!/usr/bin/env bash
#
# sync-hook.sh — merge our hook entry into /opt/webhook/hooks.json.
#
# /opt/webhook/hooks.json is a shared JSON array used by the system-wide
# webhook.service (port 9000). We don't want to clobber other apps'
# entries, so this script:
#   1. Reads our entry from /opt/marathakalyanam/deploy/webhook/hooks.snippet.json
#      (the rendered version, with the real secret substituted)
#   2. Replaces (or appends) the entry with id "marathakalyanam-deploy"
#   3. Restarts webhook.service if anything changed
#
# Must run as root (writes /opt/webhook and restarts a service).

set -euo pipefail

SNIPPET="/opt/marathakalyanam/deploy/webhook/hooks.snippet.json"
HOOKS_FILE="/opt/webhook/hooks.json"
TMP_FILE="$(mktemp)"
HOOK_ID="marathakalyanam-deploy"

if [[ ! -f "$SNIPPET" ]]; then
    echo "Snippet not found at $SNIPPET — run install.sh first." >&2
    exit 1
fi

if [[ ! -f "$HOOKS_FILE" ]]; then
    echo "[" > "$HOOKS_FILE"
    echo "]" >> "$HOOKS_FILE"
fi

# Replace existing entry by id, or append if not present.
jq --slurpfile new "$SNIPPET" \
   --arg id "$HOOK_ID" \
   '[.[] | select(.id != $id)] + [$new[0]]' \
   "$HOOKS_FILE" > "$TMP_FILE"

# Validate the result is still valid JSON before swapping.
jq empty < "$TMP_FILE"

if ! diff -q "$TMP_FILE" "$HOOKS_FILE" >/dev/null 2>&1; then
    cp "$TMP_FILE" "$HOOKS_FILE"
    chown www-data:www-data "$HOOKS_FILE"
    chmod 644 "$HOOKS_FILE"
    /bin/systemctl restart webhook.service
    echo "hooks.json updated and webhook.service restarted"
else
    echo "hooks.json already current — no change"
fi

rm -f "$TMP_FILE"
