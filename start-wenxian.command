#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

load_env_file() {
  local env_file="$1"
  if [[ -f "$env_file" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$env_file"
    set +a
  fi
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
  echo "cd \"$SCRIPT_DIR\" && docker compose -f docker-compose.local.yml logs --tail=100"
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

echo "正在启动文献工作台 Docker 前后端..."
echo "数据目录：$APP_DATA_DIR"
echo "前端地址：http://127.0.0.1:$WEB_PORT"
echo "后端地址：http://127.0.0.1:$API_PORT/api/health"

docker compose -f docker-compose.local.yml up -d --build

wait_for_url "http://127.0.0.1:$API_PORT/api/health" "后端 API"
wait_for_url "http://127.0.0.1:$WEB_PORT" "前端页面"

open "http://127.0.0.1:$WEB_PORT"

echo
echo "文献工作台已经启动。"
echo "停止服务请双击 stop-wenxian.command"
echo "查看日志：cd \"$SCRIPT_DIR\" && docker compose -f docker-compose.local.yml logs -f"
