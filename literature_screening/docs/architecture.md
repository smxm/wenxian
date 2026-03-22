# 架构说明

## 1. 仓库分层

当前仓库按职责分成两层：

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

这两个模块已经拆分。主项目不再依赖独立报告模块才能完成初筛。

## 2. 主项目结构

```text
src/literature_screening/
  bibtex/         输入解析、标准化、去重、导出
  core/           配置、模型、常量、异常、环境变量
  pipeline/       主流程编排
  reporting/      初筛结果报告
  screening/      Prompt、批次、LLM 客户端、响应校验
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

### `reporting/`

- `report_generator.py`
  - 生成纳入/剔除/不确定报告
- `summary_builder.py`
  - 汇总运行统计
- `writers.py`
  - 写入 Markdown / JSON 文件

## 3. 前端结构

路径：

- `E:\wenxian\literature_screening\frontend_app`

前端原则：

- 页面层只处理交互
- 服务层统一调用初筛和报告模块
- 尽量不让 UI 直接依赖底层实现细节

关键文件：

- `app.py`
- `services.py`
- `styles.py`

## 4. 配置原则

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

## 5. 当前发布分支保留内容

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
