# wenxian

这是一个本地文献工作台仓库，当前包含三部分：

- `literature_screening/`
  - 初筛主项目与本地 API
- `literature_screening/separated_modules/formal_report_module/`
  - 独立报告模块
- `literature_screening_web/`
  - Vue 3 Web 工作台

## 已实现的核心能力

### 项目 / 数据集 / 任务链

- 每个任务都属于一个 `Project`
- 每次运行都会形成可追踪的 `Task`
- 初筛和审核产物会登记为 `Dataset`
- 支持从已有 `unused`、`included`、`cumulative_included` 数据集继续筛选
- 支持 `parent_task_id` 形成任务链
- 项目内自动维护 `cumulative_included` 累计纳入集

### 初筛

- 输入格式：`.bib`、`.ris`、`.enw`、PubMed `.txt`
- 多文件合并与 DOI/标题去重
- DeepSeek / Kimi 模型接入
- 达到目标纳入数后提前停止
- 输出纳入、剔除、`uncertain` 报告
- 默认导出 `RIS`，可选兼容导出 `BibTeX`

### 报告

- 报告模块与初筛主流程完全拆分
- 可基于单轮筛选结果生成报告
- 可基于项目内一个或多个 dataset 生成报告
- `GB/T 7714` 按报告顺序列出参考文献
- `APA7` 使用 `pandoc + citeproc + CSL` 渲染

### 工作流 / 平台能力

- 项目级模板 / preset
- 输入源管理：上传文件 + 复用已有数据集
- 中间态可视化：阶段、进度、进度消息
- 失败恢复 / 断点续跑：支持继续执行，初筛复用已完成 batch
- 审核与人工修正：可人工改判单篇结果并产出 reviewed RIS
- 搜索与过滤：按项目、任务类型、状态、关键词过滤
- 日志和可审计性：任务事件流 / 审计时间线
- 报告来源控制：明确选择哪些 dataset 进入报告

### 配置与隔离策略

- API Key 只通过环境变量读取，不写入任务和项目数据
- 模板按 project 作用域隔离
- 数据集、任务和产物按 project 归档

## 启动

后端 API：

```bash
cd E:\wenxian\literature_screening
python -m uvicorn literature_screening.api.app:app --host 127.0.0.1 --port 8000
```

Web 前端：

```bash
cd E:\wenxian\literature_screening_web
npm install
npm run dev
```

独立报告命令行入口：

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

## 说明文档

- [主项目说明](E:/wenxian/literature_screening/README.md)
- [架构说明](E:/wenxian/literature_screening/docs/architecture.md)
- [Web 工作台说明](E:/wenxian/literature_screening/docs/web-workbench.md)
- [独立报告模块说明](E:/wenxian/literature_screening/separated_modules/formal_report_module/README.md)
