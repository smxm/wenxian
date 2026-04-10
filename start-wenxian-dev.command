#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
LOCAL_PROJECT_NAME="literature-screening-local"
DEV_PROJECT_NAME="literature-screening-dev"

load_env_file() {
  local env_file="$1"
  if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  fi
}

stop_legacy_stacks() {
  docker compose -f docker-compose.local.yml down >/dev/null 2>&1 || true
  docker compose -f docker-compose.dev.yml down >/dev/null 2>&1 || true
}

wait_for_url() {
  local url="$1"
  local name="$2"
  local attempts="${3:-60}"

  for ((i = 1; i <= attempts; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "$name 已就绪：$url"
      return 0
    fi
    sleep 2
  done

  echo "$name 启动超时，请运行下面命令查看日志："
  echo "cd \"$SCRIPT_DIR\" && docker compose -p \"$DEV_PROJECT_NAME\" -f docker-compose.dev.yml logs --tail=100"
  return 1
}

if ! command -v docker >/dev/null 2>&1; then
  echo "未检测到 docker，请先安装 Docker Desktop。"
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker Desktop 还没有启动，请先打开 Docker。"
  exit 1
fi

load_env_file "$SCRIPT_DIR/.env"
load_env_file "$SCRIPT_DIR/literature_screening/.env"

if [[ -n "${MOONSHOT_API_KEY:-}" && -z "${KIMI_API_KEY:-}" ]]; then
  export KIMI_API_KEY="$MOONSHOT_API_KEY"
fi

export APP_DATA_DIR="${APP_DATA_DIR:-$SCRIPT_DIR/literature_screening/data/api_runs}"
export API_PORT="${API_PORT:-8000}"
export WEB_PORT="${WEB_PORT:-8080}"

mkdir -p "$APP_DATA_DIR"

if [[ ! -f "$SCRIPT_DIR/literature_screening/.env" ]]; then
  cp "$SCRIPT_DIR/literature_screening/.env.example" "$SCRIPT_DIR/literature_screening/.env"
  echo "已创建 literature_screening/.env，可按需补充 API Key。"
fi

if [[ -z "${KIMI_API_KEY:-}" && -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "提示：当前没有检测到 KIMI_API_KEY 或 DEEPSEEK_API_KEY。"
  echo "项目可以启动并查看已有数据，但新建 AI 任务前需要先配置 API Key。"
fi

echo "正在启动文献工作台开发模式..."
echo "数据目录：$APP_DATA_DIR"
echo "前端热更新地址：http://127.0.0.1:$WEB_PORT"
echo "后端热重载地址：http://127.0.0.1:$API_PORT/api/health"

stop_legacy_stacks
docker compose -p "$LOCAL_PROJECT_NAME" -f docker-compose.local.yml down >/dev/null 2>&1 || true
docker compose -p "$DEV_PROJECT_NAME" -f docker-compose.dev.yml up -d

wait_for_url "http://127.0.0.1:$API_PORT/api/health" "后端 API"
wait_for_url "http://127.0.0.1:$WEB_PORT" "前端页面"

open "http://127.0.0.1:$WEB_PORT"

echo
echo "文献工作台开发模式已经启动。"
echo "前端源码保存后会自动热更新，后端 Python 改动会自动重载。"
echo "只有改依赖或 Dockerfile 时，才需要手动执行带 --build 的 compose 命令。"
echo "停止服务请双击 stop-wenxian-dev.command"
echo "查看日志：cd \"$SCRIPT_DIR\" && docker compose -p \"$DEV_PROJECT_NAME\" -f docker-compose.dev.yml logs -f"
