#!/bin/sh
set -eu
PROJECT_DIR="${GHOST_QNAP_DIR:-/share/Container/ghost-qnap-installer}"
REPO_URL="${GHOST_QNAP_REPO:-https://github.com/therepro21/ghost-qnap-installer.git}"

arch="$(uname -m)"
case "$arch" in
  x86_64|amd64|aarch64|arm64) ;;
  *) echo "Nicht unterstützt: $arch. Unterstützt werden Intel/AMD64 und ARM64." >&2; exit 1 ;;
esac
command -v docker >/dev/null || { echo "Docker/Container Station wurde nicht gefunden." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 wurde nicht gefunden." >&2; exit 1; }

if [ ! -d "$PROJECT_DIR/.git" ]; then
  command -v git >/dev/null || { echo "Git wurde nicht gefunden. Repository zuerst als ZIP entpacken." >&2; exit 1; }
  git clone "$REPO_URL" "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"
[ -f .env ] || cp .env.example .env

rand() { od -An -N24 -tx1 /dev/urandom | tr -d ' \n'; }
sed -i "s|^DATA_DIR=.*|DATA_DIR=/share/Container/ghost-qnap|" .env
sed -i "0,/^DB_PASSWORD=CHANGE_ME/s//DB_PASSWORD=$(rand)/" .env
sed -i "0,/^DB_ROOT_PASSWORD=CHANGE_ME/s//DB_ROOT_PASSWORD=$(rand)/" .env
manager_password="$(rand)"
sed -i "0,/^MANAGER_PASSWORD=CHANGE_ME/s//MANAGER_PASSWORD=$manager_password/" .env

echo "Ghost URL (z. B. http://192.168.1.100:2368):"
read -r ghost_url
[ -n "$ghost_url" ] && sed -i "s|^GHOST_URL=.*|GHOST_URL=$ghost_url|" .env
docker compose up -d --build
echo "Installation abgeschlossen."
echo "Ghost: $ghost_url"
echo "Manager-Kennwort: $manager_password"
