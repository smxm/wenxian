#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/wenxian}"
ARCHIVE_PATH="${1:-/opt/wenxian-release.tar.gz}"
TMP_ROOT="${APP_ROOT}.new"
BACKUP_ROOT="${APP_ROOT}.bak"

if [[ ! -f "$ARCHIVE_PATH" ]]; then
  echo "Archive not found: $ARCHIVE_PATH" >&2
  exit 1
fi

mkdir -p "$TMP_ROOT"
rm -rf "${TMP_ROOT:?}/"*
tar -xzf "$ARCHIVE_PATH" -C "$TMP_ROOT"

if [[ -f "${APP_ROOT}/.env" ]]; then
  cp "${APP_ROOT}/.env" "${TMP_ROOT}/.env"
fi

mkdir -p /opt/wenxian-data/api_runs
mkdir -p /opt/wenxian-secrets

if [[ -f "${APP_ROOT}/deploy/.htpasswd" && ! -f /opt/wenxian-secrets/.htpasswd ]]; then
  cp "${APP_ROOT}/deploy/.htpasswd" /opt/wenxian-secrets/.htpasswd
fi

if [[ -d "${APP_ROOT}/server-data/api_runs" ]]; then
  cp -a "${APP_ROOT}/server-data/api_runs/." /opt/wenxian-data/api_runs/
fi

if [[ -f "${TMP_ROOT}/.env" ]]; then
  if ! grep -q '^APP_DATA_DIR=' "${TMP_ROOT}/.env"; then
    printf '\nAPP_DATA_DIR=/opt/wenxian-data/api_runs\n' >> "${TMP_ROOT}/.env"
  fi
  if ! grep -q '^BASIC_AUTH_FILE=' "${TMP_ROOT}/.env"; then
    printf 'BASIC_AUTH_FILE=/opt/wenxian-secrets/.htpasswd\n' >> "${TMP_ROOT}/.env"
  fi
fi

rm -rf "$BACKUP_ROOT"
if [[ -d "$APP_ROOT" ]]; then
  mv "$APP_ROOT" "$BACKUP_ROOT"
fi
mv "$TMP_ROOT" "$APP_ROOT"

cd "$APP_ROOT"
docker compose up -d --build --force-recreate

echo "Update complete."
echo "App root: $APP_ROOT"
echo "Persistent data: /opt/wenxian-data/api_runs"
echo "Basic auth file: /opt/wenxian-secrets/.htpasswd"
