#!/usr/bin/env bash
#
# install.sh — first-time install on the ramboq server.
#
# Idempotent: safe to re-run.
#
# What it does:
#   - Creates /opt/marathakalyanam/{var/media,.log} owned by www-data
#   - Clones the GitHub repo (or pulls if already cloned)
#   - Creates Postgres role + DB if missing
#   - Generates .env on the server (DB password, session secret) — never logged
#   - Creates Python venv, installs backend, runs Alembic migrations
#   - Installs Node deps and builds the frontend
#   - Installs systemd units, enables + starts services
#   - Renders the webhook hook snippet with a fresh secret and registers it
#   - Installs the nginx vhost (HTTP only initially) and reloads nginx
#   - Optionally requests a Let's Encrypt cert via certbot
#
# After the script runs, it prints the values you must paste into:
#   - GitHub → repo Settings → Webhooks (URL + secret)
#   - admin Settings UI later (SMTP creds, etc.)

set -euo pipefail

APP_DIR="/opt/marathakalyanam"
REPO_URL="https://github.com/RamanaAmbore/matrimony_website.git"
BRANCH="master"
APP_USER="www-data"
APP_GROUP="www-data"
DOMAIN="marathakalyanam.com"
DOMAIN_WWW="www.marathakalyanam.com"
DB_NAME="marathakalyanam"
DB_USER="marathakalyanam"

ENV_FILE="$APP_DIR/.env"
NGINX_SITE="/etc/nginx/sites-available/${DOMAIN}.conf"
NGINX_LINK="/etc/nginx/sites-enabled/${DOMAIN}.conf"

log()  { echo -e "\033[1;34m[install]\033[0m $*"; }
warn() { echo -e "\033[1;33m[install]\033[0m $*" >&2; }
fail() { echo -e "\033[1;31m[install]\033[0m $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || fail "run as root"

# --- 1. Directories ---
log "Creating $APP_DIR"
mkdir -p "$APP_DIR/var/media" "$APP_DIR/.log"

# --- 2. Clone or pull repo ---
if [[ -d "$APP_DIR/.git" ]]; then
    log "Repo present — pulling $BRANCH"
    git -C "$APP_DIR" fetch --quiet origin "$BRANCH"
    git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
    log "Cloning $REPO_URL into $APP_DIR"
    # Clone into a temp dir then move so we don't fight with the empty $APP_DIR
    tmpclone="$(mktemp -d)"
    git clone --quiet --branch "$BRANCH" "$REPO_URL" "$tmpclone"
    shopt -s dotglob
    mv "$tmpclone"/* "$APP_DIR/"
    rmdir "$tmpclone"
fi

# --- 3. Postgres ---
log "Ensuring Postgres role + database '$DB_NAME'"
DB_EXISTS="$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'")"
if [[ "$DB_EXISTS" != "1" ]]; then
    DB_PASSWORD="$(openssl rand -hex 24)"
    sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}';
CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
SQL
    DB_NEW=1
else
    log "DB exists — leaving role password untouched"
    DB_NEW=0
fi

# --- 4. .env ---
if [[ ! -f "$ENV_FILE" ]]; then
    [[ "${DB_NEW:-0}" == "1" ]] || fail ".env missing but DB role unchanged — set DATABASE_URL by hand"
    SESSION_SECRET="$(openssl rand -hex 16)"   # 16 bytes -> Litestar AES-128 key
    cat > "$ENV_FILE" <<EOF
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5432/${DB_NAME}
SESSION_SECRET=${SESSION_SECRET}
MEDIA_ROOT=${APP_DIR}/var/media
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM=no-reply@${DOMAIN}
OWNER_EMAIL=ramanamborespam@gmail.com
CORS_ORIGINS=https://${DOMAIN},https://${DOMAIN_WWW}
IS_PROD=true
EOF
    chmod 600 "$ENV_FILE"
    chown "$APP_USER:$APP_GROUP" "$ENV_FILE"
    log "Wrote $ENV_FILE (mode 600)"
else
    log "$ENV_FILE already present — leaving in place"
fi

# --- 5a. Ownership ---
log "Chowning $APP_DIR to $APP_USER:$APP_GROUP (excluding .env which stays 600)"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
chmod 600 "$ENV_FILE"

# --- 5. Backend venv + migrate ---
log "Installing backend (venv + Alembic)"
sudo -u "$APP_USER" -H bash -c "
    set -euo pipefail
    cd '$APP_DIR/backend'
    [[ -d .venv ]] || python3 -m venv .venv
    .venv/bin/pip install --quiet --no-cache-dir --upgrade pip
    .venv/bin/pip install --quiet --no-cache-dir -e .
    set -a; source '$ENV_FILE'; set +a
    .venv/bin/alembic upgrade head
"

# --- 6. Frontend build ---
log "Building frontend"
sudo -u "$APP_USER" -H bash -c "
    set -euo pipefail
    cd '$APP_DIR/frontend'
    npm ci --no-audit --no-fund --silent
    npm run build --silent
"

# --- 7. Render webhook snippet with fresh secret ---
SNIPPET_RENDERED="$APP_DIR/deploy/webhook/hooks.snippet.json"
SECRET_FILE="$APP_DIR/deploy/webhook/.secret"
if [[ ! -f "$SECRET_FILE" ]]; then
    WEBHOOK_SECRET="$(openssl rand -hex 32)"
    echo "$WEBHOOK_SECRET" > "$SECRET_FILE"
    chmod 600 "$SECRET_FILE"
    chown "$APP_USER:$APP_GROUP" "$SECRET_FILE"
    log "Generated new webhook secret (saved at $SECRET_FILE, mode 600)"
else
    WEBHOOK_SECRET="$(cat "$SECRET_FILE")"
fi
sed "s/__WEBHOOK_SECRET__/${WEBHOOK_SECRET}/" \
    "$APP_DIR/deploy/webhook/hooks.snippet.json.tmpl" > "$SNIPPET_RENDERED"
chown "$APP_USER:$APP_GROUP" "$SNIPPET_RENDERED"

log "Registering hook in /opt/webhook/hooks.json"
"$APP_DIR/deploy/webhook/sync-hook.sh"

# --- 8. systemd units ---
log "Installing systemd units"
cp "$APP_DIR/deploy/systemd/marathakalyanam_api.service" /etc/systemd/system/
cp "$APP_DIR/deploy/systemd/marathakalyanam_web.service" /etc/systemd/system/

# webhook-deploy.sh is invoked via `sudo systemctl restart` — grant www-data passwordless rights for just our two units.
SUDOERS=/etc/sudoers.d/marathakalyanam
if [[ ! -f "$SUDOERS" ]]; then
    cat > "$SUDOERS" <<EOF
www-data ALL=(root) NOPASSWD: /bin/systemctl restart marathakalyanam_api.service, /bin/systemctl restart marathakalyanam_web.service, /bin/systemctl restart webhook.service, $APP_DIR/deploy/webhook/sync-hook.sh
EOF
    chmod 440 "$SUDOERS"
    visudo -cf "$SUDOERS" >/dev/null
fi

systemctl daemon-reload
systemctl enable --now marathakalyanam_api.service
systemctl enable --now marathakalyanam_web.service

# --- 9. nginx vhost ---
log "Installing nginx vhost"
cp "$APP_DIR/deploy/nginx/${DOMAIN}.conf" "$NGINX_SITE"
ln -sf "$NGINX_SITE" "$NGINX_LINK"

# Test nginx config — but the cert lines reference paths certbot hasn't created yet.
# Use a minimal HTTP-only vhost first, run certbot, then swap to the full vhost.
HTTP_ONLY="$(mktemp)"
cat > "$HTTP_ONLY" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} ${DOMAIN_WWW};
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 200 'install in progress'; add_header Content-Type text/plain; }
}
EOF
mkdir -p /var/www/certbot
cp "$HTTP_ONLY" "$NGINX_SITE"
nginx -t
systemctl reload nginx
rm -f "$HTTP_ONLY"

if [[ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]]; then
    log "Requesting Let's Encrypt cert for ${DOMAIN}, ${DOMAIN_WWW}"
    certbot certonly --webroot -w /var/www/certbot \
        -d "${DOMAIN}" -d "${DOMAIN_WWW}" \
        --non-interactive --agree-tos -m "ramanamborespam@gmail.com" \
        --no-eff-email
fi

log "Swapping in the full vhost (with SSL)"
cp "$APP_DIR/deploy/nginx/${DOMAIN}.conf" "$NGINX_SITE"
nginx -t
systemctl reload nginx

# --- 10. Permissions sanity ---
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR/var" "$APP_DIR/.log"

log "Done."
echo
echo "================================================================"
echo "WEBHOOK CONFIG — paste these into GitHub"
echo "  URL:          https://${DOMAIN}/hooks/deploy"
echo "  Content type: application/json"
echo "  Secret:       ${WEBHOOK_SECRET}"
echo "  Events:       Just the push event"
echo "================================================================"
echo
echo "Bootstrap admin password for ramanamborespam@gmail.com is in:"
echo "  journalctl -u marathakalyanam_api.service -n 200 --no-pager | grep -i 'admin'"
echo
