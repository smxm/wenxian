# 文献初筛主项目

这个目录是主项目。职责已经收口到“初筛 + API + 工作流编排”，不再承担最终综述式成稿报告的深加工。

## 当前边界

主项目负责：

- 输入解析
- 合并与去重
- 分批调用大模型进行标题/摘要级别初筛
- 输出初筛结果和导出文件
- 提供本地 API
- 提供项目 / 数据集 / 任务链工作流

主项目不负责：

- 最终综述式报告排版优化
- 引文样式深度渲染

这些能力已经拆到：

- `E:\wenxian\literature_screening\separated_modules\formal_report_module`

## 输入格式

- `.bib`
- `.ris`
- `.enw`
- PubMed `.txt`

## 当前能力

- 多文件输入
- DOI 精确去重
- 标题标准化精确去重
- 分批筛选
- 达到目标纳入数后停止
- Kimi / DeepSeek 接入
- 默认 RIS 导出
- 可选 BibTeX 导出

## 工作流能力

- Project / Dataset / Task 模型
- 累计纳入数据集 `cumulative_included`
- 从 `unused` 数据集继续筛选
- 项目模板 / preset
- 中间态进度与阶段
- 任务事件流
- 任务继续执行 / 断点续跑
- 人工审核与 reviewed RIS

## 启动

```bash
cd E:\wenxian\literature_screening
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev,ui]
```

环境变量：

```bash
copy .env.example .env
```

然后在 `.env` 或系统环境变量中设置至少一个：

- `KIMI_API_KEY`
- `DEEPSEEK_API_KEY`

命令行运行：

```bash
python -m literature_screening.main --config .\configs\config.example.yaml
```

仅检查配置：

```bash
python -m literature_screening.main --config .\configs\config.example.yaml --dry-run
```

本地 API：

```bash
python -m uvicorn literature_screening.api.app:app --host 127.0.0.1 --port 8000
```

## 前端

- 新 Web 工作台：`E:\wenxian\literature_screening_web`
- 旧 Streamlit 兼容入口：`E:\wenxian\literature_screening\frontend_app`

启动 Web 前端：

```bash
cd E:\wenxian\literature_screening_web
npm install
npm run dev
```

## 目录

```text
literature_screening/
  configs/                 示例配置
  docs/                    技术说明
  frontend_app/            兼容版 Streamlit 前端
  prompts/                 初筛 Prompt 与输出 Schema
  separated_modules/       已拆分出去的扩展模块
  src/                     主项目源码
  tests/                   主项目测试
```

## 文档

- [架构说明](E:/wenxian/literature_screening/docs/architecture.md)
- [Web 工作台说明](E:/wenxian/literature_screening/docs/web-workbench.md)
- [独立报告模块说明](E:/wenxian/literature_screening/separated_modules/formal_report_module/README.md)
