# 前端工作台

这个目录提供本地 `Streamlit` 前端，用于统一操作初筛主流程和独立报告模块。

## 目标

前端只做交互编排，不复制后端业务逻辑。

## 启动

```bash
python -m streamlit run E:\wenxian\literature_screening\frontend_app\app.py
```

## 当前功能

- 选择或上传文献文件
- 支持 `.bib`、`.ris`、`.enw`、PubMed `.txt`
- 读取和编辑筛选标准
- 运行初筛
- 查看纳入 / 剔除 / `uncertain`
- 触发独立报告模块生成简洁报告
- 管理本地 UI 运行目录

## 结构

- `app.py`
  - 页面入口
- `services.py`
  - 与初筛主项目、独立报告模块交互的服务层
- `styles.py`
  - 页面样式

## 约束

- 页面层不直接依赖底层 pipeline 细节
- 模块参数变动优先在 `services.py` 适配
- UI 层只读取结果，不重新实现初筛和报告逻辑
