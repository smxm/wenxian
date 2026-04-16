#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
LOCAL_PROJECT_NAME="literature-screening-local"
DEV_PROJECT_NAME="literature-screening-dev"

trim_whitespace() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

strip_matching_quotes() {
  local value="$1"
  if [[ ${#value} -ge 2 ]]; then
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    fi
  fi
  printf '%s' "$value"
}

is_placeholder_value() {
  local normalized
  normalized="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$normalized" in
    your_*|*_here|example|example_*|sample|sample_*|placeholder|placeholder_*|changeme|change_me|replace_me|replace_with_*)
      return 0
      ;;
  esac
  [[ "$normalized" == *"your_kimi_api_key_here"* || "$normalized" == *"your_deepseek_api_key_here"* ]]
}

has_effective_env_value() {
  local key="$1"
  local current="${!key-}"
  [[ -n "$current" ]] || return 1
  is_placeholder_value "$current" && return 1
  return 0
}

load_env_file() {
  local env_file="$1"
  [[ -f "$env_file" ]] || return

  while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
    local line key value
    line="$(trim_whitespace "$raw_line")"
    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" == export\ * ]] && line="${line#export }"
    [[ "$line" != *=* ]] && continue

    key="$(trim_whitespace "${line%%=*}")"
    value="$(strip_matching_quotes "$(trim_whitespace "${line#*=}")")"
    [[ -n "$key" && -n "$value" ]] || continue
    is_placeholder_value "$value" && continue
    has_effective_env_value "$key" && continue

    export "$key=$value"
  done < "$env_file"
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

if [[ ! -f "$SCRIPT_DIR/.env" && -f "$SCRIPT_DIR/.env.example" ]]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo "已创建仓库根目录 .env，请在其中填写 API Key。"
fi

load_env_file "$SCRIPT_DIR/.env"
load_env_file "$SCRIPT_DIR/literature_screening/.env"

if [[ -f "$SCRIPT_DIR/literature_screening/.env" ]]; then
  echo "提示：literature_screening/.env 现在只作为旧配置兼容补缺；推荐统一改到仓库根目录 .env。"
fi

if [[ -n "${MOONSHOT_API_KEY:-}" ]] && ! has_effective_env_value KIMI_API_KEY; then
  export KIMI_API_KEY="$MOONSHOT_API_KEY"
fi

export APP_DATA_DIR="${APP_DATA_DIR:-$SCRIPT_DIR/literature_screening/data/api_runs}"
export API_PORT="${API_PORT:-8000}"
export WEB_PORT="${WEB_PORT:-8080}"

mkdir -p "$APP_DATA_DIR"

if [[ -z "${KIMI_API_KEY:-}" && -z "${DEEPSEEK_API_KEY:-}" ]]; then
  echo "提示：当前没有检测到 KIMI_API_KEY 或 DEEPSEEK_API_KEY。"
  echo "项目可以启动并查看已有数据，但新建 AI 任务前需要先配置 API Key。"
fi

echo "正在启动文献工作台 Docker 前后端..."
echo "数据目录：$APP_DATA_DIR"
echo "前端地址：http://127.0.0.1:$WEB_PORT"
echo "后端地址：http://127.0.0.1:$API_PORT/api/health"

stop_legacy_stacks
docker compose -p "$DEV_PROJECT_NAME" -f docker-compose.dev.yml down >/dev/null 2>&1 || true
docker compose -p "$LOCAL_PROJECT_NAME" -f docker-compose.local.yml up -d --build

wait_for_url "http://127.0.0.1:$API_PORT/api/health" "后端 API"
wait_for_url "http://127.0.0.1:$WEB_PORT" "前端页面"

open "http://127.0.0.1:$WEB_PORT"

echo
echo "文献工作台已经启动。"
echo "这是稳定模式：会重建镜像，适合演示和固定版本验证。"
echo "日常改界面或接口建议双击 start-wenxian-dev.command 使用热更新模式。"
echo "停止服务请双击 stop-wenxian.command"
echo "查看日志：cd \"$SCRIPT_DIR\" && docker compose -p \"$LOCAL_PROJECT_NAME\" -f docker-compose.local.yml logs -f"
