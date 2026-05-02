# 腾讯云部署与更新

## 1. 当前推荐部署形态

- 服务器：腾讯云 Lighthouse / Ubuntu
- 运行方式：Docker Compose
- 站点保护：Basic Auth
- 前端：Nginx 容器
- 后端：FastAPI 容器

## 2. 关键原则

### 不要把运行数据放在项目目录里作为唯一副本

之前“更新后主题线程全没了”的根因是：

- 运行数据默认挂在 `/opt/wenxian/server-data/api_runs`
- 更新时会整体替换 `/opt/wenxian`
- 如果复制旧数据失败或漏掉，线程、任务、报告就会一起消失

现在推荐改成仓库外的持久目录：

- 运行数据：
  - `/opt/wenxian-data/api_runs`
- Basic Auth 文件：
  - `/opt/wenxian-secrets/.htpasswd`

这样即使替换 `/opt/wenxian`，已有主题和任务也不会丢。

## 3. 服务器首次准备

登录服务器后执行：

```bash
apt update && apt upgrade -y
apt install -y docker-compose-plugin
mkdir -p /opt/wenxian-data/api_runs
mkdir -p /opt/wenxian-secrets
```

## 4. 本地打包

在本地仓库根目录执行。Windows PowerShell 示例：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package-release.ps1 -Branch codex/release-clean -OutputDir . -Timestamped
```

输出示例：

- `.\wenxian-release-20260325-203000.tar.gz`

## 5. 上传到服务器

把本地打包好的 `.tar.gz` 上传到服务器，例如：

- `/opt/wenxian-release.tar.gz`

## 6. 服务器环境变量

第一次部署时，在服务器项目目录创建：

```bash
cp /opt/wenxian/.env.deploy.example /opt/wenxian/.env
```

或手动写入：

```env
DEEPSEEK_API_KEY=你的真实DeepSeekKey
KIMI_API_KEY=
APP_DATA_DIR=/opt/wenxian-data/api_runs
BASIC_AUTH_FILE=/opt/wenxian-secrets/.htpasswd
```

## 7. Basic Auth 文件

先生成密码 hash：

```bash
openssl passwd -apr1
```

然后写入：

```bash
cat > /opt/wenxian-secrets/.htpasswd <<'EOF'
friend:这里替换成完整hash
EOF
```

## 8. 首次部署或后续更新

推荐使用脚本：

```bash
chmod +x /opt/wenxian/deploy/server-update.sh
/opt/wenxian/deploy/server-update.sh /opt/wenxian-release.tar.gz
```

## 8.1 已有线上实例的一次性迁移

如果你当前线上版本已经有历史主题 / 任务，先执行一次：

```bash
chmod +x /opt/wenxian/deploy/migrate-persistent-storage.sh
/opt/wenxian/deploy/migrate-persistent-storage.sh
```

这一步会把旧目录中的：

- `/opt/wenxian/server-data/api_runs`
- `/opt/wenxian/deploy/.htpasswd`

迁移到新的仓库外持久目录，并自动把 `.env` 补成：

- `APP_DATA_DIR=/opt/wenxian-data/api_runs`
- `BASIC_AUTH_FILE=/opt/wenxian-secrets/.htpasswd`

如果是第一次部署，还没有 `/opt/wenxian`，先手动解压一次：

```bash
cd /opt
rm -rf wenxian
mkdir -p wenxian
tar -xzf wenxian-release.tar.gz -C wenxian
cd /opt/wenxian
cp .env.deploy.example .env
```

填好 `.env` 以后，再执行：

```bash
chmod +x /opt/wenxian/deploy/server-update.sh
/opt/wenxian/deploy/server-update.sh /opt/wenxian-release.tar.gz
```

## 9. 更新脚本做了什么

`server-update.sh` 会：

1. 解压新版本到临时目录
2. 保留旧的 `.env`
3. 把旧项目目录中的历史数据迁移到 `/opt/wenxian-data/api_runs`
4. 保留 `/opt/wenxian-secrets/.htpasswd`
5. 替换项目目录
6. 重新执行：

```bash
docker compose up -d --build --force-recreate
```

## 10. 端口要求

腾讯云安全组至少放行：

- `22`
- `80`

如果以后加 HTTPS，再放行：

- `443`

## 11. 检查部署状态

```bash
cd /opt/wenxian
docker compose ps
docker compose logs --tail=100 api
docker compose logs --tail=100 web
```

## 12. 访问地址

直接访问服务器公网 IP：

```text
http://你的服务器IP
```

浏览器会先弹出 Basic Auth 登录框。

## 13. 常见问题

### 问题：更新后还是旧页面

通常是以下原因之一：

1. 上传的是旧压缩包
2. 服务器解压的不是最新包
3. 浏览器缓存了旧前端

处理方式：

- 本地重新打包
- 重新上传
- 重新跑 `server-update.sh`
- 浏览器 `Ctrl + F5` 强刷，或开无痕窗口

### 问题：更新后主题线程消失

根因通常是旧流程把数据留在了 `/opt/wenxian/server-data/api_runs`，然后更新时没正确复制。

现在应统一使用：

- `/opt/wenxian-data/api_runs`

只要 `.env` 里设置了：

```env
APP_DATA_DIR=/opt/wenxian-data/api_runs
```

后续更新就不会再因为替换项目目录而丢主题。
