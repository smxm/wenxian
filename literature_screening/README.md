# 文献初筛主项目

这个目录是当前仓库的主项目。职责已经收口到“初步筛选”，不再承担最终成稿报告的生成。

## 当前边界

主项目负责：

- 读取文献输入文件
- 合并与去重
- 分批调用大模型进行标题/摘要级别的初筛
- 输出纳入、剔除、`uncertain` 结果
- 导出保留文献

主项目不负责：

- 最终综述式报告的深加工
- 报告模板排版优化
- 引文格式渲染

最终报告能力已经拆到：

- `E:\wenxian\literature_screening\separated_modules\formal_report_module`

## 支持的输入格式

- `BibTeX`：`.bib`
- `RIS`：`.ris`
- `EndNote`：`.enw`
- `PubMed` 文本导出：`.txt`

## 当前能力

- 多文件输入
- DOI 精确去重
- 标题标准化精确去重
- 分批筛选
- 到达目标纳入数后停止
- `Kimi` / `DeepSeek` 接入
- 默认 `RIS` 导出
- 可选 `BibTeX` 导出

## 安装

```bash
cd E:\wenxian\literature_screening
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev,ui]
```

设置环境变量：

```bash
copy .env.example .env
```

然后在 `.env` 中填写至少一个：

- `KIMI_API_KEY`
- `DEEPSEEK_API_KEY`

## 运行

```bash
cd E:\wenxian\literature_screening
python -m literature_screening.main --config .\configs\config.example.yaml
```

仅检查配置和输出目录：

```bash
python -m literature_screening.main --config .\configs\config.example.yaml --dry-run
```

## 前端工作台

```bash
python -m streamlit run E:\wenxian\literature_screening\frontend_app\app.py
```

前端只做编排：

- 组织初筛参数
- 触发初筛主流程
- 读取初筛结果
- 调用独立报告模块

## 目录

```text
literature_screening/
  configs/                 示例配置
  docs/                    技术说明
  frontend_app/            本地 Streamlit 前端
  prompts/                 初筛 Prompt 与输出 Schema
  separated_modules/       已拆分出去的扩展模块
  src/                     主项目源码
  tests/                   主项目最小测试
```

## 说明文档

- [架构说明](docs/architecture.md)
- [前端说明](frontend_app/README.md)
- [独立报告模块说明](separated_modules/formal_report_module/README.md)
