# 独立报告模块

这个目录存放已经从主项目拆分出来的报告模块。主项目继续只做初筛，报告整理在这里单独维护。

## 当前定位

- 主项目：`E:\wenxian\literature_screening\src\literature_screening`
  - 只做初筛
- 当前模块：
  - 读取初筛结果
  - 生成简洁的 Markdown 文献整理报告
  - 输出参考列表

## 推荐入口

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

## 当前默认报告结构

1. 相关文献总体情况
2. 类型划分
3. 每篇文献的总结与分析
4. 参考列表

其中：

- 每篇文献标题默认使用原标题
- 正文固定分成：
  - `总结：`
  - `分析：`
- `GB/T 7714` 参考列表按报告中出现顺序输出
- `APA7` 参考列表通过 `pandoc + citeproc + CSL` 渲染

## 主要输出

- `literature_report.md`
  - 当前默认成品
- `paper_notes.json`
  - 单篇总结和分析的结构化中间结果
- `raw/`
  - 模型原始响应
- `logs/`
  - 报告阶段错误日志

## 说明

- `run_report.py` 是当前推荐入口
- `run_simple_report.py` 保留为兼容入口
- 旧的复杂正式报告链路不再作为主推荐路径
