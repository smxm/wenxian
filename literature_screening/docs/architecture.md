# 架构说明

## 1. 仓库分层

当前仓库按职责分成三层：

### 初筛主项目

路径：

- `E:\wenxian\literature_screening\src\literature_screening`

职责：

- 输入解析
- 标准化文献记录
- 去重
- 分批调用 LLM 初筛
- 生成初筛报告
- 导出 `RIS` / `BibTeX`
- 提供项目 / 数据集 / 任务链 API

### 独立报告模块

路径：

- `E:\wenxian\literature_screening\separated_modules\formal_report_module`

职责：

- 读取初筛结果或项目数据集
- 生成简洁综述式报告
- 生成参考列表

### Web 工作台

路径：

- `E:\wenxian\literature_screening_web`

职责：

- 提供现代化交互界面
- 管理项目、任务、数据集和模板
- 展示中间态、任务事件和产物下载

## 2. 主项目结构

```text
src/literature_screening/
  api/            本地 API 适配层
  bibtex/         输入解析、标准化、去重、导出
  core/           配置、模型、常量、异常、环境变量
  pipeline/       主流程编排
  reporting/      初筛结果报告
  screening/      Prompt、批次、LLM 客户端、响应校验
  studio/         前端/API 共用编排服务层
```

### `api/`

- `app.py`
  - FastAPI 入口
- `schemas.py`
  - API 请求 / 响应模型
- `task_store.py`
  - 任务状态、事件流、后台执行与重试
- `workspace_store.py`
  - Project / Dataset 存储
- `template_store.py`
  - 任务模板存储

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
  - Web 前端与旧 Streamlit 共用的编排层
  - 这里负责把“项目任务请求”转成真正的初筛 / 报告执行

## 3. 核心工作流模型

### Project

用于承载一个真实主题或委托项目：

- `project_id`
- `name`
- `topic`
- `description`

### Task

用于记录一次具体执行：

- `screening`
- `report`

关键字段：

- `project_id`
- `parent_task_id`
- `input_dataset_ids`
- `output_dataset_ids`
- `attempt_count`

### Dataset

用于记录任务产出的可复用文献集合：

- `included`
- `excluded`
- `unused`
- `cumulative_included`
- `included_reviewed`
- `excluded_reviewed`

## 4. 关键能力

### 结果合并策略

- 项目内会自动重建 `cumulative_included`
- 该数据集用于跨轮次合并纳入结果

### 失败恢复 / 断点续跑

- 初筛任务重试时复用同一 task 工作目录
- 已完成 batch 会直接从现有输出恢复
- 报告任务重试时复用同一 report 输出目录

### 审核与人工修正

- 可对单篇结果执行人工改判
- 会生成 reviewed decisions 和 reviewed RIS
- reviewed 产物会再次登记为 dataset

### 审计与日志

- 每个任务都有事件流
- 会记录创建、启动、成功、失败、重试、人工审核等操作

## 5. 配置与隔离原则

- API Key 只保存在环境变量中
- 任务元数据只记录环境变量名，不记录明文 key
- 模板按项目隔离
- 数据集和任务按项目归档

## 6. 发布分支保留内容

发布分支只保留：

- 主体代码
- 最小测试
- 示例配置
- Prompt 和 Schema
- 必要文档

不保留：

- 试跑输入数据
- 临时调试文件
- 运行输出目录
