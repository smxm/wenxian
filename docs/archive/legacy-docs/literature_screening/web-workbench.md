# Web 工作台说明

## 1. 目标

Web 工作台现在承担的是“thread-first 文献工作台”角色，而不是单纯的脚本外壳。

核心目标：

- 创建策略、初筛、报告任务
- 以主题线程方式组织项目内的轮次演进
- 管理项目数据集与全文队列
- 展示任务链、进度、审计事件和产物下载

## 2. 技术栈

前端：

- Vue 3
- Vite
- Vue Router
- Pinia
- Naive UI

后端适配层：

- FastAPI

部署方式：

- Docker 构建前端静态资源
- nginx 提供 Web 页面

## 3. 为什么需要 API 适配层

如果前端直接依赖 Python 脚本或磁盘目录结构，主项目一旦调整工作目录、运行方式或存储格式，页面就会一起碎掉。

当前设计是：

- 前端只认 `/api/...`
- 下载文件只走 `/api/tasks/{task_id}/artifacts/{artifact_key}`
- API 层再去调用主项目、store 和独立报告模块

这样前后端的变更边界比较清晰。

## 4. 当前页面结构

- `/`
  - 总览页
- `/strategy/new`
  - 新建检索策略任务
- `/screening/new`
  - 新建或继续初筛
- `/tasks`
  - 任务中心
- `/tasks/:taskId`
  - 任务详情、进度、人工复核、报告入口
- `/threads/:projectId`
  - 主题线程详情页
- `/threads/:projectId/fulltext`
  - 全文获取工作台

兼容说明：

- `/projects/:projectId`
  - 现在会重定向到 `/threads/:projectId`

## 5. 当前 API 结构

核心接口包括：

- `GET /api/health`
- `GET /api/meta`
- `GET /api/projects`
- `POST /api/projects`
- `PUT /api/projects/{projectId}`
- `DELETE /api/projects/{projectId}`
- `GET /api/projects/{projectId}`
- `GET /api/datasets/{datasetId}`
- `POST /api/projects/{projectId}/fulltext/rebuild`
- `POST /api/projects/{projectId}/fulltext/status`
- `POST /api/projects/{projectId}/fulltext/enrich`
- `GET /api/templates`
- `POST /api/templates`
- `GET /api/tasks`
- `GET /api/tasks/{taskId}`
- `POST /api/tasks/{taskId}/retry`
- `POST /api/tasks/{taskId}/cancel`
- `POST /api/tasks/{taskId}/review-overrides`
- `POST /api/tasks/{taskId}/review-overrides/bulk`
- `POST /api/tasks/{taskId}/reference-overrides`
- `GET /api/tasks/{taskId}/artifacts/{artifactKey}`
- `POST /api/strategy/tasks`
- `POST /api/screening/tasks`
- `POST /api/report/tasks`

## 6. 已实现的交互

### 策略与初筛

- 草稿自动保存
- 上传文件与删除文件
- 选择项目
- 从已有 dataset 继续筛选
- 保存和应用项目模板
- 从策略任务一键带入初筛

### 任务中心

- 全局任务轮询
- 按项目 / 类型 / 状态 / 关键词过滤

### 任务详情

- 阶段与进度可视化
- 失败后继续执行
- 人工审核修正
- 批量复核
- 审计事件时间线
- 从初筛任务直接创建报告任务
- artifact 下载

### 线程详情

- 以线程视角展示策略、筛选、报告任务
- 从 `unused` 或其他 dataset 继续筛选
- 选择一个或多个 dataset 生成项目报告
- 展示累计纳入与全文摘要

### 全文工作台

- 选择来源数据集重建全文队列
- 维护 `pending` / `ready` / `unavailable` / `deferred` 状态
- 链接补全与 OA 信息刷新
- 直接把 `fulltext_ready` 结果带回报告工作台

## 7. 路径字段约定

前端默认不依赖宿主机绝对路径来工作：

- artifact 下载通过专门下载接口完成
- 数据集和任务详情现在会同时收到绝对路径与相对路径字段

目前 API 返回：

- dataset: `path` + `relative_path`
- task detail: `run_root` + `run_root_relative`
- task detail: `output_dir` + `output_dir_relative`

这让前端可以逐步减少对绝对路径字段的假设。

## 8. 启动方式

### 推荐方式

在仓库根目录执行：

```bash
./start-wenxian.command
```

这会用 Docker 同时启动 API 和 Web。

### 手动 Docker 启动

```bash
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml down
```

### 直接前端开发

如果你要单独开发 Web：

```bash
cd literature_screening_web
npm install
npm run dev
```

类型检查：

```bash
npm run typecheck
```

## 9. 设计原则

- API key 不进入前端持久化
- 前端只保存草稿和任务上下文，不保存敏感值
- Thread / Task / Dataset 三层结构先于页面细节
- 新功能优先扩 `studio/service.py` 和 `api/app.py`，再扩页面
- 页面尽量通过 API 聚合能力获取状态，而不是自己推断磁盘结构
