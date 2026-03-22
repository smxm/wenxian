# Web 工作台说明

## 1. 目标

新工作台的目标不是替换 Python 逻辑，而是给现有两个模块提供一套现代、稳定、可扩展的交互界面。

模块边界保持为：

- 主项目：初筛
- 独立报告模块：简洁报告
- 新 Web 前端：统一交互层
- 本地 API：前后端契约层

## 2. 技术栈

前端：

- Vue 3
- Vite
- Vue Router
- Pinia
- Naive UI

后端适配层：

- FastAPI

## 3. 为什么加 API 适配层

如果前端直接调用脚本文件或依赖本地输出目录结构，后面主项目内部一改，前端就会跟着大面积重写。

现在的做法是：

- 前端只认 `/api/...`
- API 层再调用主项目和独立报告模块

这样后面可以改 Prompt、模型、文件组织方式，而不必同步重做前端。

## 4. 当前页面结构

- `/`
  - 总览页
- `/screening/new`
  - 新建初筛任务
- `/tasks`
  - 任务中心
- `/tasks/:taskId`
  - 任务详情页

## 5. 当前 API 结构

- `GET /api/health`
- `GET /api/meta`
- `GET /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/artifacts/{artifactKey}`
- `POST /api/screening/tasks`
- `POST /api/report/tasks`

## 6. 启动方式

先启动 Python API：

```bash
cd E:\wenxian\literature_screening
python -m uvicorn literature_screening.api.app:app --host 127.0.0.1 --port 8000
```

再启动前端：

```bash
cd E:\wenxian\literature_screening_web
npm install
npm run dev
```

默认前端通过 Vite 代理访问：

- `http://127.0.0.1:8000`

## 7. 后续扩展建议

后面如果继续做，不建议直接扩页面逻辑，优先扩这两层：

1. `studio/service.py`
2. `api/app.py`

前端页面只消费已经稳定的数据结构。这样扩展模型、模板、历史任务和批量导出时改动最小。
