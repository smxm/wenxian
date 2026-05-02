# Literature Screening Shell Lab

这是一个完全独立的前端探索壳子。

目标不是接入接口，而是先验证一件事：

- 当前系统能不能被压缩成一套更直观、更安静、更好上手的界面

这个原型基于现有后端能力和你现在的目标重新组织界面，只保留最核心的心智：

1. 先建线程
2. 再继续初筛
3. 再处理候选文献
4. 最后生成报告

## 这套壳子的设计原则

- 一个线程就是一张总控板
- 四个阶段只保留四个主入口
- 候选工作台只回答三件事：开链接、标状态、做终判
- 报告区始终可见，不再“看不见就不知道怎么走”
- 文案尽量短，只保留操作价值

## 文件说明

- [index.html](/Users/mao/Documents/langchain/literature_screening_shell_lab/index.html)
- [styles.css](/Users/mao/Documents/langchain/literature_screening_shell_lab/styles.css)
- [app.js](/Users/mao/Documents/langchain/literature_screening_shell_lab/app.js)

## 怎么看

- 直接用浏览器打开 [index.html](/Users/mao/Documents/langchain/literature_screening_shell_lab/index.html)
- 左侧可以切换场景状态：`刚建线程 / 推进中 / 可生成报告`
- 顶部可以切换视图：`线程总览 / 候选池 / 报告台`

## 这次原型重点试的不是“功能”

而是这些问题：

- 用户能不能一眼看懂下一步做什么
- 页面能不能只保留一个主动作，而不是同时出现三四套按钮
- 统一复核能不能从“功能堆叠页”变成真正的工作流界面
- 报告区能不能提前暴露，不再等到最后才出现
