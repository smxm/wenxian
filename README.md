# wenxian

本仓库当前保留两部分主体代码：

- `literature_screening/`
  - 初筛主项目，负责文献输入解析、去重、分批筛选、初步报告和文献导出
- `literature_screening/separated_modules/formal_report_module/`
  - 独立报告模块，基于初筛结果生成简洁的综述式 Markdown 报告

仓库已经清理掉试跑过程中产生的场景数据、调试产物和输出目录，发布分支只保留可维护的代码、最小测试、示例配置和说明文档。

## 当前功能

### 文献初筛

主项目支持：

- 输入格式：`.bib`、`.ris`、`.enw`、PubMed 导出 `.txt`
- 多文件合并
- DOI/标题标准化去重
- 按批次调用大模型初筛
- 支持 `Kimi` 和 `DeepSeek`
- 达到目标纳入数量后提前停止
- 输出纳入、剔除、`uncertain` 报告
- 默认导出 `RIS`，可选兼容导出 `BibTeX`

### 本地前端

提供一个 `Streamlit` 工作台，便于本地交互：

- 选择输入文件
- 填写筛选标准
- 运行初筛
- 查看结果
- 基于初筛结果触发独立报告模块

启动：

```bash
python -m streamlit run E:\wenxian\literature_screening\frontend_app\app.py
```

### 独立报告模块

报告模块已经与初筛主流程拆分，当前默认输出简洁报告，结构为：

- 相关文献总体情况
- 类型划分
- 每篇文献的“总结 / 分析”
- 参考列表

其中：

- `GB/T 7714` 参考列表按报告中的出现顺序输出
- `APA7` 参考列表通过 `pandoc + citeproc + CSL` 渲染

## 安装

```bash
cd E:\wenxian\literature_screening
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev,ui]
```

复制环境变量模板并填写 API Key：

```bash
copy .env.example .env
```

## 快速开始

### 运行初筛

```bash
cd E:\wenxian\literature_screening
python -m literature_screening.main --config .\configs\config.example.yaml
```

### 生成独立报告

```bash
python E:\wenxian\literature_screening\separated_modules\formal_report_module\scripts\run_report.py ^
  --screening-output-dir E:\path\to\screening_output ^
  --report-output-dir E:\path\to\report_output ^
  --project-topic "你的主题" ^
  --provider deepseek ^
  --model-name deepseek-chat ^
  --api-base-url https://api.deepseek.com/v1 ^
  --api-key-env DEEPSEEK_API_KEY
```

## 目录说明

```text
E:\wenxian
  README.md
  literature_screening/
    README.md
    pyproject.toml
    configs/
    docs/
    frontend_app/
    prompts/
    separated_modules/
    src/
    tests/
```

更具体的结构和模块边界见：

- [主项目说明](literature_screening/README.md)
- [架构说明](literature_screening/docs/architecture.md)
- [独立报告模块说明](literature_screening/separated_modules/formal_report_module/README.md)
