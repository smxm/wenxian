# wenxian

这是一个本地文献工作台仓库，当前把“检索策略生成、文献初筛、人工复核、全文获取、报告生成”串成了一套以线程式项目流转为核心的工作流。

## 仓库结构

- `literature_screening/`
  - 初筛主项目、本地 API、任务与数据集持久化
- `literature_screening/separated_modules/formal_report_module/`
  - 独立报告模块
- `literature_screening_web/`
  - Vue 3 Web 工作台
- `scripts/`
  - 运行数据导出、路径修复、相对路径迁移脚本

## 当前能力

### 项目 / 数据集 / 任务链

- 每次运行都会形成可追踪的 `Task`
- 初筛、人工复核、全文获取、报告任务都围绕同一个项目线程组织
- 初筛和审核产物会登记为 `Dataset`
- 支持从已有 `unused`、`included`、`included_reviewed`、`cumulative_included` 数据集继续筛选
- 支持 `parent_task_id` 形成任务链
- 项目内自动维护 `cumulative_included` 累计纳入集

### 检索策略与初筛

- 支持生成 Scopus、Web of Science、PubMed、CNKI 的检索式草案
- 输入格式支持 `.bib`、`.ris`、`.enw`、PubMed `.txt`
- 多文件合并与 DOI / 标题去重
- DeepSeek / Kimi 模型接入
- 达到目标纳入数后提前停止
- 输出纳入、剔除、`uncertain` 报告
- 默认导出 `RIS`，可选兼容导出 `BibTeX`

### 人工复核、全文与报告

- 可人工改判单篇或批量复核结果，并产出 reviewed 数据集
- 支持全文队列重建、状态维护、链接补全与仅全文就绪数据集
- 可基于单轮筛选结果或项目内一个或多个 dataset 生成报告
- 参考文献样式支持 `GB/T 7714` 和 `APA7`

### 平台与恢复能力

- 项目级模板 / preset
- 输入源管理：上传文件 + 复用已有数据集
- 中间态可视化：阶段、进度、进度消息
- 失败恢复 / 断点续跑：支持继续执行，初筛复用已完成 batch
- 搜索与过滤：按项目、任务类型、状态、关键词过滤
- 审计信息：任务事件流 / 时间线

## 推荐启动方式

当前推荐直接使用 Docker 本地启动，前端和后端会一起拉起。

### 前置条件

- 已安装并启动 Docker Desktop
- 推荐在仓库根目录 `.env` 中设置至少一个模型密钥：
  - `KIMI_API_KEY`
  - `DEEPSEEK_API_KEY`

首次配置可以在仓库根目录执行：

```bash
cp .env.example .env
```

### macOS 一键启动

稳定模式，适合直接使用、演示或验证生产构建效果：

在仓库根目录执行：

```bash
./start-wenxian.command
```

启动后默认地址：

- Web: `http://127.0.0.1:8080`
- API health: `http://127.0.0.1:8000/api/health`

停止服务：

```bash
./stop-wenxian.command
```

### macOS 开发热更新

开发模式，适合频繁改前端布局和后端接口，不需要每次改完都重建镜像：

```bash
./start-wenxian-dev.command
```

默认地址不变：

- Web: `http://127.0.0.1:8080`
- API health: `http://127.0.0.1:8000/api/health`

停止服务：

```bash
./stop-wenxian-dev.command
```

开发模式下：

- 前端使用 Vite，保存后自动热更新
- 后端使用 `uvicorn --reload`，Python 改动后自动重载
- 只有改了依赖、`package-lock.json`、Dockerfile，或者首次拉起缺少镜像时，才需要手动执行带 `--build` 的 compose 命令

### Windows 启动

Windows 上可以直接双击仓库根目录的脚本一键启动（需要先安装并启动 Docker Desktop）：

- 稳定模式（构建镜像后启动）：`start-wenxian.cmd`
- 开发热更新模式：`start-wenxian-dev.cmd`
- 停止服务：`stop-wenxian.cmd` / `stop-wenxian-dev.cmd`

如果 `8080` 端口被占用（例如 qBittorrent WebUI），可以先设置 `WEB_PORT`（如 `8081`）；脚本在未显式设置时也会自动尝试可用端口。

环境变量规则：

- 推荐只维护仓库根目录 `.env`
- `literature_screening/.env` 仍会被读取，但只作为旧配置兼容补缺
- 如果两个文件都定义了同名变量，根目录 `.env` 优先
- 占位符值（例如 `your_deepseek_api_key_here`）不会覆盖真实值

在仓库根目录执行：

```powershell
docker compose -f docker-compose.local.yml up -d --build
```

停止服务：

```powershell
docker compose -f docker-compose.local.yml down
```

如果你需要自定义运行数据目录或端口，可以在启动前先设置环境变量，例如：

```powershell
$env:APP_DATA_DIR = ".\literature_screening\data\api_runs"
$env:API_PORT = "8000"
$env:WEB_PORT = "8080"
docker compose -f docker-compose.local.yml up -d --build
```

### 通用 Docker 手动启动

如果不使用平台脚本，也可以直接执行下面这组命令；macOS、Linux、Windows PowerShell 都适用：

```bash
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml down
```

## 数据目录与路径策略

- 当前本地运行数据默认在 `literature_screening/data/api_runs`
- 持久化文件现在按 `api_runs` 根目录存储相对路径，降低跨机器迁移时的绝对路径漂移问题
- 对于旧项目或从其他工作目录迁移过来的数据，如果磁盘里仍残留 `.../api_runs/...` 形式的 Windows 绝对路径，服务端会在读取时尝试自动重映射到当前仓库的 `literature_screening/data/api_runs`
- API 为兼容现有调用方，仍保留绝对路径字段，同时新增了相对路径字段：
  - dataset: `path` + `relative_path`
  - task detail: `run_root` + `run_root_relative`
  - task detail: `output_dir` + `output_dir_relative`
- 如果导入的是旧机器导出的数据，先运行 `scripts/repair-api-runs-paths.py`，再运行 `scripts/relativize-api-runs-paths.py`

- 兼容旧数据时，`cumulative_included` 和全文队列会优先尝试从任务产物里的 `deduped_records.json` / `screening_decisions.json` 恢复记录，这样可以保留原始 `paper_id`、导入链接和筛选上下文，避免“已纳入但没进入全文队列”或多轮筛选累计纳入丢失的问题

## 常见排障

- `401 invalid api key`
  - 先检查仓库根目录 `.env` 里的 `KIMI_API_KEY` / `DEEPSEEK_API_KEY`
  - 如果还保留了 `literature_screening/.env`，确认里面没有误导性的旧值；这个文件现在只做兼容补缺
  - 再确认修改后已经执行 `stop-wenxian*.ps1` + `start-wenxian*.ps1` 重新创建容器
- 报告里反复出现 `Selected from reusable project dataset.`
  - 这通常不是模型真的只输出了这句，而是逐篇生成笔记时模型请求失败，系统退回到了兜底模板
  - 优先查看对应报告任务目录下 `report_output/logs/paper_note_errors.log`
- 旧项目迁移后“项目累计纳入”或全文队列数量不对
  - 先同步全文队列，系统会连带重建 `cumulative_included`
  - 如果旧数据来自不同工作目录，优先确认 `api_runs` 数据是否已经复制到当前仓库的 `literature_screening/data/api_runs`

## 前端开发说明

- 日常本地使用推荐走 Docker
- 如果你要高频改界面，优先用根目录的 `./start-wenxian-dev.command`
- 如果你要直接做前端开发，再进入 `literature_screening_web/` 使用 Node 工具链执行 `npm run dev`、`npm run typecheck`
- 仓库里的 Docker Web 构建也会在容器内执行 `npm run build`

## 独立报告命令行入口

```bash
python literature_screening/separated_modules/formal_report_module/scripts/run_simple_report.py \
  --screening-output-dir /path/to/screening_output \
  --report-output-dir /path/to/report_output \
  --project-topic "你的主题" \
  --provider deepseek \
  --model-name deepseek-chat \
  --api-base-url https://api.deepseek.com/v1 \
  --api-key-env DEEPSEEK_API_KEY
```

## 说明文档

- [主项目说明](./literature_screening/README.md)
- [架构说明](./literature_screening/docs/architecture.md)
- [Web 工作台说明](./literature_screening/docs/web-workbench.md)
- [独立报告模块说明](./literature_screening/separated_modules/formal_report_module/README.md)
