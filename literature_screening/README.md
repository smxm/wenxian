# 文献初筛主项目

`literature_screening/` 是后端主项目，负责初筛、API、任务与数据集持久化，以及把策略、筛选、全文工作台和报告任务串进同一个线程式项目流程。

## 当前边界

主项目负责：

- 输入解析、标准化、合并与去重
- 分批调用模型进行标题/摘要级初筛
- 任务、项目、数据集、全文工作台与报告源的 API
- 初筛进度、任务事件、重试、取消、删除和部分产物保留
- 为报告模块准备筛选输出或项目数据集来源

报告成稿、参考文献格式和简洁报告正文生成主要位于：

- `separated_modules/formal_report_module/`

## 输入格式

- `.bib`
- `.ris`
- `.enw`
- PubMed `.txt`

## 当前能力

- 多文件输入和 DOI / 标题去重
- DeepSeek / Kimi 模型接入
- 通过 provider `/models` 接口发现可选模型
- 达到目标纳入数后停止
- 运行中实时写入 processed / included / excluded / uncertain / unused 计数
- 默认 RIS 导出，可选 BibTeX 导出
- 人工复核与 reviewed RIS
- 项目级 `cumulative_included`、`fulltext_ready`、`report_source` 派生数据集

## 本地运行

日常推荐在仓库根目录使用 Docker 启动：

```bash
./start-wenxian.command
```

停止：

```bash
./stop-wenxian.command
```

开发热更新：

```bash
./start-wenxian-dev.command
```

如果只启动后端 API：

```bash
cd literature_screening
PYTHONPATH=src python -m uvicorn literature_screening.api.app:app --host 127.0.0.1 --port 8000
```

至少在仓库根目录 `.env` 或系统环境变量中设置一个模型密钥：

- `KIMI_API_KEY`
- `DEEPSEEK_API_KEY`

`literature_screening/.env.example` 只保留给旧流程兼容；当前优先读取仓库根目录 `.env`。

## 命令行筛选入口

```bash
cd literature_screening
PYTHONPATH=src python -m literature_screening.main --config configs/config.example.yaml
```

仅检查配置：

```bash
cd literature_screening
PYTHONPATH=src python -m literature_screening.main --config configs/config.example.yaml --dry-run
```

## 目录

```text
literature_screening/
  configs/                 示例配置
  frontend_app/            兼容版 Streamlit 前端
  prompts/                 初筛 Prompt 与输出 Schema
  separated_modules/       报告等扩展模块
  src/                     主项目源码
  tests/                   主项目测试
```

## 当前文档入口

- `../project_state.md`
- `../docs/project_atlas/index.md`
- `../docs/project_atlas/change-routing.md`
- `../docs/project_atlas/modules/backend-api-and-storage.md`
- `../docs/project_atlas/modules/screening-and-data-pipeline.md`
- `../docs/project_atlas/modules/reporting-and-formal-report.md`

旧的架构和 Web 工作台说明已经归档到：

- `../docs/archive/legacy-docs/literature_screening/`
