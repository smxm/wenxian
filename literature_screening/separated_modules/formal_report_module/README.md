# 独立报告模块

这个目录存放已经从主项目拆分出来的报告模块。主项目继续承担“策略 + 初筛 + 工作流编排 + API”职责，而报告生成逻辑在这里单独维护。

## 当前定位

主项目负责：

- 输入解析、去重、初筛
- 项目 / 任务 / 数据集 API
- 全文队列与报告任务编排

当前模块负责：

- 读取已有筛选输出
- 生成简洁 Markdown 报告
- 生成更正式的报告产物
- 输出参考文献列表

## 与主项目的关系

这个模块不是孤立仓库，而是“从主项目中解耦出来的报告子系统”：

- 共享主项目的部分基础模型和环境加载逻辑
- 通过脚本入口把 `src/` 和模块自己的 `src/` 一起挂到 Python path
- 默认从已有 `screening_output` 目录读取数据

在 Web / API 工作流里，报告任务通常由主项目编排，再调用这里的报告逻辑。

## 当前报告链路

默认简洁报告链路分成两阶段：

1. 先逐篇生成文献 `summary / analysis`
2. 再汇总这些单篇 notes，生成：
   - 相关文献总体情况
   - 类型划分
   - 报告正文与参考文献

这意味着报告前部内容主要来自“逐篇 notes 的二次整理”，而不是旧的启发式分类文本。

## 推荐入口

### 简洁报告

推荐直接使用：

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

兼容入口：

- `scripts/run_report.py`
  - 目前只是 `run_simple_report.py` 的轻量包装

### 更正式的报告

如果要生成更正式的报告链路，可以使用：

```bash
python literature_screening/separated_modules/formal_report_module/scripts/run_formal_report.py \
  --screening-output-dir /path/to/screening_output \
  --report-output-dir /path/to/report_output \
  --project-topic "你的主题" \
  --report-title-hint "你的报告标题"
```

`run_formal_report.py` 支持：

- `--provider none`
  - 只使用不依赖模型的链路
- 或指定 `kimi` / `deepseek`
  - 让部分整理步骤接入模型

## 输入要求

模块默认读取一个现成的 `screening_output` 目录。

常见来源：

- 某次真实初筛任务的输出目录
- 主项目为了报告任务临时准备的虚拟 screening 输出目录

通常需要包含：

- `deduped_records.json`
- `screening_decisions.json`

## 默认简洁报告结构

1. 相关文献总体情况
2. 类型划分
3. 每篇文献的总结与分析
4. 参考列表

其中：

- 每篇文献标题默认使用原标题
- 正文固定分成“总结”和“分析”
- `GB/T 7714` 按报告中出现顺序输出
- `APA7` 通过 `pandoc + citeproc + CSL` 渲染

## 主要输出

- `literature_report.md`
  - 默认成品
- `paper_notes.json`
  - 单篇总结与分析
- `report_overview.json`
  - 总体情况与类型划分
- `raw/`
  - 模型原始响应
- `logs/`
  - 报告阶段错误日志

更正式报告链路可能会在此基础上增加自己的中间产物，但核心输入输出边界保持一致。
