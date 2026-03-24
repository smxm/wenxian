# 独立报告模块

这个目录存放已经从主项目拆分出来的报告模块。主项目继续只做初筛，报告整理在这里单独维护。

## 当前定位

- 主项目：`E:\wenxian\literature_screening\src\literature_screening`
  - 只做初筛
- 当前模块：
  - 读取初筛结果或项目数据集
  - 生成简洁的 Markdown 文献整理报告
  - 输出参考列表

## 当前生成顺序

默认报告链路现在分成两阶段：

1. 先逐篇生成文献 `summary / analysis`
2. 再把这些逐篇 notes 提交给模型，生成：
   - 相关文献总体情况
   - 类型划分
   - 各类型简介

也就是说，报告前两部分不再直接依赖旧的启发式分类文本，而是基于逐篇结果二次整理。

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

## 默认报告结构

1. 相关文献总体情况
2. 类型划分
3. 每篇文献的总结与分析
4. 参考列表

其中：

- 每篇文献标题默认使用原标题
- 正文固定分成：
  - `总结：`
  - `分析：`
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
