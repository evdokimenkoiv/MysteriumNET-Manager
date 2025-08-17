#!/usr/bin/env bash
set -Eeuo pipefail

# Usage:
#   sudo -E env ADMIN_USER=admin ADMIN_PASSWORD='Strong!' MANAGER_PORT=8080 \
#     bash -c 'bash <(curl -fsSL https://raw.githubusercontent.com/<user>/MysteriumNET-Manager/main/scripts/install_manager_one_command.sh)'

# Allow carriage returns from curl on Windows editors
fix_crlf() { sed -e 's/\r$//'; }

# Defaults
: "${ADMIN_USER:=admin}"
: "${ADMIN_PASSWORD:=password}"
: "${MANAGER_PORT:=8080}"
: "${GITHUB_OWNER:=evdokimenkoiv}"
REPO_URL="https://github.com/${GITHUB_OWNER}/MysteriumNET-Manager.git"
INSTALL_DIR="/opt/mysterium/MysteriumNET-Manager"

echo "[*] Ensuring docker + compose present..."
if ! command -v docker >/dev/null 2>&1; then
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y ca-certificates curl gnupg lsb-release
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker || true
fi

echo "[*] Cloning/updating repository..."
mkdir -p "$(dirname "$INSTALL_DIR")"
if [ ! -d "$INSTALL_DIR/.git" ]; then
  git clone "$REPO_URL" "$INSTALL_DIR"
else
  git -C "$INSTALL_DIR" fetch --all --prune
  git -C "$INSTALL_DIR" reset --hard origin/$(git -C "$INSTALL_DIR" rev-parse --abbrev-ref HEAD || echo main) || git -C "$INSTALL_DIR" reset --hard origin/main
fi

cd "$INSTALL_DIR"

echo "[*] Preparing .env ..."
if [ ! -f .env ]; then
  cp .env.example .env
fi
# Generate a random secret if empty/placeholder
if ! grep -q '^MANAGER_SECRET=' .env || grep -q 'please_change_me' .env; then
  SEC="$(tr -dc 'A-F0-9' </dev/urandom | head -c 32 || true)"
  sed -i "s|^MANAGER_SECRET=.*|MANAGER_SECRET=${SEC}|" .env
fi

sed -i "s|^ADMIN_USER=.*|ADMIN_USER=${ADMIN_USER}|" .env
sed -i "s|^ADMIN_PASSWORD=.*|ADMIN_PASSWORD=${ADMIN_PASSWORD}|" .env
sed -i "s|^MANAGER_PORT=.*|MANAGER_PORT=${MANAGER_PORT}|" .env

echo "[*] Starting containers..."
docker compose down || true
docker compose up -d --build

echo "[+] DONE"
echo "  Admin UI:   http://$(hostname -I | awk '{print $1}'):${MANAGER_PORT}/ui/admin"
echo "  Login:      ${ADMIN_USER} / ${ADMIN_PASSWORD}"
echo "  Secret:     $(grep '^MANAGER_SECRET=' .env | cut -d= -f2)"
