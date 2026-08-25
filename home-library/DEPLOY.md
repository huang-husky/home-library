# HomeLib 生产环境部署指南

## 概述

本指南将帮助你将 HomeLib 部署到你的域名上。使用 Docker Compose 部署，包含：
- **Backend**: FastAPI 应用 (Python)
- **Frontend**: React 应用 (Nginx 静态文件)
- **Nginx**: 反向代理 + SSL
- **Certbot**: 自动 SSL 证书管理

## 前提条件

1. **一台 VPS/云服务器**（推荐配置）
   - CPU: 1 核+
   - 内存: 1GB+
   - 存储: 10GB+
   - 系统: Ubuntu 20.04+ / Debian 10+ / CentOS 8+

2. **域名**已解析到服务器 IP
   - A 记录: `your-domain.com` → `服务器IP`
   - A 记录: `www.your-domain.com` → `服务器IP`

3. **已安装**
   - Docker
   - Docker Compose
   - Git

## 快速部署

### 1. 登录服务器并克隆代码

```bash
# SSH 登录你的服务器
ssh root@your-server-ip

# 安装 Docker 和 Docker Compose（如未安装）
curl -fsSL https://get.docker.com | sh
apt-get install -y docker-compose-plugin

# 克隆代码
cd /opt
git clone https://github.com/YOUR_USERNAME/homelib.git
cd homelib
```

### 2. 运行部署脚本

```bash
# 给脚本执行权限
chmod +x deploy.sh

# 运行部署脚本（替换为你的域名和邮箱）
./deploy.sh your-domain.com your-email@example.com
```

### 3. 手动部署（如果需要更多控制）

```bash
# 1. 创建必要目录
mkdir -p data uploads/scans nginx/ssl

# 2. 更新 Nginx 配置中的域名
sed -i "s/YOUR_DOMAIN/your-domain.com/g" nginx/nginx.conf

# 3. 构建镜像
docker-compose build

# 4. 启动服务
docker-compose up -d

# 5. 获取 SSL 证书
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your-email@example.com \
    --agree-tos \
    --no-eff-email \
    -d your-domain.com

# 6. 重启 Nginx
docker-compose restart nginx
```

## 配置说明

### 环境变量

在 `docker-compose.yml` 中可以修改以下环境变量：

```yaml
backend:
  environment:
    - DEBUG=false                    # 生产环境设为 false
    - CORS_ORIGINS=https://your-domain.com  # 允许的跨域来源
```

### Nginx 配置

`nginx/nginx.conf` 包含以下配置：
- HTTP → HTTPS 自动跳转
- SSL/TLS 安全设置
- API 反向代理到后端
- 前端静态文件服务
- 文件上传大小限制 (50MB)

### SSL 证书

使用 Let's Encrypt 免费 SSL 证书，自动续期。

## 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
docker-compose logs -f backend   # 只看后端日志
docker-compose logs -f nginx     # 只看 Nginx 日志

# 重启服务
docker-compose restart
docker-compose restart backend   # 只重启后端

# 停止服务
docker-compose down

# 更新代码后重新构建
git pull
docker-compose up -d --build

# 进入容器调试
docker-compose exec backend bash
docker-compose exec nginx sh

# 备份数据
tar -czvf homelib-backup-$(date +%Y%m%d).tar.gz data/ uploads/

# 进入数据库（SQLite）
docker-compose exec backend sqlite3 /app/data/homelib.db
```

## 更新部署

### 更新代码

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 如有数据库迁移，进入后端容器执行
# docker-compose exec backend bash
# alembic upgrade head
```

### 仅更新前端

```bash
# 重新构建前端
docker-compose up -d --build frontend
```

### 仅更新后端

```bash
# 重新构建后端
docker-compose up -d --build backend

# 重启 Nginx（如有必要）
docker-compose restart nginx
```

## 故障排查

### 服务无法启动

```bash
# 检查日志
docker-compose logs

# 检查端口占用
netstat -tlnp | grep -E '80|443|8000'

# 重启所有服务
docker-compose down
docker-compose up -d
```

### SSL 证书问题

```bash
# 手动获取证书
docker-compose run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email your-email@example.com \
    --agree-tos \
    -d your-domain.com

# 测试证书续期
docker-compose run --rm certbot renew --dry-run
```

### 数据库问题

```bash
# 检查数据库文件
ls -la data/

# 修复权限
chown -R 1000:1000 data/ uploads/

# 进入数据库命令行
docker-compose exec backend sqlite3 /app/data/homelib.db
```

## 安全配置

### 1. 防火墙设置

```bash
# UFW (Ubuntu)
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# 或者使用 iptables
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -j DROP
```

### 2. 自动备份

创建定时任务：

```bash
crontab -e

# 添加以下内容（每天凌晨 3 点备份）
0 3 * * * cd /opt/homelib && tar -czvf backups/homelib-backup-$(date +\%Y\%m\%d).tar.gz data/ uploads/ 2>/dev/null

# 保留最近 7 天的备份
0 4 * * * find /opt/homelib/backups -name "homelib-backup-*.tar.gz" -mtime +7 -delete 2>/dev/null
```

### 3. 监控（可选）

可以集成 Prometheus + Grafana 监控容器状态。

## DNS 配置（国内）

### 方式 1：直接解析（推荐，简单稳定）

```
A 记录: your-domain.com → 你的服务器 IP
A 记录: www → 你的服务器 IP
```

**优点**：简单、稳定、国内访问快  
**缺点**：暴露服务器真实 IP

### 方式 2：使用 Cloudflare（仅 DNS，不开代理）

在 Cloudflare  dashboard 中：
- 橙色云朵 → 点击变成 **灰色云朵**（仅 DNS）
- 这样 Cloudflare 只做 DNS 解析，不代理流量

**优点**：免费的 DNS 管理、SSL 证书自动续期  
**缺点**：国内访问可能偶尔抽风

### 方式 3：国内 CDN（域名需要备案）

如果你有备案域名，可以使用：
- 阿里云 CDN
- 腾讯云 CDN
- 又拍云 CDN（有免费额度）

配置方式：
```
用户 → 国内 CDN → 你的 VPS
```

**优点**：国内访问极快、减轻 VPS 带宽压力  
**缺点**：需要备案、配置稍复杂

---

## 国内 VPS 推荐

| 厂商 | 配置 | 价格 | 备注 |
|------|------|------|------|
| 阿里云轻量 | 2核2G 30Mbps | ~¥100/年 | 国内首选 |
| 腾讯云轻量 | 2核2G 30Mbps | ~¥100/年 | 国内首选 |
| 华为云 | 2核2G | ~¥150/年 | 稳定性好 |

**注意**：国内 VPS 需要域名备案才能使用 80/443 端口（或直接使用 IP + 非标准端口）

## 成本估算

| 项目 | 费用 |
|------|------|
| 域名 | ~¥60-100/年 |
| VPS (1核1GB) | ~¥200-400/年 |
| Cloudflare | 免费 |
| Let's Encrypt SSL | 免费 |
| **总计** | **~¥260-500/年** |

## 相关文件

```
home-library/
├── docker-compose.yml      # Docker Compose 配置
├── deploy.sh               # 一键部署脚本
├── backend/
│   └── Dockerfile          # 后端镜像配置
├── frontend/
│   └── Dockerfile          # 前端镜像配置
└── nginx/
    └── nginx.conf          # Nginx 配置模板
```

## 技术支持

遇到问题可以：
1. 查看日志：`docker-compose logs -f`
2. 检查服务状态：`docker-compose ps`
3. 重启服务：`docker-compose restart`

---

**部署完成后访问**: https://your-domain.com
