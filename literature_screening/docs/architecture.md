# 架构说明

## 1. 仓库分层

当前仓库按职责分成三层：

### 初筛主项目

路径：

- `E:\wenxian\literature_screening\src\literature_screening`

职责：

- 读取输入文件
- 标准化文献记录
- 去重
- 按批次调用 LLM 初筛
- 生成初筛报告
- 导出 `RIS` / `BibTeX`

### 独立报告模块

路径：

- `E:\wenxian\literature_screening\separated_modules\formal_report_module`

职责：

- 读取初筛结果
- 生成简洁综述式报告
- 生成参考列表

### 新 Web 工作台

路径：

- `E:\wenxian\literature_screening_web`

职责：

- 提供现代化交互界面
- 管理任务创建、状态轮询、结果查看和文件下载
- 通过本地 API 访问初筛主项目与独立报告模块

## 2. 主项目结构

```text
src/literature_screening/
  api/            本地 API 适配层
  bibtex/         输入解析、标准化、去重、导出
  core/           配置、模型、常量、异常、环境变量
  pipeline/       主流程编排
  reporting/      初筛结果报告
  screening/      Prompt、批次、LLM 客户端、响应校验
  studio/         前端/API 共用的编排服务层
```

### `bibtex/`

- `parser.py`
  - 负责解析 `.bib`、`.ris`、`.enw`、PubMed `.txt`
- `normalizer.py`
  - 标题标准化、作者和文本清洗
- `deduper.py`
  - DOI 与标题去重
- `exporter.py`
  - 导出 `RIS` / `BibTeX`

### `screening/`

- `batcher.py`
  - 批量切分
- `llm_client.py`
  - 统一封装 `Kimi` / `DeepSeek`
- `prompt_builder.py`
  - 生成初筛 Prompt
- `response_parser.py`
  - 解析模型输出
- `validator.py`
  - 校验返回的 `paper_id` 集合与批次完整性

### `api/`

- `app.py`
  - FastAPI 入口
- `schemas.py`
  - API 请求/响应模型
- `task_store.py`
  - 本地任务状态存储与后台线程调度

### `studio/`

- `service.py`
  - Web 前端与兼容版 Streamlit 共用的编排服务层

## 3. 前端结构

兼容版 Streamlit：

- `E:\wenxian\literature_screening\frontend_app`

新的 Web 工作台：

- `E:\wenxian\literature_screening_web\src\api`
- `E:\wenxian\literature_screening_web\src\stores`
- `E:\wenxian\literature_screening_web\src\views`
- `E:\wenxian\literature_screening_web\src\components`
- `E:\wenxian\literature_screening_web\src\router`

## 4. API 适配层

新增本地 API 的目的，是让前端不直接依赖 Python 脚本和本地输出目录结构。

当前接口职责：

- 创建初筛任务
- 创建报告任务
- 提供任务列表与详情
- 提供产物下载接口

## 5. 配置原则

主项目入口使用 YAML 配置，示例文件：

- `E:\wenxian\literature_screening\configs\config.example.yaml`

配置分为：

- `project`
- `input`
- `dedup`
- `screening`
- `criteria`
- `model`
- `report`

## 6. 当前发布分支保留内容

发布分支只保留：

- 代码
- 最小测试
- 示例配置
- Prompt 和 Schema
- 必要说明文档

不再保留：

- 试跑输入数据
- 临时调试文件
- 运行输出目录
- 过程性工作日志
