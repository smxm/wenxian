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

## 4. 配置站点访问密码

先生成 `.htpasswd`：

```bash
openssl passwd -apr1
```

系统会让你输入密码，并输出一行类似：

```text
$apr1$xxxxxxxx$xxxxxxxxxxxxxxxxxxxxxx
```

然后写入：

```bash
cat > deploy/.htpasswd <<'EOF'
friend:把上面那串完整hash贴到这里
EOF
```

说明：

- `friend` 是登录用户名，可以自己改
- 冒号后面必须是完整 hash，不是明文密码
- 之后你和朋友访问网站时都要先输入这个用户名和密码

## 5. 启动

```bash
mkdir -p server-data/api_runs
docker compose up -d --build
```

## 6. 查看状态

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f web
```

## 7. 访问

浏览器打开：

```text
http://你的服务器公网IP
```

首次访问会先弹出浏览器用户名/密码框。

## 8. 腾讯云控制台要放行的端口

- 80
- 22

如果之后要上 HTTPS，再放行：

- 443

## 9. 停止与更新

停止：

```bash
docker compose down
```

更新代码后重建：

```bash
git pull
docker compose up -d --build
```

## 10. 数据位置

运行数据保存在：

```text
/opt/wenxian/server-data/api_runs
```

删容器不会丢这里的数据。
