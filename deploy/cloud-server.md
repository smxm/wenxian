# 国内云服务器部署

## 1. 服务器初始化

登录服务器后执行：

```bash
apt update && apt upgrade -y
apt install -y git
```

如果系统没有自带 Docker Compose 插件，安装：

```bash
apt install -y docker-compose-plugin
```

## 2. 拉代码

```bash
cd /opt
git clone https://github.com/smxm/wenxian.git
cd wenxian
```

## 3. 配置 API Key

复制模板：

```bash
cp .env.deploy.example .env
```

编辑 `.env`，至少填一个：

```env
DEEPSEEK_API_KEY=你的真实DeepSeekKey
KIMI_API_KEY=
```

## 4. 启动

```bash
mkdir -p server-data/api_runs
docker compose up -d --build
```

## 5. 查看状态

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f web
```

## 6. 访问

浏览器打开：

```text
http://你的服务器公网IP
```

## 7. 腾讯云控制台要放行的端口

- 80
- 22

如果之后要上 HTTPS，再放行：

- 443

## 8. 停止与更新

停止：

```bash
docker compose down
```

更新代码后重建：

```bash
git pull
docker compose up -d --build
```

## 9. 数据位置

运行数据保存在：

```text
/opt/wenxian/server-data/api_runs
```

删容器不会丢这里的数据。
