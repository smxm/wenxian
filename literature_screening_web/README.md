# Literature Screening Web

`literature_screening_web/` 是本地 Web 工作台。当前产品形态以线程式项目为中心，把检索策略、初筛、人工复核、全文获取和报告生成放在同一条工作流里。

## 技术栈

- Vue 3
- Vite
- Pinia
- Vue Router
- Naive UI

## 本地启动

日常推荐从仓库根目录启动完整 Docker 环境：

```bash
./start-wenxian.command
```

开发热更新：

```bash
./start-wenxian-dev.command
```

只做前端开发时，先确保后端 API 在 `http://127.0.0.1:8000` 运行，然后执行：

```bash
cd literature_screening_web
npm install
npm run dev
```

类型检查：

```bash
cd literature_screening_web
npm run typecheck
```

如果本机没有可用的 `node` / `npm`，优先使用 Docker 开发模式，或使用当前环境已配置的 Node 运行时。

## 当前主要路由

- `/threads/new` — 从研究需求创建线程
- `/threads/:projectId` — 线程详情和阶段入口
- `/threads/:projectId/plan/new` — 生成或刷新检索策略
- `/threads/:projectId/screening/new` — 新建或编辑后重提初筛任务
- `/threads/:projectId/fulltext` — 全文获取和最终报告源工作台
- `/tasks` — 任务中心
- `/tasks/:taskId` — 任务详情、进度、产物和任务级操作

兼容路由：

- `/projects/:projectId` 会重定向到 `/threads/:projectId`

## 相关文档

- `../project_state.md`
- `../docs/project_atlas/index.md`
- `../docs/project_atlas/change-routing.md`
- `../docs/project_atlas/modules/frontend-shell-and-stores.md`
- `../docs/project_atlas/modules/frontend-thread-and-task-views.md`
