#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/wenxian}"
DATA_DIR="${APP_DATA_DIR:-/opt/wenxian-data/api_runs}"
AUTH_FILE="${BASIC_AUTH_FILE:-/opt/wenxian-secrets/.htpasswd}"
ENV_FILE="${APP_ROOT}/.env"

mkdir -p "$DATA_DIR"
mkdir -p "$(dirname "$AUTH_FILE")"

if [[ -d "${APP_ROOT}/server-data/api_runs" ]]; then
  cp -a "${APP_ROOT}/server-data/api_runs/." "$DATA_DIR/"
fi

if [[ -f "${APP_ROOT}/deploy/.htpasswd" && ! -f "$AUTH_FILE" ]]; then
  cp "${APP_ROOT}/deploy/.htpasswd" "$AUTH_FILE"
fi

touch "$ENV_FILE"

if ! grep -q '^APP_DATA_DIR=' "$ENV_FILE"; then
  printf '\nAPP_DATA_DIR=%s\n' "$DATA_DIR" >> "$ENV_FILE"
fi

if ! grep -q '^BASIC_AUTH_FILE=' "$ENV_FILE"; then
  printf 'BASIC_AUTH_FILE=%s\n' "$AUTH_FILE" >> "$ENV_FILE"
fi

echo "Migration complete."
echo "APP_DATA_DIR=$DATA_DIR"
echo "BASIC_AUTH_FILE=$AUTH_FILE"
