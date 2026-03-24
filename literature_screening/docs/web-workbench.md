# Web 工作台说明

## 1. 目标

Web 工作台不是脚本壳。它现在承担的是“项目工作台”角色：

- 创建和继续初筛任务
- 管理项目内的数据集
- 创建报告任务
- 查看任务链、进度和审计事件
- 下载产物

## 2. 技术栈

前端：

- Vue 3
- Vite
- Vue Router
- Pinia
- Naive UI

后端适配层：

- FastAPI

## 3. 为什么必须有 API 适配层

如果前端直接调用 Python 脚本或直接依赖输出目录结构，后面主项目一改，前端就会一起碎掉。

现在的设计是：

- 前端只认 `/api/...`
- API 层再去调用初筛主项目和独立报告模块

这样前后端的修改面是解耦的。

## 4. 当前页面结构

- `/`
  - 总览页
- `/screening/new`
  - 新建或继续初筛
- `/tasks`
  - 任务中心
- `/tasks/:taskId`
  - 任务详情、进度、审核、报告入口
- `/projects/:projectId`
  - 项目详情、数据集、任务链、项目级报告入口

## 5. 当前 API 结构

- `GET /api/health`
- `GET /api/meta`
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{projectId}`
- `GET /api/datasets/{datasetId}`
- `GET /api/templates`
- `POST /api/templates`
- `GET /api/tasks`
- `GET /api/tasks/{taskId}`
- `POST /api/tasks/{taskId}/retry`
- `POST /api/tasks/{taskId}/review-overrides`
- `GET /api/tasks/{taskId}/artifacts/{artifactKey}`
- `POST /api/screening/tasks`
- `POST /api/report/tasks`

## 6. 已实现的交互

### 初筛

- 草稿自动保存
- 上传文件与删除文件
- 选择项目
- 从已有 dataset 继续筛选
- 保存和应用项目模板

### 任务中心

- 全局任务轮询
- 按项目 / 类型 / 状态 / 关键词过滤

### 任务详情

- 阶段与进度可视化
- 失败后继续执行
- 人工审核修正
- 审计事件时间线
- 从初筛任务直接创建报告任务

### 项目详情

- 查看项目 datasets
- 从 `unused` 或其他 dataset 继续筛选
- 选择一个或多个 dataset 生成项目报告
- 查看任务链

## 7. 启动方式

后端：

```bash
cd E:\wenxian\literature_screening
python -m uvicorn literature_screening.api.app:app --host 127.0.0.1 --port 8000
```

前端：

```bash
cd E:\wenxian\literature_screening_web
npm install
npm run dev
```

## 8. 设计原则

- API Key 不进入前端持久化
- 前端只保存草稿和任务上下文，不保存敏感值
- 项目、任务、数据集三层结构先于页面细节
- 新功能优先扩 `studio/service.py` 和 `api/app.py`，再扩页面
