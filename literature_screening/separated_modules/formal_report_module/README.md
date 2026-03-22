# Detached Formal Report Module

这个目录存放已经从主初筛流程中拆分出来的独立报告模块。主项目仍然只负责初筛，报告整理在这里单独演进。

当前约定：

- 主项目 `E:\wenxian\literature_screening\src\literature_screening` 只做初筛
- 本模块默认使用“简洁整理报告”工作流
- 旧的 `run_formal_report.py` 仍保留作历史实验入口，但不是推荐用法

推荐入口：

```bash
python E:\wenxian\literature_screening\separated_modules\formal_report_module\scripts\run_report.py ^
  --screening-output-dir E:\wenxian\literature_screening\data\output\run_robot_screening_deepseek ^
  --report-output-dir E:\wenxian\literature_screening\separated_modules\formal_report_module\outputs\run_robot_simple_report_deepseek ^
  --project-topic "地下钻进机器人推进与破土机制" ^
  --provider deepseek ^
  --model-name deepseek-chat ^
  --api-base-url https://api.deepseek.com/v1 ^
  --api-key-env DEEPSEEK_API_KEY
```

默认输出：

- `literature_report.md`
  - 当前默认成品，后续优先查看这个文件
- `simple_report.md`
  - 与默认成品内容相同，保留给历史脚本兼容
- `paper_notes.json`
  - 单篇总结与分析的结构化中间结果
- `raw/`
  - 模型逐篇原始响应
- `logs/`
  - 报告阶段错误日志

当前固定的报告结构：

1. 相关文献总体情况
2. 类型划分
3. 逐篇文献总结分析

其中第三部分每篇文献统一使用原标题作为标题，并固定使用：

- `总结：`
- `分析：`

如果只是想稳定地产出这一类报告，请优先使用 `run_report.py` 或 `run_simple_report.py`，不要再使用旧的复杂正式报告链路。
