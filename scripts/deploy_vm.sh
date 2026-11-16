#!/usr/bin/env bash
set -Eeuo pipefail
cd /opt/agroconecta
# Arguments are validated by render_deploy.py before this script is sent to Azure.
IMAGE="$1"
DOMAIN="$2"
cloud-init status --wait
if [ ! -f .grafana-password ]; then
  umask 077
  openssl rand -hex 24 > .grafana-password
fi
PASSWORD=$(cat .grafana-password)
umask 077
cp .env .env.previous 2>/dev/null || true
printf 'APP_IMAGE=%s
SITE_DOMAIN=%s
GRAFANA_ADMIN_PASSWORD=%s
' "$IMAGE" "$DOMAIN" "$PASSWORD" > .env
chmod 600 .env .grafana-password
# Public registry image: VM needs no Docker Hub credential.
docker compose pull
# Start the candidate before exposing it through Caddy.
docker compose up -d --wait --wait-timeout 240 app
# /ready verifies that the trained model loaded, not just that Python started.
docker compose exec -T app python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=5)"
docker compose up -d caddy prometheus grafana
for i in $(seq 1 40); do
  if curl --fail --silent --max-time 10 "https://$DOMAIN/ready" >/dev/null; then
    echo "AGROCONECTA_DEPLOY_OK"
    exit 0
  fi
  sleep 5
done
echo 'HTTPS/readiness failed. Inspect Caddy, DNS, certificate issuance and app logs.' >&2
exit 1
