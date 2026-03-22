# AI自动筛选整理文献系统技术设计文档

## 1. 文档目的

本文档用于将项目方案进一步细化为可开发、可实现、可测试的技术设计说明，覆盖以下内容：

- 系统模块划分
- 推荐目录结构
- 配置文件格式
- 核心数据结构
- JSON Schema 设计
- 输入输出约定
- 批处理与停止逻辑
- 错误处理与日志设计
- 开发顺序建议

本文档默认以 Python 命令行项目为目标实现形态，模型接入默认使用 Kimi API，后续保留扩展空间。

---

## 2. 设计原则

### 2.1 核心原则

- 先保证主链路可跑通，再逐步增强
- 所有关键中间结果可追踪、可落盘
- 模型输入与输出必须结构化
- 业务状态明确，避免未处理文献与已排除文献混淆
- 配置优先，不把关键参数硬编码在代码中

### 2.2 当前阶段技术边界

- 单机本地运行
- 命令行触发
- 文件级输入输出
- 无数据库依赖
- 无前端界面

---

## 3. 系统架构概览

### 3.1 模块分层

系统建议划分为以下模块：

1. `config`
2. `models`
3. `bibtex`
4. `screening`
5. `reporting`
6. `pipeline`
7. `cli`

### 3.2 模块职责

`config`

- 读取 YAML/TOML/JSON 配置
- 校验运行参数
- 提供默认值

`models`

- 定义系统内部数据模型
- 统一枚举值和状态值

`bibtex`

- 读取 `.bib` 文件
- 解析 BibTeX 记录
- 标准化字段
- 执行合并与去重
- 导出 BibTeX

`screening`

- 将文献组装成 AI 输入批次
- 构建 prompt
- 调用 Kimi API
- 校验并解析 AI 返回结果

`reporting`

- 生成运行总结
- 生成纳入/排除/未确定报告
- 输出中间结果和最终结果

`pipeline`

- 串联完整业务流程
- 控制批处理与停止逻辑
- 更新状态并汇总统计

`cli`

- 提供命令行入口
- 接收用户参数
- 调起主流程

---

## 4. 推荐项目目录结构

```text
literature_screening/
  README.md
  pyproject.toml
  .env.example
  configs/
    config.example.yaml
  data/
    input/
    output/
    cache/
    logs/
  prompts/
    screening_prompt.md
    screening_output_schema.json
  src/
    literature_screening/
      __init__.py
      main.py
      cli.py
      core/
        config.py
        constants.py
        exceptions.py
        models.py
        schema.py
      bibtex/
        parser.py
        normalizer.py
        deduper.py
        exporter.py
      screening/
        batcher.py
        prompt_builder.py
        kimi_client.py
        response_parser.py
        validator.py
      reporting/
        report_generator.py
        summary_builder.py
        writers.py
      pipeline/
        run_pipeline.py
        state_manager.py
  tests/
    test_parser.py
    test_deduper.py
    test_batcher.py
    test_response_parser.py
    test_pipeline.py
```

---

## 5. 运行流程设计

### 5.1 主流程

```text
读取配置
  -> 扫描输入 BibTeX 文件
  -> 解析所有 BibTeX 记录
  -> 标准化字段
  -> 合并与去重
  -> 生成统一文献池
  -> 按 batch_size 切分未处理文献
  -> 构建 AI prompt
  -> 调用 Kimi API
  -> 解析并校验返回 JSON
  -> 更新文献状态
  -> 判断是否达到 target_include_count
  -> 若未达到则继续下一批
  -> 若达到则停止并标记剩余文献为 unused
  -> 生成报告与导出 BibTeX
```

### 5.2 运行状态转移

文献状态建议采用以下枚举：

- `unprocessed`
- `included`
- `excluded`
- `uncertain`
- `unused`
- `error`

状态流转建议如下：

```text
unprocessed -> included
unprocessed -> excluded
unprocessed -> uncertain
unprocessed -> error
unprocessed -> unused
```

说明：

- `unused` 仅用于因提前停止而未送审的文献
- `error` 仅用于解析失败或单条处理异常时的兜底标记

---

## 6. 配置设计

### 6.1 推荐配置文件格式

推荐优先支持 YAML，原因如下：

- 结构清晰
- 易读性好
- 适合表达嵌套配置

同时可以保留后续支持 JSON 或 TOML 的能力。

### 6.2 配置文件示例

建议文件路径：

- `configs/config.example.yaml`
- 用户运行时可传入 `configs/project_a.yaml`

示例：

```yaml
project:
  name: "burrowing-robot-screening"
  output_dir: "./data/output/run_001"
  save_raw_response: true
  save_intermediate_files: true

input:
  bib_files:
    - "./data/input/scopus_export_1.bib"
    - "./data/input/scopus_export_2.bib"
  encoding: "utf-8"

dedup:
  enabled: true
  strict_doi_match: true
  normalized_title_exact_match: true
  fuzzy_title_match: false

screening:
  batch_size: 20
  target_include_count: 50
  stop_when_target_reached: true
  allow_uncertain: true
  retry_times: 2
  request_timeout_seconds: 120

criteria:
  topic: "地下钻进机器人推进与破土机制"
  inclusion:
    - "研究对象必须为能在土壤、砂土、行星风化层或地表以下介质中推进或挖掘的机器人系统"
    - "重点关注推进、破土、钻进、切削、冲击、振动液化、仿生掘进、生长式推进等机制"
    - "涉及机构设计、运动学建模、机器人-颗粒介质相互作用或实验验证"
  exclusion:
    - "传统大型工业掘进设备"
    - "仅在既有管道内移动且不具备自主破土能力的管道机器人"
    - "纯水下机器人或纯空中飞行器"
    - "无机器人载体背景的纯土力学或纯地质研究"

model:
  provider: "kimi"
  model_name: "moonshot-v1-auto"
  api_base_url: "https://api.moonshot.cn/v1"
  api_key_env: "KIMI_API_KEY"
  temperature: 0.2

report:
  export_included_bib: true
  export_excluded_bib: false
  export_unused_bib: true
  included_report_format: "md"
  excluded_report_format: "md"
  summary_format: "json"
```

### 6.3 配置字段说明

`project`

- `name`: 当前任务名称
- `output_dir`: 输出目录
- `save_raw_response`: 是否保存原始 API 返回文本
- `save_intermediate_files`: 是否保存中间 JSON 文件

`input`

- `bib_files`: 输入 BibTeX 文件列表
- `encoding`: 输入文件编码，默认 `utf-8`

`dedup`

- `enabled`: 是否启用去重
- `strict_doi_match`: 是否启用 DOI 强去重
- `normalized_title_exact_match`: 是否启用标题标准化精确匹配
- `fuzzy_title_match`: 是否启用模糊去重，MVP 默认关闭

`screening`

- `batch_size`: 每批文献数量
- `target_include_count`: 目标纳入数
- `stop_when_target_reached`: 达标后是否停止
- `allow_uncertain`: 是否允许输出 `uncertain`
- `retry_times`: API 或解析失败重试次数
- `request_timeout_seconds`: 请求超时时间

`criteria`

- `topic`: 当前筛选主题
- `inclusion`: 纳入标准列表
- `exclusion`: 排除标准列表

`model`

- `provider`: 模型提供方
- `model_name`: 具体模型名称
- `api_base_url`: API 地址
- `api_key_env`: API key 对应环境变量名
- `temperature`: 模型温度

`report`

- `export_included_bib`
- `export_excluded_bib`
- `export_unused_bib`
- `included_report_format`
- `excluded_report_format`
- `summary_format`

---

## 7. 环境变量设计

建议通过 `.env` 或系统环境变量注入敏感信息。

`.env.example` 示例：

```env
KIMI_API_KEY=your_api_key_here
```

代码中仅读取环境变量名，不在配置文件中直接写明密钥值。

---

## 8. 核心数据模型设计

### 8.1 `PaperRecord`

```json
{
  "paper_id": "paper_000001",
  "entry_type": "article",
  "title": "Propulsion mechanism of subterranean robots in granular media",
  "authors": [
    "Alice Smith",
    "Bob Lee"
  ],
  "year": 2024,
  "journal": "Robotics and Autonomous Systems",
  "doi": "10.1000/example-doi",
  "abstract": "This paper studies ...",
  "keywords": [
    "burrowing robot",
    "granular media"
  ],
  "normalized_title": "propulsion mechanism of subterranean robots in granular media",
  "raw_bibtex": "@article{...}",
  "source_files": [
    "scopus_export_1.bib",
    "scopus_export_2.bib"
  ],
  "source_keys": [
    "Smith2024A",
    "Smith2024B"
  ],
  "merged_from": [
    "raw_000012",
    "raw_000089"
  ],
  "status": "unprocessed"
}
```

### 8.2 `ScreeningDecision`

```json
{
  "paper_id": "paper_000001",
  "batch_id": "batch_0001",
  "decision": "include",
  "reason": "研究对象和推进机制均与筛选主题直接相关。",
  "evidence": [
    "title",
    "abstract",
    "keywords"
  ],
  "confidence": 0.91,
  "screen_stage": "title_abstract",
  "model_provider": "kimi",
  "model_name": "moonshot-v1-auto",
  "timestamp": "2026-03-20T14:10:00+08:00"
}
```

### 8.3 `BatchRequestRecord`

```json
{
  "batch_id": "batch_0001",
  "paper_ids": [
    "paper_000001",
    "paper_000002"
  ],
  "paper_count": 2,
  "criteria_snapshot": {
    "topic": "地下钻进机器人推进与破土机制"
  },
  "model_provider": "kimi",
  "model_name": "moonshot-v1-auto",
  "created_at": "2026-03-20T14:00:00+08:00"
}
```

### 8.4 `RunSummary`

```json
{
  "run_id": "run_20260320_140000",
  "input_files_count": 5,
  "raw_entries_count": 320,
  "deduped_entries_count": 270,
  "processed_count": 80,
  "included_count": 51,
  "excluded_count": 24,
  "uncertain_count": 5,
  "unused_count": 190,
  "batch_count": 4,
  "api_call_count": 4,
  "stop_reason": "target_include_count_reached",
  "started_at": "2026-03-20T14:00:00+08:00",
  "finished_at": "2026-03-20T14:15:00+08:00"
}
```

---

## 9. JSON Schema 设计

### 9.1 运行配置 Schema

建议文件：

- `src/literature_screening/core/schema.py`
- 或单独保存为 `schemas/run_config.schema.json`

示例：

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RunConfig",
  "type": "object",
  "required": ["project", "input", "screening", "criteria", "model", "report"],
  "properties": {
    "project": {
      "type": "object",
      "required": ["name", "output_dir"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "output_dir": { "type": "string", "minLength": 1 },
        "save_raw_response": { "type": "boolean", "default": true },
        "save_intermediate_files": { "type": "boolean", "default": true }
      },
      "additionalProperties": false
    },
    "input": {
      "type": "object",
      "required": ["bib_files"],
      "properties": {
        "bib_files": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "minLength": 1 }
        },
        "encoding": { "type": "string", "default": "utf-8" }
      },
      "additionalProperties": false
    },
    "screening": {
      "type": "object",
      "required": ["batch_size", "target_include_count", "stop_when_target_reached"],
      "properties": {
        "batch_size": { "type": "integer", "minimum": 1, "maximum": 100, "default": 20 },
        "target_include_count": { "type": "integer", "minimum": 1 },
        "stop_when_target_reached": { "type": "boolean", "default": true },
        "allow_uncertain": { "type": "boolean", "default": true },
        "retry_times": { "type": "integer", "minimum": 0, "maximum": 10, "default": 2 },
        "request_timeout_seconds": { "type": "integer", "minimum": 10, "maximum": 600, "default": 120 }
      },
      "additionalProperties": false
    },
    "criteria": {
      "type": "object",
      "required": ["topic", "inclusion", "exclusion"],
      "properties": {
        "topic": { "type": "string", "minLength": 1 },
        "inclusion": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "minLength": 1 }
        },
        "exclusion": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "minLength": 1 }
        }
      },
      "additionalProperties": false
    },
    "model": {
      "type": "object",
      "required": ["provider", "model_name", "api_base_url", "api_key_env"],
      "properties": {
        "provider": { "type": "string", "enum": ["kimi"] },
        "model_name": { "type": "string", "minLength": 1 },
        "api_base_url": { "type": "string", "minLength": 1 },
        "api_key_env": { "type": "string", "minLength": 1 },
        "temperature": { "type": "number", "minimum": 0, "maximum": 2, "default": 0.2 }
      },
      "additionalProperties": false
    },
    "report": {
      "type": "object",
      "required": ["export_included_bib", "export_unused_bib"],
      "properties": {
        "export_included_bib": { "type": "boolean", "default": true },
        "export_excluded_bib": { "type": "boolean", "default": false },
        "export_unused_bib": { "type": "boolean", "default": true },
        "included_report_format": { "type": "string", "enum": ["md", "json"], "default": "md" },
        "excluded_report_format": { "type": "string", "enum": ["md", "json"], "default": "md" },
        "summary_format": { "type": "string", "enum": ["json"], "default": "json" }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 9.2 `PaperRecord` Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PaperRecord",
  "type": "object",
  "required": [
    "paper_id",
    "title",
    "authors",
    "source_files",
    "source_keys",
    "status"
  ],
  "properties": {
    "paper_id": { "type": "string", "minLength": 1 },
    "entry_type": { "type": ["string", "null"] },
    "title": { "type": "string", "minLength": 1 },
    "authors": {
      "type": "array",
      "items": { "type": "string" }
    },
    "year": { "type": ["integer", "null"] },
    "journal": { "type": ["string", "null"] },
    "doi": { "type": ["string", "null"] },
    "abstract": { "type": ["string", "null"] },
    "keywords": {
      "type": "array",
      "items": { "type": "string" }
    },
    "normalized_title": { "type": ["string", "null"] },
    "raw_bibtex": { "type": ["string", "null"] },
    "source_files": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    },
    "source_keys": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    },
    "merged_from": {
      "type": "array",
      "items": { "type": "string" }
    },
    "status": {
      "type": "string",
      "enum": ["unprocessed", "included", "excluded", "uncertain", "unused", "error"]
    }
  },
  "additionalProperties": false
}
```

### 9.3 AI 返回结果 Schema

这份 Schema 非常关键，建议同时用于：

- prompt 中提示模型输出结构
- 本地响应校验

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "BatchScreeningResponse",
  "type": "object",
  "required": ["batch_id", "results"],
  "properties": {
    "batch_id": { "type": "string", "minLength": 1 },
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["paper_id", "decision", "reason", "evidence", "confidence"],
        "properties": {
          "paper_id": { "type": "string", "minLength": 1 },
          "decision": {
            "type": "string",
            "enum": ["include", "exclude", "uncertain"]
          },
          "reason": { "type": "string", "minLength": 1 },
          "evidence": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["title", "abstract", "keywords", "year", "journal", "doi", "other"]
            }
          },
          "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1
          }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

### 9.4 运行总结 Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "RunSummary",
  "type": "object",
  "required": [
    "run_id",
    "input_files_count",
    "raw_entries_count",
    "deduped_entries_count",
    "processed_count",
    "included_count",
    "excluded_count",
    "uncertain_count",
    "unused_count",
    "batch_count",
    "api_call_count",
    "stop_reason",
    "started_at",
    "finished_at"
  ],
  "properties": {
    "run_id": { "type": "string" },
    "input_files_count": { "type": "integer", "minimum": 0 },
    "raw_entries_count": { "type": "integer", "minimum": 0 },
    "deduped_entries_count": { "type": "integer", "minimum": 0 },
    "processed_count": { "type": "integer", "minimum": 0 },
    "included_count": { "type": "integer", "minimum": 0 },
    "excluded_count": { "type": "integer", "minimum": 0 },
    "uncertain_count": { "type": "integer", "minimum": 0 },
    "unused_count": { "type": "integer", "minimum": 0 },
    "batch_count": { "type": "integer", "minimum": 0 },
    "api_call_count": { "type": "integer", "minimum": 0 },
    "stop_reason": {
      "type": "string",
      "enum": [
        "target_include_count_reached",
        "all_records_processed",
        "manual_stop",
        "runtime_error"
      ]
    },
    "started_at": { "type": "string" },
    "finished_at": { "type": "string" }
  },
  "additionalProperties": false
}
```

---

## 10. 文件输入输出约定

### 10.1 输入文件约定

输入目录建议：

```text
data/input/
```

支持：

- 单个 `.bib`
- 多个 `.bib`
- 后续可扩展目录扫描模式

### 10.2 输出目录约定

每次运行建议创建独立目录：

```text
data/output/run_20260320_140000/
```

目录内建议包含：

```text
run_20260320_140000/
  config.snapshot.yaml
  merged_records.json
  deduped_records.json
  included_report.md
  excluded_report.md
  uncertain_report.md
  included.bib
  unused_remaining.bib
  run_summary.json
  logs/
    pipeline.log
  batches/
    batch_0001_input.json
    batch_0001_output.json
    batch_0001_raw_response.txt
```

### 10.3 文件命名建议

- 统一使用时间戳 + 语义名
- 批次 ID 固定补零，便于排序

例如：

- `run_20260320_140000`
- `batch_0001_input.json`
- `batch_0001_output.json`

---

## 11. Prompt 设计与接口约定

### 11.1 Prompt 文件化

建议不要把 prompt 硬编码在 Python 代码中，而是放在：

- `prompts/screening_prompt.md`

代码只负责：

- 读取 prompt 模板
- 注入筛选标准
- 注入批次文献内容
- 注入输出 JSON 约束

### 11.2 Prompt 组成建议

Prompt 可分为四段：

1. 模型角色说明
2. 筛选标准
3. 本批文献清单
4. 输出 JSON 格式要求

### 11.3 接口层职责

`kimi_client.py` 负责：

- 拼接请求体
- 发起 HTTP 请求
- 处理认证
- 处理超时和重试

`response_parser.py` 负责：

- 提取模型文本
- 尝试解析 JSON
- 校验是否符合 Schema
- 在失败时抛出明确异常

---

## 12. 去重实现设计

### 12.1 去重流程

建议顺序：

1. 解析原始记录
2. 生成 `normalized_title`
3. 优先按 DOI 建索引
4. 对无 DOI 记录按 `normalized_title` 建索引
5. 识别重复并执行合并

### 12.2 标题标准化建议

建议步骤：

- 转小写
- 去除首尾空格
- 合并连续空格
- 去除常见标点
- 去除大括号与转义残留

例如：

`"Propulsion of {Subterranean} Robots: A Review"`

标准化为：

`"propulsion of subterranean robots a review"`

### 12.3 合并优先级

字段合并建议：

- `title`: 选更长且非空版本
- `abstract`: 选非空版本
- `doi`: 选非空版本
- `authors`: 选作者数量更多版本
- `keywords`: 去重合并
- `raw_bibtex`: 优先保留首条，同时保存全部来源信息

---

## 13. 批处理与停止逻辑设计

### 13.1 批次切分规则

- 每次仅从 `status = unprocessed` 的文献中取数据
- 按输入顺序或去重后顺序切分
- 默认每批 20 篇

### 13.2 停止逻辑

每一批完成后：

1. 累计本轮 `include` 数量
2. 若 `included_count >= target_include_count`
3. 且 `stop_when_target_reached = true`
4. 则停止后续筛选

### 13.3 超出目标的处理

允许最后一批纳入后超过目标值。原因：

- 批次作为最小处理单元更稳定
- 避免最后一批拆分造成 prompt 和流程复杂化

### 13.4 剩余文献处理

停止后，所有尚未处理的文献应：

- 标记为 `unused`
- 单独导出为 `unused_remaining.bib`
- 在总结报告中单列数量

---

## 14. 错误处理设计

### 14.1 错误分类

建议定义以下错误类型：

- `ConfigValidationError`
- `BibtexParseError`
- `DeduplicationError`
- `ModelRequestError`
- `ResponseParseError`
- `SchemaValidationError`
- `ReportExportError`

### 14.2 错误处理策略

配置错误：

- 立即终止运行

单个 BibTeX 记录解析失败：

- 记录日志
- 跳过或标记异常
- 继续处理其他记录

批次请求失败：

- 自动重试
- 达到重试上限后终止本次运行或标记批次失败

JSON 解析失败：

- 重试一次模型请求
- 保存原始响应供排查

---

## 15. 日志设计

### 15.1 日志级别

- `INFO`
- `WARNING`
- `ERROR`
- `DEBUG`

### 15.2 推荐日志内容

- 输入文件数量
- 原始条目数量
- 去重后数量
- 每批开始和结束时间
- 每批文献数量
- API 调用耗时
- 当前纳入数
- 停止原因
- 异常栈信息

### 15.3 日志文件建议

- `data/output/<run_id>/logs/pipeline.log`

---

## 16. 测试设计建议

### 16.1 单元测试

建议覆盖：

- BibTeX 解析
- 标题标准化
- DOI 去重
- 标题精确去重
- 批次切分
- 响应 JSON 解析
- Schema 校验

### 16.2 集成测试

建议覆盖：

- 从多个 `.bib` 到最终输出的完整主流程
- 达标后提前停止
- 剩余文献导出
- API mock 返回非法 JSON 的场景

### 16.3 测试数据建议

建议准备：

- 小样本 `.bib` 测试集
- 含重复 DOI 的样本
- 标题一致但 BibTeX key 不同的样本
- 摘要缺失样本
- 非法字段样本

---

## 17. 第一版实现建议

### 17.1 推荐依赖

可优先考虑以下方向：

- `bibtexparser` 或其他 BibTeX 解析库
- `pydantic` 用于配置和数据模型校验
- `PyYAML` 用于 YAML 配置读取
- `httpx` 用于 API 请求
- `jsonschema` 或 `pydantic` 用于响应校验

### 17.2 CLI 命令建议

建议提供基础命令：

```bash
python -m literature_screening.main --config ./configs/project_a.yaml
```

可扩展参数：

```bash
python -m literature_screening.main --config ./configs/project_a.yaml --dry-run
python -m literature_screening.main --config ./configs/project_a.yaml --resume
```

说明：

- `--dry-run` 仅执行到分批前或不调用 API
- `--resume` 用于未来断点续跑扩展

---

## 18. 后续实现建议

完成本技术设计后，最自然的下一步有三个：

1. 搭建 Python 项目骨架与配置加载
2. 先实现 BibTeX 解析、标准化与去重模块
3. 设计并固化 Kimi 的筛选 prompt 模板

如果按最稳妥路线推进，建议顺序是：

1. 项目骨架
2. 数据模型和配置校验
3. BibTeX 处理模块
4. 批处理模块
5. Kimi API 接入
6. 报告导出

---

## 19. 结论

本技术设计文档将项目方案进一步具体化为可编码实现的结构。核心重点是：配置外置、过程可追踪、输出结构化、状态边界清晰。按此文档推进，可以较平滑地从“概念方案”进入“可开发工程”阶段，并为后续多模型支持、人工复核和更复杂去重策略预留清晰扩展点。
