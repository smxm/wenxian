# Literature Screening Web

这个目录是新的本地 Web 工作台。

技术栈：

- Vue 3
- Vite
- Pinia
- Vue Router
- Naive UI

## 启动

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

默认通过代理访问本地 Python API：

- `http://127.0.0.1:8000`

## 当前页面

- `/` 总览页
- `/screening/new` 新建初筛任务
- `/tasks` 任务中心
- `/tasks/:taskId` 任务详情页
