# Deploy — marathakalyanam

Production target: **ramboq server** (`ssh ramboq` as root, IP `69.62.78.136`),
folder `/opt/marathakalyanam/`, domain `marathakalyanam.com`
(behind Cloudflare proxy, Full-strict SSL).

## Files in this directory

| File | Purpose |
|---|---|
| `install.sh` | First-time installer. Idempotent. Run **once** on the server as root. |
| `webhook-deploy.sh` | Deploy script invoked by the webhook on every push to `master`. |
| `nginx/marathakalyanam.com.conf` | nginx vhost (HTTPS, proxies to backend :8003 / frontend :3003). |
| `systemd/marathakalyanam_api.service` | Backend uvicorn unit. |
| `systemd/marathakalyanam_web.service` | Frontend SvelteKit (adapter-node) unit. |
| `webhook/hooks.snippet.json.tmpl` | Hook entry template (secret substituted at install). |
| `webhook/sync-hook.sh` | Merges our hook entry into `/opt/webhook/hooks.json`. |

## How services map

```
internet (Cloudflare proxy) ──► nginx :443 (marathakalyanam.com)
                                  ├── /api/*    → 127.0.0.1:8003 (marathakalyanam_api.service, uvicorn)
                                  ├── /media/*  → 127.0.0.1:8003 (passport-private auth in app)
                                  ├── /hooks/deploy → 127.0.0.1:9000/hooks/marathakalyanam-deploy (webhook.service)
                                  └── /         → 127.0.0.1:3003 (marathakalyanam_web.service, node build)
```

Systemd units installed on the server:

- `marathakalyanam_api.service` (port 8003)
- `marathakalyanam_web.service` (port 3003)
- `webhook.service` (port 9000) — already present; we just register a new hook id

## First-time install

```bash
ssh ramboq
sudo /opt/marathakalyanam/deploy/install.sh   # if repo is already cloned
# OR, if /opt/marathakalyanam doesn't exist yet:
sudo bash -c 'mkdir -p /opt/marathakalyanam && cd /opt/marathakalyanam && git clone https://github.com/RamanaAmbore/matrimony_website.git . && bash deploy/install.sh'
```

The script prints the **webhook URL + secret** at the end. Paste them into:

GitHub → `RamanaAmbore/matrimony_website` → Settings → Webhooks → Add webhook
- Payload URL: `https://marathakalyanam.com/hooks/deploy`
- Content type: `application/json`
- Secret: (printed by install.sh)
- Events: `Just the push event`
- Active: ✅

## Subsequent deploys

`git push origin master` — that's it. GitHub fires the webhook → `webhook.service`
verifies the HMAC signature and matches `refs/heads/master` → runs
`/opt/marathakalyanam/deploy/webhook-deploy.sh`, which pulls, installs, migrates,
rebuilds the frontend, and restarts both systemd units.

## Operational

```bash
# Logs
sudo journalctl -u marathakalyanam_api.service -f
sudo journalctl -u marathakalyanam_web.service -f
tail -f /opt/marathakalyanam/.log/api.log
tail -f /opt/marathakalyanam/.log/web.log

# Restart manually
sudo systemctl restart marathakalyanam_api.service marathakalyanam_web.service

# Trigger a deploy by hand (skip the webhook)
sudo -u www-data /opt/marathakalyanam/deploy/webhook-deploy.sh

# Edit env (DB URL is the only thing here you should never touch by hand;
# everything else lives in admin Settings UI)
sudo -u www-data nano /opt/marathakalyanam/.env
```

## Cert renewal

certbot's systemd timer renews automatically. To force-renew:

```bash
sudo certbot renew --force-renewal -d marathakalyanam.com -d www.marathakalyanam.com
sudo systemctl reload nginx
```

## Rolling back

```bash
ssh ramboq
cd /opt/marathakalyanam
sudo -u www-data git log --oneline -10            # find the SHA
sudo -u www-data git reset --hard <sha>
sudo -u www-data /opt/marathakalyanam/deploy/webhook-deploy.sh
```
