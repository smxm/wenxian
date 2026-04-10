#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
DEV_PROJECT_NAME="literature-screening-dev"

stop_legacy_stacks() {
  docker compose -f docker-compose.local.yml down >/dev/null 2>&1 || true
  docker compose -f docker-compose.dev.yml down >/dev/null 2>&1 || true
}

if ! command -v docker >/dev/null 2>&1; then
  echo "未检测到 docker，无法停止容器。"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker Desktop 还没有启动。"
  exit 1
fi

echo "正在停止文献工作台开发模式..."
stop_legacy_stacks
docker compose -p "$DEV_PROJECT_NAME" -f docker-compose.dev.yml down
echo "文献工作台开发模式已经停止。"
