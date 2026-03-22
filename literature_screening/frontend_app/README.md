# Frontend App

这是面向当前文献筛选项目的本地交互前端。

## 定位

- 不替代主项目初筛逻辑
- 不替代独立报告模块
- 只做统一交互、参数编排、运行结果展示

## 推荐启动方式

```bash
python -m streamlit run E:\wenxian\literature_screening\frontend_app\app.py
```

## 当前功能

- 从本地文件夹或上传文件导入文献
- 支持 `.bib`、`.ris`、`.enw` 和 EndNote 风格 `.txt`
- 从 Markdown 自动读取筛选标准并允许人工微调
- 调用主项目完成初筛
- 预览纳入/剔除/不确定结果
- 调用独立报告模块生成简洁报告
- 回看 UI 工作台生成的历史运行目录
- 默认导出更适合 Zotero 的 `.ris` 文献文件

## 架构原则

- 前端只和 `frontend_app/services.py` 交互
- 初筛参数变化优先改服务层
- 报告模块变化也优先改服务层
- 尽量避免 UI 代码直接依赖底层 pipeline 细节
