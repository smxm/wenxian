# 架构说明

## 1. 仓库分层

当前仓库按职责分成三层：

### 初筛主项目

路径：

- `literature_screening/`

职责：

- 输入解析与标准化
- 合并与去重
- 检索策略生成
- 分批调用 LLM 执行标题 / 摘要级初筛
- 任务、项目、数据集与模板 API
- 全文队列与状态管理
- 报告任务编排

### 独立报告模块

路径：

- `literature_screening/separated_modules/formal_report_module/`

职责：

- 读取已有筛选输出
- 生成简洁报告或更正式的报告产物
- 生成参考文献列表

### Web 工作台

路径：

- `literature_screening_web/`

职责：

- 提供线程式项目界面
- 管理任务、数据集、模板和全文工作台
- 展示中间态、任务事件和产物下载

## 2. 本地运行拓扑

当前推荐使用 Docker 本地运行：

- `api`
  - FastAPI 服务
  - 默认端口 `8000`
- `web`
  - Vue 构建产物 + nginx
  - 默认端口 `8080`

推荐入口：

- 仓库根目录的 `./start-wenxian.command`
- 仓库根目录的 `./stop-wenxian.command`
- 或手动执行 `docker compose -f docker-compose.local.yml up -d --build`

运行数据默认挂载到：

- `literature_screening/data/api_runs`

## 3. 主项目结构

```text
src/literature_screening/
  api/            FastAPI 入口、schema、任务与项目存储
  bibtex/         输入解析、标准化、去重、导出
  core/           配置、模型、常量、环境变量
  pipeline/       初筛主流程编排
  reporting/      初筛结果报告
  screening/      Prompt、批次、LLM 客户端、响应校验
  studio/         API / Web 共用服务编排层
  storage_paths.py 持久化路径脱水/回填辅助
```

### `api/`

- `app.py`
  - FastAPI 入口
  - 项目、任务、全文、模板、报告相关接口
- `schemas.py`
  - API 请求 / 响应模型
- `task_store.py`
  - 任务状态、事件流、后台执行与重试
- `workspace_store.py`
  - `Project` / `Dataset` / 全文队列存储
- `template_store.py`
  - 任务模板存储
- `secret_store.py`
  - API key 引用存储

### `bibtex/`

- `parser.py`
  - 解析 `.bib`、`.ris`、`.enw`、PubMed `.txt`
- `normalizer.py`
  - 标题标准化、作者和文本清洗
- `deduper.py`
  - DOI 与标题去重
- `exporter.py`
  - 导出 `RIS` / `BibTeX`

### `screening/`

- `batcher.py`
  - 批次切分
- `llm_client.py`
  - 统一封装 Kimi / DeepSeek
- `prompt_builder.py`
  - 生成初筛 Prompt
- `response_parser.py`
  - 解析模型输出
- `validator.py`
  - 校验 `paper_id` 集合与批次完整性

### `studio/`

- `service.py`
  - 把策略、初筛、报告请求转成真正的执行任务
  - 负责 API 与旧 Streamlit 兼容层共享的编排逻辑

## 4. 核心工作流模型

### Thread / Project

UI 现在更偏向“thread”概念，但持久化模型仍然是 `Project`：

- `project_id`
- `name`
- `topic`
- `description`

### Task

一次具体执行对应一个 `Task`，当前主要有三类：

- `strategy`
- `screening`
- `report`

关键字段：

- `project_id`
- `parent_task_id`
- `input_dataset_ids`
- `output_dataset_ids`
- `attempt_count`
- `run_root`
- `output_dir`

### Dataset

用于记录任务产出的可复用文献集合：

- `included`
- `excluded`
- `unused`
- `included_reviewed`
- `excluded_reviewed`
- `cumulative_included`
- `fulltext_ready`
- `report_source`

## 5. 路径持久化与存储策略

运行数据保存在 `api_runs` 根目录下，主要包括：

- `projects/`
- `tasks/`
- `runs/`
- `templates/`

当前磁盘存储策略是：

- 写盘时把 `path`、`run_root`、`output_dir` 等字段脱水为相对 `api_runs` 的路径
- 读盘时再回填成当前机器可访问的绝对路径

这层能力由：

- `src/literature_screening/storage_paths.py`
- `api/task_store.py`
- `api/workspace_store.py`

共同实现。

为了兼容现有调用方，API 响应现在同时返回：

- dataset: `path` + `relative_path`
- task detail: `run_root` + `run_root_relative`
- task detail: `output_dir` + `output_dir_relative`

因此：

- 磁盘格式以相对路径为准
- 服务端运行逻辑继续使用 hydrated 绝对路径
- 前端和外部调用方可以逐步迁移到相对路径字段

## 6. 核心工作流边界

### 策略生成

- 生成 Scopus、Web of Science、PubMed、CNKI 检索式草案
- 产出结构化策略计划和 Markdown 结果

### 初筛

- 多文件导入
- 合并去重
- 分批调用模型
- 导出纳入、剔除、未使用结果

### 人工复核

- 单篇改判
- 批量改判
- 参考文献顺序重排
- 复核后数据集再登记回项目

### 全文工作台

- 基于纳入数据集重建全文队列
- 维护状态、备注、链接与 OA 信息
- 生成 `fulltext_ready` 数据集供报告使用

### 报告

- 可直接基于某轮筛选结果生成
- 也可基于项目内一个或多个 dataset 生成
- 简洁报告主流程依赖独立报告模块

## 7. 设计原则

- API key 只从环境变量读取，不写入任务或项目数据
- 项目、任务、数据集分层先于页面表达
- 持久化格式优先考虑跨机器迁移稳定性
- 前端只依赖 `/api/...` 与 artifact 下载端点，不直接依赖磁盘目录结构
- 新功能优先扩 `studio/service.py`、`api/app.py` 和 store 层，再补 UI
